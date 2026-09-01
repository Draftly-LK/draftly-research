"""Sample resolved links for a human precision check.

Nothing in this pipeline has been checked against real case text by a
person -- every row is status=unverified, per the repo-wide rule. This
draws a small, stratified sample of resolved_links.csv (roughly even
across the two resolver paths plus the name/number disagreement bucket)
into review-sample.csv, with a blank verdict column, following the same
one-time-review pattern the repo already uses elsewhere for lawyer
sign-off (README's review-sample.csv / lawyer_legal_precision gate).

This script does not grade anything itself -- it only selects what a
person should look at next. Sampling is seeded for reproducibility.

Usage:
    python scripts/case-law-statute-linking/build_review_sample.py
"""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE_OUT = ROOT / "scripts" / "case-law-statute-linking" / "output"
RESOLVED_LINKS = STAGE_OUT / "resolved_links.csv"
OUT = STAGE_OUT / "review-sample.csv"

NUMBER_YEAR_RE = re.compile(r"\b(?:ordinance|act)\s+no\.?\s*\d+\s+of\s+\d{4}", re.I)
SAMPLE_PER_STRATUM = 15
SEED = 20260901  # fixed so re-running draws the same sample


def stratum_for(row: dict[str, str]) -> str:
    if row["reason"].startswith("name-number-mismatch"):
        return "name-number-mismatch"
    if NUMBER_YEAR_RE.search(row["citation"]):
        return "number-plus-year-path"
    return "name-alias-path"


def build_sample(rows: list[dict[str, str]], *, seed: int = SEED) -> list[dict[str, str]]:
    by_stratum: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_stratum.setdefault(stratum_for(row), []).append(row)

    rng = random.Random(seed)
    sample: list[dict[str, str]] = []
    for stratum, stratum_rows in sorted(by_stratum.items()):
        chosen = sorted(stratum_rows, key=lambda r: (r["case_id"], r["rule_id"]))
        rng.shuffle(chosen)
        for row in chosen[:SAMPLE_PER_STRATUM]:
            sample.append({**row, "resolver_path": stratum, "lawyer_verdict": "", "notes": ""})
    return sample


def run() -> int:
    if not RESOLVED_LINKS.exists():
        raise SystemExit(f"{RESOLVED_LINKS} not found -- run 02_resolve_links.py first.")

    with RESOLVED_LINKS.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["band"] in ("verified", "review")]

    sample = build_sample(rows)

    with OUT.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "case_id",
            "rule_id",
            "citation",
            "source_id",
            "section_number",
            "band",
            "reason",
            "resolver_path",
            "lawyer_verdict",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sample)

    print(f"  sampled {len(sample)} rows across {len({r['resolver_path'] for r in sample})} strata")
    print(f"  wrote {OUT.relative_to(ROOT)}")
    print("  lawyer_verdict is blank -- status=unverified until filled in by a lawyer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
