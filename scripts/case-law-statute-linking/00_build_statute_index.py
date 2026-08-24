"""Stage 0 of case-law -> statute linking: build the statute index.

Reads Lahiru's folder of statute JSONs and produces the lookup tables every
later stage matches against:

  statute_index.csv   -- one row per Act: source_id, official_title,
                         act_number, year, section_count, verification_status
  statute_sections.csv-- one row per section: source_id, section_number,
                         heading  (the flat target for section resolution)
  alias_seed.csv      -- source_id, official_title  (the backbone of the
                         alias table; you add abbreviations / historical names
                         by hand on top of this)

It also prints a coverage summary: how many Acts, how many sections, and -- if
you pass --cited-ids -- which of your most-cited source_ids are present vs
missing from the catalogue.

Nothing outside the output folder is written.

Usage:
    python scripts/case-law-statute-linking/00_build_statute_index.py \
        --statutes data/legal-sources/statutes
    # check coverage against the ids your cases actually cite:
    python 00_build_statute_index.py --statutes <folder> \
        --cited-ids SRC030 SRC071 SRC001 SRC029 SRC049 SRC059 SRC026 SRC027
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "scripts" / "case-law-statute-linking" / "output"


def load_statutes(folder: Path) -> list[dict]:
    acts = []
    for p in sorted(folder.rglob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [skip] {p.name}: {e}")
            continue
        if "source_id" not in d or "sections" not in d:
            print(f"  [skip] {p.name}: not a statute JSON (no source_id/sections)")
            continue
        acts.append(d)
    return acts


def run(statutes: str, cited_ids: list[str] | None = None) -> int:
    folder = Path(statutes)
    if not folder.exists():
        raise SystemExit(f"statute folder not found: {folder}")

    acts = load_statutes(folder)
    if not acts:
        raise SystemExit("no statute JSONs found in that folder")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- statute_index.csv ----
    index_rows = []
    for d in acts:
        index_rows.append({
            "source_id": d.get("source_id", ""),
            "official_title": d.get("official_title", ""),
            "act_number": d.get("act_number", ""),
            "year": d.get("year", ""),
            "section_count": len(d.get("sections", [])),
            "verification_status": d.get("verification_status", ""),
            "source_error_count": len(d.get("source_errors", []) or []),
        })
    index_rows.sort(key=lambda r: r["source_id"])
    _write(OUT_DIR / "statute_index.csv", index_rows,
           ["source_id", "official_title", "act_number", "year",
            "section_count", "verification_status", "source_error_count"])

    # ---- statute_sections.csv ----
    sec_rows = []
    for d in acts:
        sid = d.get("source_id", "")
        for s in d.get("sections", []):
            sec_rows.append({
                "source_id": sid,
                "section_number": str(s.get("section_number", "")).strip(),
                "heading": (s.get("heading", "") or "").strip(),
            })
    _write(OUT_DIR / "statute_sections.csv", sec_rows,
           ["source_id", "section_number", "heading"])

    # ---- alias_seed.csv (backbone of the alias table) ----
    alias_rows = [{"source_id": r["source_id"],
                   "official_title": r["official_title"],
                   "year": r["year"],
                   # blank column for you to fill: comma-separated aliases /
                   # historical names / abbreviations seen in case citations
                   "aliases": ""} for r in index_rows]
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
            print(f"\n  -> ask Lahiru for these missing Acts: {missing}")
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
    ap.add_argument("--statutes", required=True,
                    help="folder containing Lahiru's statute JSON files")
    ap.add_argument("--cited-ids", nargs="*", default=None,
                    help="optional: source_ids your cases cite most, to report "
                         "HAVE vs MISSING")
    raise SystemExit(run(**vars(ap.parse_args())))