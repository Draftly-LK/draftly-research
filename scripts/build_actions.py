"""Promote the amendment actions into `data/processed/actions.csv`.

An action is one amending instrument touching one section of a principal
enactment. They come from the inline markers a consolidated text prints beside
the provision they changed:

    s.756  Security to be by bond and with surety.
           [50, 79 of 1980] [50, 79 of 1988] [12, 14 of 1997]

read as `[amending_act_section, Act of Year]`. That is a three-step version
chain for one section, and it is the first real input to the temporal statute
model: a section number is not a stable identifier, so a 1985 judgment and a
2026 matter can cite "section 9" and mean different provisions.

HONEST LIMIT, stated here and in the file header rather than inferred away:
`operation` is `unknown` on 853 of 872 rows. A marker names the amending Act and
its section; it does not say what that section *did*. Recovering it needs the
amending Act's own marginal notes ("Amendment of section 653 of the principal
enactment"), which is a separate fetch. The 19 rows that do carry an operation
got it from wording already present in the marker.

Nothing here is verified. `status` stays `unverified` on every row.

    python scripts/build_actions.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "evaluation/runs/lawlanka-section-index/actions.csv"
OUT = ROOT / "data/processed/actions.csv"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"

COLUMNS = ["action_id", "source_id", "statute_name", "target_section",
           "amending_act", "amending_act_no", "amending_year",
           "amending_section", "operation", "verbatim", "source_url", "status"]

OPERATIONS = {"inserted", "amended", "replaced", "repealed", "unknown"}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()


def load_registry() -> dict[str, str]:
    with REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        return {norm(r["official_title"]): r["source_id"]
                for r in csv.DictReader(f) if r.get("official_title")}


def split_act(act: str) -> tuple[str, str]:
    """`79 of 1988` -> ('79', '1988'). `Law 13 of 1972.` -> ('13', '1972').

    A handful of markers drop the "of" (`20 1977`), so fall back to a bare
    number-year pair rather than leaving the row undated.
    """
    act = str(act)
    m = re.search(r"(\d+)\s+of\s+(\d{4})", act) or re.search(r"\b(\d{1,3})\s+(\d{4})\b", act)
    return (m.group(1), m.group(2)) if m else ("", "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SRC.exists():
        raise SystemExit(f"no {SRC.relative_to(ROOT)}: run the sweep first")
    with SRC.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    by_title = load_registry()
    out, unresolved = [], set()
    for i, r in enumerate(sorted(
            rows, key=lambda x: (x.get("statute_name", ""),
                                 x.get("target_section", ""),
                                 x.get("amending_act", ""))), start=1):
        sid = (r.get("source_id") or "").strip()
        if not sid:
            # The sweep wrote these before the statutes were registered.
            sid = by_title.get(norm(r.get("statute_name", "")), "")
        if not sid:
            unresolved.add(r.get("statute_name", ""))
        act_no, year = split_act(r.get("amending_act", ""))
        op = (r.get("operation") or "unknown").strip().lower()
        if op not in OPERATIONS:
            op = "unknown"
        out.append({
            "action_id": f"ACT{i:05d}",
            "source_id": sid,
            "statute_name": r.get("statute_name", ""),
            "target_section": r.get("target_section", ""),
            "amending_act": r.get("amending_act", ""),
            "amending_act_no": act_no,
            "amending_year": year,
            "amending_section": r.get("amending_section", ""),
            "operation": op,
            "verbatim": r.get("verbatim", ""),
            "source_url": r.get("source_url", ""),
            "status": "unverified",
        })

    unknown = sum(1 for r in out if r["operation"] == "unknown")
    dated = sum(1 for r in out if r["amending_year"])
    print(f"  actions            : {len(out):,}")
    print(f"  with a source_id   : {sum(1 for r in out if r['source_id']):,}")
    print(f"  with an amending year: {dated:,}")
    print(f"  operation unknown  : {unknown:,} of {len(out):,} "
          f"({unknown/len(out):.0%}) -- a marker names the Act, not what it did")
    print(f"  distinct statutes  : {len({r['source_id'] for r in out if r['source_id']})}")
    print(f"  distinct amending Acts: {len({r['amending_act'] for r in out})}")
    if unresolved:
        print(f"  statutes with no registry id ({len(unresolved)}): "
              f"{', '.join(sorted(unresolved)[:5])}")
    if args.dry_run:
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        f.write("# Amendment actions: one amending instrument touching one "
                "section of a principal enactment.\n")
        f.write(f"# operation is 'unknown' on {unknown} of {len(out)} rows -- the "
                "source marker names the amending Act and its\n")
        f.write("# section, not what that section did. Filling it needs the "
                "amending Act's own marginal notes.\n")
        f.write("# Every row is status=unverified. Generated by "
                "scripts/build_actions.py; do not edit by hand.\n")
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"  wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
