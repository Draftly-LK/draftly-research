"""Run the case-law -> statute linking pipeline end to end, in order.

Before this script, running the pipeline meant remembering to invoke
00_build_statute_index.py, then 02_resolve_links.py, in the right order,
and reading two or three sets of printed output by hand to see whether
anything improved. This wires them into one command with one summary.

Deliberately does NOT re-run case-law-information-extraction's LLM rule
extraction (rules.csv) -- that costs NVIDIA credits and is a separate,
manually-invoked pipeline per the top-level project commands. This only
checks that its output already exists.

Usage:
    python scripts/case-law-statute-linking/run_pipeline.py
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE_DIR = ROOT / "scripts" / "case-law-statute-linking"
STAGE_OUT = STAGE_DIR / "output"
RULES_CSV = ROOT / "scripts" / "case-law-information-extraction" / "output" / "rules.csv"
RESOLVED_LINKS = STAGE_OUT / "resolved_links.csv"
PROPOSED_ALIASES = STAGE_OUT / "proposed_aliases.csv"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, STAGE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not RULES_CSV.exists():
        raise SystemExit(
            f"{RULES_CSV.relative_to(ROOT)} not found.\n"
            "This pipeline resolves citations already extracted by "
            "case-law-information-extraction; it does not run that "
            "extraction itself (it costs NVIDIA credits). Run it first, e.g.:\n"
            "  python scripts/case-law-information-extraction/extract_case_rules.py "
            "--track A --source commonlii\n"
            "See scripts/case-law-information-extraction/README.md."
        )

    print("=== stage 0: build statute index ===")
    stage0 = _load_module("lsl_stage0", "00_build_statute_index.py")
    stage0.run()

    print("\n=== alias proposals (report only; never applied automatically) ===")
    proposer = _load_module("lsl_propose_aliases", "propose_aliases.py")
    proposer.run()

    print("\n=== stage 2: resolve links ===")
    stage2 = _load_module("lsl_stage2", "02_resolve_links.py")
    stage2.run()

    print("\n=== pipeline summary ===")
    with RESOLVED_LINKS.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    bands = Counter(row["band"] for row in rows)
    reasons = Counter(row["reason"] for row in rows if row["band"] != "verified")

    for band in ("verified", "review", "unresolved"):
        print(f"  {band:<12} {bands.get(band, 0):>5}")

    if reasons:
        print("\n  top non-verified reasons:")
        for reason, count in reasons.most_common(8):
            print(f"    {reason:<40} {count:>5}")

    if PROPOSED_ALIASES.exists():
        with PROPOSED_ALIASES.open("r", encoding="utf-8", newline="") as handle:
            proposals = list(csv.DictReader(handle))
        clean = [row for row in proposals if row["collision"] == "none"]
        print(
            f"\n  {len(clean)} alias proposals with no collision are waiting for human "
            f"review in {PROPOSED_ALIASES.relative_to(ROOT)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
