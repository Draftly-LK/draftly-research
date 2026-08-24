"""Stage 0 of case-law -> statute linking: build the statute index.

Reads this repo's own generated corpus data -- `data/processed/documents.csv`
(kind, title) and `data/processed/section_versions.jsonl` (source_id ->
section numbers actually present) -- cross-walked against
`data/legal-sources/manifests/source-registry.csv` for official titles and
Act/Ordinance numbers. This is the same corpus the statute retrieval engine
serves, so a source_id here is guaranteed to be a real, in-scope statute.

(An earlier version of this script read a folder of standalone statute JSONs
that only had 3 Acts populated at the time, which is why `resolved_links.csv`
downstream had zero verified links. Sourcing from the generated corpus fixes
that without waiting on that folder to be filled in.)

Produces:

  statute_index.csv   -- one row per Act: source_id, official_title,
                         act_number, year, section_count, verification_status,
                         source_error_count
  statute_sections.csv-- one row per section: source_id, section_number,
                         heading  (the flat target for section resolution)
  alias_seed.csv       -- source_id, official_title, year, aliases  (the
                         backbone of the alias table; add abbreviations /
                         historical names seen in case citations by hand)

It also prints a coverage summary: how many Acts, how many sections, and -- if
you pass --cited-ids -- which of your most-cited source_ids are present vs
missing from the catalogue.

Nothing outside the output folder is written.

Usage:
    python scripts/case-law-statute-linking/00_build_statute_index.py
    # check coverage against the ids your cases actually cite:
    python 00_build_statute_index.py \
        --cited-ids SRC030 SRC071 SRC001 SRC029 SRC049 SRC059 SRC027
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "scripts" / "case-law-statute-linking" / "output"
DOCUMENTS_CSV = ROOT / "data" / "processed" / "documents.csv"
SECTION_VERSIONS_JSONL = ROOT / "data" / "processed" / "section_versions.jsonl"
SOURCE_REGISTRY_CSV = ROOT / "data" / "legal-sources" / "manifests" / "source-registry.csv"


def load_csv(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return {row["source_id"]: row for row in csv.DictReader(fh)}


def load_sections_by_source(path: Path) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = defaultdict(set)
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            sections[row["source_id"]].add(str(row["section"]).strip())
    return sections


def run(cited_ids: list[str] | None = None) -> int:
    if not DOCUMENTS_CSV.exists():
        raise SystemExit(f"documents.csv not found at {DOCUMENTS_CSV} -- run the corpus build scripts first.")
    if not SECTION_VERSIONS_JSONL.exists():
        raise SystemExit(f"section_versions.jsonl not found at {SECTION_VERSIONS_JSONL} -- run scripts/build_section_versions.py first.")

    documents = load_csv(DOCUMENTS_CSV)
    registry = load_csv(SOURCE_REGISTRY_CSV) if SOURCE_REGISTRY_CSV.exists() else {}
    sections_by_source = load_sections_by_source(SECTION_VERSIONS_JSONL)

    # scope: statute documents that actually have section data
    statute_ids = sorted(
        sid for sid, row in documents.items()
        if row.get("kind") == "statute" and sections_by_source.get(sid)
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- statute_index.csv ----
    index_rows = []
    for sid in statute_ids:
        reg = registry.get(sid, {})
        doc = documents[sid]
        index_rows.append({
            "source_id": sid,
            "official_title": reg.get("official_title") or doc.get("title", ""),
            "act_number": reg.get("act_or_ordinance_no", ""),
            "year": reg.get("year") or doc.get("year", ""),
            "section_count": len(sections_by_source[sid]),
            "verification_status": "unverified",
            "source_error_count": 0,
        })
    _write(OUT_DIR / "statute_index.csv", index_rows,
           ["source_id", "official_title", "act_number", "year",
            "section_count", "verification_status", "source_error_count"])

    # ---- statute_sections.csv ----
    sec_rows = []
    for sid in statute_ids:
        for num in sorted(sections_by_source[sid]):
            sec_rows.append({"source_id": sid, "section_number": num, "heading": ""})
    _write(OUT_DIR / "statute_sections.csv", sec_rows,
           ["source_id", "section_number", "heading"])

    # ---- alias_seed.csv (backbone of the alias table) ----
    # every statute AND amendment in the registry gets a row, even ones without
    # section data yet, so their official title is available to match against
    # once the corpus catches up. Hand-added aliases from a previous run are
    # preserved -- this file is meant to be edited in place, not clobbered.
    existing_aliases = {}
    existing_path = OUT_DIR / "alias_seed.csv"
    if existing_path.exists():
        with existing_path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                aliases = (row.get("aliases") or "").strip()
                if aliases:
                    existing_aliases[row["source_id"]] = aliases

    alias_ids = sorted(
        sid for sid, row in registry.items()
        if row.get("source_type") in ("statute", "amendment")
    ) or statute_ids
    alias_rows = [{
        "source_id": sid,
        "official_title": registry.get(sid, {}).get("official_title", ""),
        "year": registry.get(sid, {}).get("year", ""),
        "aliases": existing_aliases.get(sid, ""),
    } for sid in alias_ids]
    _write(OUT_DIR / "alias_seed.csv", alias_rows,
           ["source_id", "official_title", "year", "aliases"])

    # ---- coverage summary ----
    total_acts = len(index_rows)
    total_secs = len(sec_rows)
    print(f"\nstatutes loaded: {total_acts} Acts, {total_secs} sections")
    print(f"wrote:")
    print(f"  {OUT_DIR / 'statute_index.csv'}")
    print(f"  {OUT_DIR / 'statute_sections.csv'}")
    print(f"  {OUT_DIR / 'alias_seed.csv'}  <- fill the 'aliases' column by hand")

    have = {r["source_id"] for r in index_rows}
    if cited_ids:
        print(f"\ncoverage of your most-cited source_ids:")
        for sid in cited_ids:
            mark = "HAVE " if sid in have else "MISS "
            title = next((r["official_title"] for r in index_rows
                          if r["source_id"] == sid), "")
            print(f"  [{mark}] {sid:<10} {title}")
        missing = [s for s in cited_ids if s not in have]
        if missing:
            print(f"\n  -> these source_ids have no section data in the processed corpus yet: {missing}")
        else:
            print(f"\n  -> all your top-cited Acts are present. Good to resolve.")

    print("\ndone.")
    return 0


def _write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cited-ids", nargs="*", default=None,
                    help="optional: source_ids your cases cite most, to report "
                         "HAVE vs MISSING")
    raise SystemExit(run(**vars(ap.parse_args())))
