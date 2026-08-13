"""Generate `data/legal-sources/derived/statute-section-index.json`.

Until now that file had no generator. Nothing in the repo wrote it, which is how
it drifted from the live BM25 index -- 514 Civil Procedure Code sections here
against 103 there -- and how 938 of its 3,547 headings ended up as fragments of
a marginal note (`is made special`, `actions: in what`) rather than headings.

This composes it from ranked sources and records which source each entry came
from, so third-party structural data is identifiable and removable:

    official     official PDFs, via a coordinate-block extractor. NOT YET BUILT.
    srilankalaw  Arrangement-of-Sections blocks from the free republisher. Body
                 text on those pages is paywalled, so only the arrangement is used.
    lawlanka     the permitted structural sweep: section numbers, marginal-note
                 headings, inline `[n, Act of Year]` amendment markers.
    legacy       the hand-made index this script replaces, frozen on first run to
                 `statute-section-index.legacy.json` so the build is reproducible.

Precedence for *headings* is official > srilankalaw > lawlanka > legacy: where
two republishers carry the same provision, the freely accessible one wins, so
the corpus depends on the subscription source only where nothing else reaches.
Section existence is a union -- a section any source knows about is kept, and
`present_in` names every source that saw it, which is what makes the two
republishers a cross-check on each other rather than two guesses.

    python scripts/build_section_index.py                    # full index
    python scripts/build_section_index.py --no-subscription  # licence-risk gate
    python scripts/build_section_index.py --official-only    # reproducibility gate

`--no-subscription` drops the subscription source and keeps the open one: it
answers "what survives if the licence falls through?". `--official-only` drops
every republisher, and today yields the legacy index minus the year leak,
because the official extractor does not exist yet.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data/legal-sources/derived"
INDEX = DERIVED / "statute-section-index.json"
LEGACY = DERIVED / "statute-section-index.legacy.json"
SWEEP = ROOT / "evaluation/runs/lawlanka-section-index/sections.jsonl"
SRILANKALAW = DERIVED / "srilankalaw-sections.json"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"

# No Sri Lankan enactment in this corpus reaches 1,800 sections -- the Civil
# Procedure Code, the longest, stops at 840. A "section" in that band is an
# enactment year captured by the old extractor ("No. 22 of 1871" -> 1871).
YEAR_BAND = (1800, 2100)

# A marginal note is a multi-line block in the left column; the old extraction
# took one line of it. A heading opening lowercase or on a connective is a
# fragment, so a real heading from another source should win.
TRUNCATED = re.compile(r"^(?:[a-z]|and\b|or\b|to be\b|is\b|of\b|in\b|the\b)")


# Heading precedence. Official first; then the freely accessible republisher
# ahead of the subscription one, so where both carry the same provision the
# corpus leans on the open source.
PRECEDENCE = ("official", "srilankalaw", "lawlanka", "legacy")


def looks_truncated(heading: str) -> bool:
    heading = (heading or "").strip()
    return bool(heading) and bool(TRUNCATED.match(heading))


def section_sort_key(section: str) -> tuple[int, str]:
    m = re.match(r"(\d+)(.*)", str(section).strip())
    return (int(m.group(1)), m.group(2).upper()) if m else (10**9, str(section))


def section_number(section: str) -> int | None:
    m = re.match(r"(\d+)", str(section).strip())
    return int(m.group(1)) if m else None


def load_legacy() -> dict[str, dict[str, dict]]:
    """The hand-made index, frozen on first run so re-builds are reproducible."""
    if not LEGACY.exists():
        if not INDEX.exists():
            return {}
        LEGACY.write_text(INDEX.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  froze the existing index to {LEGACY.name} as a build input")
    raw = json.loads(LEGACY.read_text(encoding="utf-8"))
    return {sid: {str(e["section"]): {"heading": (e.get("heading") or "").strip()}
                  for e in entries}
            for sid, entries in raw.items()}


def load_lawlanka() -> dict[str, dict[str, dict]]:
    if not SWEEP.exists():
        return {}
    out: dict[str, dict[str, dict]] = {}
    for line in SWEEP.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sid = r.get("source_id") or ""
        if not sid.startswith("SRC"):
            continue  # unregistered: run register_statutes.py first
        # Markers arrive as {amending_section, amending_act, verbatim}. Keep the
        # structure -- actions.csv is built from these fields, and str() would
        # bake a Python repr into the index.
        out.setdefault(sid, {})[str(r["section"])] = {
            "heading": (r.get("heading") or "").strip(),
            "markers": list(r.get("amendment_markers") or []),
        }
    return out


def load_srilankalaw() -> dict[str, dict[str, dict]]:
    """Arrangement-of-Sections blocks from the free republisher.

    Ranked above LawLanka: both are republishers of the same Legislative
    Enactments, but this one is openly accessible, so preferring it reduces how
    much of the corpus depends on a subscription source. Only the arrangement is
    used -- the body text on those pages is paywalled at an unmarked point.

    The arrangement is usually above the paywall and therefore complete, but not
    always: the Administration of Justice Law lists 4 sections here against 55
    from the other source, because the cut lands inside the arrangement itself.
    So this is a second opinion, not a ceiling. Section existence stays a union
    and `present_in` records who saw what, which is what makes the disagreement
    reviewable instead of silently deciding it.
    """
    if not SRILANKALAW.exists():
        return {}
    raw = json.loads(SRILANKALAW.read_text(encoding="utf-8"))
    return {sid: {str(s["section"]): {"heading": (s.get("heading") or "").strip()}
                  for s in rec.get("sections", [])}
            for sid, rec in raw.items()}


def load_official() -> dict[str, dict[str, dict]]:
    """Official-PDF extraction. The coordinate-block extractor is not built, so
    this is empty by design rather than silently absent."""
    return {}


def build(*, include_lawlanka: bool = True,
          include_republishers: bool = True) -> tuple[dict, dict]:
    legacy = load_legacy()
    lawlanka = load_lawlanka() if (include_lawlanka and include_republishers) else {}
    srilankalaw = load_srilankalaw() if include_republishers else {}
    official = load_official()

    stats = {"dropped_year_leak": [], "heading_upgraded": 0,
             "sections_added": 0, "sections_kept": 0}

    index: dict[str, list[dict]] = {}
    for sid in sorted(set(legacy) | set(lawlanka) | set(srilankalaw) | set(official)):
        merged: dict[str, dict] = {}
        for name, src in (("legacy", legacy), ("lawlanka", lawlanka),
                          ("srilankalaw", srilankalaw), ("official", official)):
            for sec, data in src.get(sid, {}).items():
                e = merged.setdefault(sec, {"present_in": [], "headings": {},
                                            "markers": []})
                e["present_in"].append(name)
                if data.get("heading"):
                    e["headings"][name] = data["heading"]
                if data.get("markers"):
                    e["markers"] = data["markers"]

        entries = []
        for sec in sorted(merged, key=section_sort_key):
            e = merged[sec]
            num = section_number(sec)
            # A year masquerading as a section, with no other source seeing it.
            if (num is not None and YEAR_BAND[0] <= num <= YEAR_BAND[1]
                    and e["present_in"] == ["legacy"]):
                stats["dropped_year_leak"].append(f"{sid}:s{sec}")
                continue
            # Strict precedence: the first source that has a heading wins, and a
            # lower-ranked source never overrides it. Legacy headings are
            # single lines cut out of a multi-line marginal note, so a legacy
            # heading is not evidence about anything when a better source has
            # already spoken -- even when it happens to read more cleanly.
            heading, heading_source = "", ""
            for name in PRECEDENCE:
                h = e["headings"].get(name)
                if h:
                    heading, heading_source = h, name
                    break
            if heading_source and heading_source != "legacy" and \
                    looks_truncated(e["headings"].get("legacy", "")):
                stats["heading_upgraded"] += 1
            if "legacy" in e["present_in"]:
                stats["sections_kept"] += 1
            else:
                stats["sections_added"] += 1
            entry = {"section": sec, "heading": heading,
                     "heading_source": heading_source or "none",
                     "present_in": e["present_in"]}
            if e["markers"]:
                entry["amendment_markers"] = e["markers"]
            entries.append(entry)
        if entries:
            index[sid] = entries
    return index, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--official-only", action="store_true",
                    help="build without any republisher data at all; the "
                         "reproducibility gate")
    ap.add_argument("--no-subscription", action="store_true",
                    help="build without the subscription source, keeping the "
                         "freely accessible one; the licence-risk gate")
    ap.add_argument("--out", default="",
                    help="write somewhere other than the canonical index")
    args = ap.parse_args()

    index, stats = build(include_lawlanka=not (args.official_only or args.no_subscription),
                         include_republishers=not args.official_only)
    total = sum(len(v) for v in index.values())
    out = Path(args.out) if args.out else INDEX
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")

    mode = ("official-only" if args.official_only else
            "no-subscription" if args.no_subscription else "full")
    print(f"  mode              : {mode}")
    print(f"  statutes          : {len(index)}")
    print(f"  sections          : {total:,}")
    print(f"    carried over    : {stats['sections_kept']:,}")
    print(f"    newly indexed   : {stats['sections_added']:,}")
    print(f"  headings upgraded : {stats['heading_upgraded']:,} "
          f"(a fragment replaced by a full marginal note)")
    dropped = stats["dropped_year_leak"]
    print(f"  year-leak dropped : {len(dropped)}"
          + (f"  {', '.join(dropped[:6])}" + (" ..." if len(dropped) > 6 else "")
             if dropped else ""))
    src_count: dict[str, int] = {}
    for entries in index.values():
        for e in entries:
            src_count[e["heading_source"]] = src_count.get(e["heading_source"], 0) + 1
    print(f"  heading sources   : {dict(sorted(src_count.items()))}")
    print(f"  wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
