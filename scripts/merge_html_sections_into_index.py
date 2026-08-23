"""Fold the LankaLaw HTML parse into `statute-section-index.json`.

`parse_lankalaw_html.py` reads the born-digital HTML editions and writes
`data/processed/lankalaw-html-sections.json`. Nothing consumed that file, so
RUBRIK.md reported statutes as "sections not extracted" while a clean parse of
them sat on disk. This is the missing join.

The merge follows the same rules as `build_section_index.py`, so the index keeps
one meaning throughout:

    section existence is a union   a section any source saw is kept, and
                                   `present_in` names every source that saw it
    headings run by precedence     official > srilankalaw > lankalaw-html
                                   > lawlanka > legacy

`lankalaw-html` sits above `lawlanka` and below `srilankalaw`. It is the same
publisher as `lawlanka` but a better structural source -- semantic markup rather
than a sweep over a two-column PDF -- so it wins between those two. It stays
below the freely accessible republisher for the same licence reason
`build_section_index.py` gives: where both carry a provision, prefer the open
source.

Re-running is idempotent, and nothing here is verified: LankaLaw is a private
republisher, not the Government Printer.

    uv run python scripts/merge_html_sections_into_index.py --source-id SRC070
    uv run python scripts/merge_html_sections_into_index.py --all --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "data/legal-sources/manifests/statute-section-index.json"
HTML_SECTIONS = REPO_ROOT / "data/processed/lankalaw-html-sections.json"

SOURCE = "lankalaw-html"
# Heading precedence, best first. Mirrors build_section_index.py.
PRECEDENCE = ("official", "srilankalaw", SOURCE, "lawlanka", "legacy")
# Canonical order for `present_in`. Keeps the relative order the existing index
# already uses, so entries this run does not touch stay byte-identical.
SOURCE_ORDER = ("legacy", "lawlanka", SOURCE, "srilankalaw", "official")


def section_sort_key(section: str) -> tuple[int, str]:
    match = re.match(r"(\d+)(.*)", str(section).strip())
    return (int(match.group(1)), match.group(2).upper()) if match else (10**9, str(section))


def marker_key(marker: dict) -> tuple[str, str]:
    return (marker.get("amending_section", ""), marker.get("amending_act", ""))


def merge_statute(existing: list[dict], parsed: list[dict]) -> tuple[list[dict], dict[str, int]]:
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
                "heading_source": SOURCE if heading else "none",
                "present_in": [SOURCE],
            }
            if markers:
                entry["amendment_markers"] = markers
                stats["markers_added"] += len(markers)
            by_section[number] = entry
            stats["added"] += 1
            continue

        stats["seen_again"] += 1
        if SOURCE not in entry["present_in"]:
            entry["present_in"] = sorted(
                {*entry["present_in"], SOURCE},
                key=lambda name: SOURCE_ORDER.index(name) if name in SOURCE_ORDER else len(SOURCE_ORDER),
            )
        # Precedence, not recency: a better-ranked source that already spoke keeps
        # the heading even where this one reads more cleanly.
        current = entry.get("heading_source", "none")
        current_rank = PRECEDENCE.index(current) if current in PRECEDENCE else len(PRECEDENCE)
        if heading and PRECEDENCE.index(SOURCE) < current_rank:
            entry["heading"] = heading
            entry["heading_source"] = SOURCE
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
                        help="merge every statute the HTML parse covers")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change and write nothing")
    args = parser.parse_args()

    if not args.source_id and not args.all:
        parser.error("pass --source-id SRCnnn (repeatable) or --all")

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    parsed = json.loads(HTML_SECTIONS.read_text(encoding="utf-8"))

    targets = sorted(parsed) if args.all else sorted(set(args.source_id))
    missing = [s for s in targets if s not in parsed]
    if missing:
        parser.error(f"no HTML parse for {', '.join(missing)}; run parse_lankalaw_html.py first")

    totals = {"added": 0, "seen_again": 0, "heading_upgraded": 0, "markers_added": 0}
    for source_id in targets:
        before = len(index.get(source_id, []))
        entries, stats = merge_statute(index.get(source_id, []), parsed[source_id])
        index[source_id] = entries
        for key in totals:
            totals[key] += stats[key]
        note = "new to the index" if not before else f"{before} already held"
        print(f"  {source_id}: {before} -> {len(entries)} sections ({note}), "
              f"+{stats['added']} added, {stats['heading_upgraded']} headings upgraded, "
              f"+{stats['markers_added']} markers")

    body = json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    if args.dry_run:
        print("\nDry run. Nothing written.")
        return 0
    INDEX.write_text(body, encoding="utf-8")

    print(f"\n{len(targets)} statutes merged from {SOURCE}")
    print(f"  sections added     : {totals['added']}")
    print(f"  sections confirmed : {totals['seen_again']} (already known from another source)")
    print(f"  headings upgraded  : {totals['heading_upgraded']}")
    print(f"  markers added      : {totals['markers_added']}")
    print(f"wrote {INDEX.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
