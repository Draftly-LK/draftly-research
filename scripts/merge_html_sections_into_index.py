"""Fold parsed statute structures into `statute-section-index.json`.

Two sources feed this, and a statute is taken from the better one:

    finalized      a tree in `data/legal-sources/library/finalized` that someone
                   has reviewed and accepted. Headings there have been corrected
                   against the printed page, marginal-note bleed removed, and
                   damaged section numbers repaired.
    lankalaw-html  `parse_lankalaw_html.py`'s raw read of the same HTML, in
                   `data/processed/lankalaw-html-sections.json`.

Nothing consumed either file, so RUBRIK.md reported statutes as "sections not
extracted" while a clean parse of them sat on disk. This is the missing join.

The merge follows the same rules as `build_section_index.py`, so the index keeps
one meaning throughout:

    section existence is a union   a section any source saw is kept, and
                                   `present_in` names every source that saw it
    headings run by precedence     official > finalized > srilankalaw
                                   > lankalaw-html > lawlanka > legacy

`finalized` outranks the republishers because a person has read it against the
source; that is the only thing in this corpus with a human behind it.
`lankalaw-html` sits above `lawlanka` and below `srilankalaw`. It is the same
publisher as `lawlanka` but a better structural source -- semantic markup rather
than a sweep over a two-column PDF -- so it wins between those two. It stays
below the freely accessible republisher for the same licence reason
`build_section_index.py` gives: where both carry a provision, prefer the open
source.

A finalized tree nests sections under Parts and crossheadings, so sections are
collected recursively rather than off the top level; the Companies Act would
otherwise contribute one section instead of 534.

Re-running is idempotent. Nothing here is verified in the legal sense: even a
finalized tree is `status=unverified` until a lawyer signs it off.

    uv run python scripts/merge_html_sections_into_index.py --source-id SRC070
    uv run python scripts/merge_html_sections_into_index.py --all --dry-run
    uv run python scripts/merge_html_sections_into_index.py --finalized
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "data/legal-sources/manifests/statute-section-index.json"
HTML_SECTIONS = REPO_ROOT / "data/processed/lankalaw-html-sections.json"
FINALIZED_DIR = REPO_ROOT / "data/legal-sources/library/finalized"

SOURCE = "lankalaw-html"
FINALIZED = "finalized"
# Heading precedence, best first. Mirrors build_section_index.py.
PRECEDENCE = ("official", FINALIZED, "srilankalaw", SOURCE, "lawlanka", "legacy")
# Canonical order for `present_in`. Keeps the relative order the existing index
# already uses, so entries this run does not touch stay byte-identical.
SOURCE_ORDER = ("legacy", "lawlanka", SOURCE, "srilankalaw", FINALIZED, "official")


def section_sort_key(section: str) -> tuple[int, str]:
    match = re.match(r"(\d+)(.*)", str(section).strip())
    return (int(match.group(1)), match.group(2).upper()) if match else (10**9, str(section))


def marker_key(marker: dict) -> tuple[str, str]:
    return (marker.get("amending_section", ""), marker.get("amending_act", ""))


def finalized_sections() -> dict[str, list[dict]]:
    """Sections from every accepted tree, shaped like the HTML parse.

    Sections nest under Parts and crossheadings, so the walk is recursive.
    Amendment events carry more than the flat marker does; only the fields the
    index already uses are kept, so the two sources stay the same shape.
    """
    out: dict[str, list[dict]] = {}
    if not FINALIZED_DIR.exists():
        return out
    for file in sorted(FINALIZED_DIR.rglob("*.json")):
        document = json.loads(file.read_text(encoding="utf-8"))
        # Amending instruments live in the same tree but are not statutes.
        if "source_id" not in document or "body" not in document:
            continue
        collected: list[dict] = []

        def walk(nodes: list[dict]) -> None:
            for node in nodes:
                if node.get("type") == "section" and node.get("number"):
                    collected.append(
                        {
                            "section": str(node["number"]),
                            "heading": (node.get("heading") or "").strip().rstrip("."),
                            "amendment_markers": [
                                {
                                    "amending_section": str(event.get("amending_section", "")),
                                    "amending_act": event.get("amending_act", ""),
                                    "verbatim": event.get("verbatim", ""),
                                }
                                for event in node.get("amendment_events") or []
                            ],
                        }
                    )
                walk(node.get("children", []))

        walk(document["body"])
        if collected:
            out[document["source_id"]] = collected
    return out


def merge_statute(
    existing: list[dict], parsed: list[dict], source: str = SOURCE
) -> tuple[list[dict], dict[str, int]]:
    """Union the parsed sections into one statute's entries."""
    stats = {"added": 0, "seen_again": 0, "heading_upgraded": 0, "markers_added": 0}
    by_section = {str(entry["section"]): entry for entry in existing}

    for section in parsed:
        number = str(section["section"])
        heading = (section.get("heading") or "").strip()
        markers = list(section.get("amendment_markers") or [])
        entry = by_section.get(number)

        if entry is None:
            entry = {
                "section": number,
                "heading": heading,
                "heading_source": source if heading else "none",
                "present_in": [source],
            }
            if markers:
                entry["amendment_markers"] = markers
                stats["markers_added"] += len(markers)
            by_section[number] = entry
            stats["added"] += 1
            continue

        stats["seen_again"] += 1
        if source not in entry["present_in"]:
            entry["present_in"] = sorted(
                {*entry["present_in"], source},
                key=lambda name: SOURCE_ORDER.index(name) if name in SOURCE_ORDER else len(SOURCE_ORDER),
            )
        # Precedence, not recency: a better-ranked source that already spoke keeps
        # the heading even where this one reads more cleanly.
        current = entry.get("heading_source", "none")
        current_rank = PRECEDENCE.index(current) if current in PRECEDENCE else len(PRECEDENCE)
        if heading and PRECEDENCE.index(source) < current_rank:
            entry["heading"] = heading
            entry["heading_source"] = source
            stats["heading_upgraded"] += 1

        if markers:
            held = entry.get("amendment_markers") or []
            seen = {marker_key(m) for m in held}
            fresh = [m for m in markers if marker_key(m) not in seen]
            if fresh:
                entry["amendment_markers"] = held + fresh
                stats["markers_added"] += len(fresh)

    ordered = sorted(by_section.values(), key=lambda e: section_sort_key(e["section"]))
    return ordered, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", action="append", default=[],
                        help="merge only this statute; repeatable")
    parser.add_argument("--all", action="store_true",
                        help="merge every statute either source covers")
    parser.add_argument("--finalized", action="store_true",
                        help="merge only the statutes that have an accepted tree")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change and write nothing")
    args = parser.parse_args()

    if not args.source_id and not args.all and not args.finalized:
        parser.error("pass --source-id SRCnnn (repeatable), --finalized, or --all")

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    html_parsed = json.loads(HTML_SECTIONS.read_text(encoding="utf-8"))
    accepted = finalized_sections()

    if args.finalized:
        targets = sorted(accepted)
    elif args.all:
        targets = sorted(set(html_parsed) | set(accepted))
    else:
        targets = sorted(set(args.source_id))
    missing = [s for s in targets if s not in html_parsed and s not in accepted]
    if missing:
        parser.error(
            f"no parse for {', '.join(missing)}; run parse_lankalaw_html.py, or accept a tree "
            "into data/legal-sources/library/finalized"
        )

    totals = {"added": 0, "seen_again": 0, "heading_upgraded": 0, "markers_added": 0}
    used = collections.Counter()
    for source_id in targets:
        # An accepted tree has been read against the page; prefer it.
        source = FINALIZED if source_id in accepted else SOURCE
        sections = accepted.get(source_id) or html_parsed[source_id]
        used[source] += 1
        before = len(index.get(source_id, []))
        entries, stats = merge_statute(index.get(source_id, []), sections, source)
        index[source_id] = entries
        for key in totals:
            totals[key] += stats[key]
        note = "new to the index" if not before else f"{before} already held"
        print(f"  {source_id}: {before} -> {len(entries)} sections ({note}) from {source}, "
              f"+{stats['added']} added, {stats['heading_upgraded']} headings upgraded, "
              f"+{stats['markers_added']} markers")

    body = json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    if args.dry_run:
        print("\nDry run. Nothing written.")
        return 0
    INDEX.write_text(body, encoding="utf-8")

    print(f"\n{len(targets)} statutes merged "
          f"({used[FINALIZED]} from {FINALIZED}, {used[SOURCE]} from {SOURCE})")
    print(f"  sections added     : {totals['added']}")
    print(f"  sections confirmed : {totals['seen_again']} (already known from another source)")
    print(f"  headings upgraded  : {totals['heading_upgraded']}")
    print(f"  markers added      : {totals['markers_added']}")
    print(f"wrote {INDEX.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
