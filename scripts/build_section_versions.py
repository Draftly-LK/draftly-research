"""Build section versions and check every case-to-section link against the date.

A section number is not a stable identifier. Civil Procedure Code s.5 has been
amended in 2017, 2023 and 2024; Prevention of Frauds s.2 in 1947, 2022 and 2024.
So a 1985 judgment and a 2026 matter can both cite "section 5" and mean
materially different provisions, and quoting today's consolidated text as the
provision a 1985 court applied is simply wrong.

This turns `actions.csv` into version intervals, then grades every link:

    applicable                 no amendment falls between the judgment and now
    superseded-since-judgment  the section changed after the court spoke, so the
                               current text is NOT what was applied
    history-unknown            we hold no amendment history for this statute --
                               unknown, which is not the same as unchanged

What this can and cannot do, stated plainly:

  * A first version carries a real commencement date where we have one (62
    statutes, from `statute_commencement.csv`). Every later boundary is still
    keyed to the amending Act's YEAR, because that is all the markers give.
    An Act of 1980 may commence in 1981, so a boundary case still cannot be
    settled from an amendment year alone.
  * We hold the TEXT of the current version only. Earlier versions are known to
    exist and are dated, but their wording is not in the corpus, so
    `text_available` is false for every superseded version. Recovering it needs
    the 1956 and 1981 revised editions, or the amending Acts themselves.
  * `operation` is unknown on 853 of 872 actions, so a version boundary means
    "something changed here", not "the section was replaced".

Nothing here is verified. Every row is status=unverified.

    python scripts/build_section_versions.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ROOT / "data/processed/actions.csv"
# The live index. `data/legal-sources/derived/` is where build_section_index.py
# still writes, but nothing has been there for some time and every consumer,
# apps/statute-browser included, reads the manifests copy.
INDEX = ROOT / "data/legal-sources/manifests/statute-section-index.json"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
LINKS = ROOT / "evaluation/runs/headnote-recovery-v1/structured/statute_links_v2.csv"
COMMENCEMENT = ROOT / "data/processed/statute_commencement.csv"

OUT_VERSIONS = ROOT / "data/processed/section_versions.jsonl"
OUT_REPORT = ROOT / "data/processed/temporal-alignment-report.md"

APPLICABLE = "applicable"
SUPERSEDED = "superseded-since-judgment"
UNKNOWN = "history-unknown"


def read_actions() -> dict[tuple[str, str], list[dict]]:
    """(source_id, section) -> the dated amendments that touched it."""
    by_section: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    with ACTIONS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(l for l in f if not l.startswith("#")):
            year = row.get("amending_year", "")
            if not year.strip().isdigit():
                continue
            by_section[(row["source_id"], str(row["target_section"]))].append({
                "year": int(year),
                "action_id": row["action_id"],
                "amending_act": row["amending_act"],
                "amending_section": row["amending_section"],
                "operation": row.get("operation") or "unknown",
            })
    for v in by_section.values():
        v.sort(key=lambda a: (a["year"], a["action_id"]))
    return by_section


def statutes_with_history(actions: dict) -> set[str]:
    """Statutes for which we hold ANY amendment history. Absence of a marker in
    one of these means the section is unamended; absence everywhere else means
    we simply do not know."""
    return {sid for sid, _ in actions}


def enactment_years() -> dict[str, int]:
    out: dict[str, int] = {}
    with REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            y = (row.get("year") or "").strip()
            m = re.match(r"(\d{4})", y)
            if m:
                out[row["source_id"]] = int(m.group(1))
    return out


def commencement_dates() -> dict[str, str]:
    """source_id -> ISO commencement date, where we have one.

    The registry only carries a year of enactment, which is not the same thing:
    an Act of 1980 may commence in 1981. Where a real commencement date exists
    it becomes the start of the first version, so a judgment sitting between
    enactment and commencement is not silently placed under the wrong version.
    """
    if not COMMENCEMENT.exists():
        return {}
    with COMMENCEMENT.open(encoding="utf-8", newline="") as f:
        rows = csv.DictReader(l for l in f if not l.startswith("#"))
        return {r["source_id"]: r["commencement"]
                for r in rows if r.get("commencement")}


def build_versions(actions: dict, index: dict, years: dict,
                   commencement: dict[str, str]) -> list[dict]:
    known = statutes_with_history(actions)
    versions: list[dict] = []
    for sid in sorted(index):
        for entry in index[sid]:
            sec = str(entry["section"])
            amendments = actions.get((sid, sec), [])
            boundaries = sorted({a["year"] for a in amendments})
            starts = [years.get(sid)] + boundaries
            ends = boundaries + [None]
            for i, (frm, to) in enumerate(zip(starts, ends), start=1):
                created_by = ([] if i == 1 else
                              [a["action_id"] for a in amendments if a["year"] == frm])
                versions.append({
                    "version_id": f"{sid}:s{sec}:v{i}",
                    "valid_from_date": (commencement.get(sid, "") if i == 1 else ""),
                    "source_id": sid,
                    "section": sec,
                    "version_no": i,
                    "valid_from_year": frm,
                    "valid_to_year": to,
                    "is_current": to is None,
                    # We hold the consolidated text, which is the current version.
                    "text_available": to is None,
                    "created_by_actions": created_by,
                    "amendment_history": ("known" if sid in known else "unknown"),
                    "status": "unverified",
                })
    return versions


def grade_link(case_year: int | None, sid: str, sec: str,
               actions: dict, known: set[str]) -> tuple[str, list[int]]:
    amendments = actions.get((sid, sec), [])
    later = sorted({a["year"] for a in amendments if case_year and a["year"] > case_year})
    if later:
        return SUPERSEDED, later
    if sid not in known:
        return UNKNOWN, []
    return APPLICABLE, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for p in (ACTIONS, INDEX):
        if not p.exists():
            raise SystemExit(f"missing {p.relative_to(ROOT)}")

    actions = read_actions()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    years = enactment_years()
    known = statutes_with_history(actions)

    commencement = commencement_dates()
    versions = build_versions(actions, index, years, commencement)
    multi = [v for v in versions if v["version_no"] > 1]
    sections_versioned = len({(v["source_id"], v["section"]) for v in multi})

    print(f"  sections in the index        : {sum(len(v) for v in index.values()):,}")
    print(f"  version records              : {len(versions):,}")
    print(f"  sections with >1 version     : {sections_versioned:,}")
    print(f"  statutes with any history    : {len(known)} of {len(index)}")
    print(f"  versions whose text we hold  : {sum(1 for v in versions if v['text_available']):,}"
          f" of {len(versions):,} (the current one only)")
    print(f"  first versions with a real commencement date : "
          f"{sum(1 for v in versions if v.get('valid_from_date')):,}"
          f"  ({len(commencement)} statutes dated)")

    # --- link alignment -------------------------------------------------------
    rows, tally = [], collections.Counter()
    if LINKS.exists():
        with LINKS.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("grade") != "in-index":
                    continue
                y = r.get("year", "")
                case_year = int(float(y)) if y and y.replace(".", "").isdigit() else None
                g, later = grade_link(case_year, r["source_id"], str(r["section"]),
                                      actions, known)
                tally[g] += 1
                rows.append({**r, "temporal_status": g,
                             "amended_after_judgment": ";".join(map(str, later))})
        total = sum(tally.values())
        print(f"\n  in-index links checked       : {total:,}")
        for k in (APPLICABLE, SUPERSEDED, UNKNOWN):
            print(f"    {k:<26} {tally[k]:5,d}  ({tally[k]/total:.1%})")

    if args.dry_run:
        return 0

    OUT_VERSIONS.write_text(
        "\n".join(json.dumps(v, ensure_ascii=False) for v in versions) + "\n",
        encoding="utf-8")
    print(f"\n  wrote {OUT_VERSIONS.relative_to(ROOT)}")

    # --- report ---------------------------------------------------------------
    worst = collections.Counter()
    detail: dict[tuple[str, str], list[int]] = {}
    for r in rows:
        if r["temporal_status"] == SUPERSEDED:
            k = (r["source_id"], str(r["section"]))
            worst[k] += 1
            detail[k] = sorted({int(x) for x in r["amended_after_judgment"].split(";") if x})
    titles = {}
    with REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["source_id"]] = row["official_title"]

    # The marker list only reaches back so far. A judgment older than the
    # earliest amendment we hold cannot be graded `applicable` with confidence,
    # because an amendment between it and that date would be invisible to us.
    earliest = min((a["year"] for v in actions.values() for a in v), default=None)
    pre = sum(1 for r in rows
              if r["temporal_status"] == APPLICABLE
              and (r.get("year") or "").replace(".", "").isdigit()
              and earliest and int(float(r["year"])) < earliest)

    total = sum(tally.values()) or 1
    lines = [
        "# Temporal alignment of case-to-section links",
        "",
        "Generated by `scripts/build_section_versions.py`. Every row is",
        "`status=unverified`.",
        "",
        "A section number is not a stable identifier. This checks each link that",
        "resolves to a real section against the amendment history of that section,",
        "using the judgment year.",
        "",
        "| Status | Links | Share | Meaning |",
        "| --- | ---: | ---: | --- |",
        f"| `{APPLICABLE}` | {tally[APPLICABLE]:,} | {tally[APPLICABLE]/total:.1%} "
        "| no recorded amendment falls between the judgment and now |",
        f"| `{SUPERSEDED}` | {tally[SUPERSEDED]:,} | {tally[SUPERSEDED]/total:.1%} "
        "| the section changed after the court spoke, so the current text is not what was applied |",
        f"| `{UNKNOWN}` | {tally[UNKNOWN]:,} | {tally[UNKNOWN]/total:.1%} "
        "| no amendment history held for this statute; unknown, not unchanged |",
        "",
        "## Sections most affected",
        "",
        "| Statute | Section | Links | Amended after the judgment |",
        "| --- | --- | ---: | --- |",
    ]
    for (sid, sec), n in worst.most_common(15):
        lines.append(f"| {titles.get(sid, sid)} | s.{sec} | {n} | "
                     f"{', '.join(map(str, detail[(sid, sec)]))} |")
    lines += [
        "",
        "## Limits",
        "",
        "- Intervals are keyed to the amending Act's year, not its commencement",
        "  date, so a boundary case cannot be settled from this alone.",
        "- Only the current version's text is held. Superseded versions are dated",
        "  but their wording is not in the corpus.",
        "- `operation` is unknown on 853 of 872 actions, so a boundary means",
        "  something changed, not what changed.",
        f"- **`{APPLICABLE}` is not proof.** The earliest amendment recorded "
        f"anywhere is {earliest}, but the case corpus starts in 1886, and the "
        "pre-1933",
        "  instruments for the Civil Procedure Code sit in a document header the",
        f"  source page does not render. {pre:,} links graded `{APPLICABLE}` come "
        "from judgments",
        f"  older than {earliest}, where an intervening amendment would be "
        "invisible to us.",
        f"- `{UNKNOWN}` is a coverage gap, not a clean bill of health.",
        "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {OUT_REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
