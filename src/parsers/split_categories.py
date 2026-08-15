"""Split layout-categories.json into per-category JSON files.

Confident records go to ``<category>.json``; records whose top score is below
0.75 or whose top-two margin is below 0.5 go to ``uncertain.json`` instead
(same thresholds as the EDA notebook). Each output keeps the full records so
downstream parsing needs no other input.

Usage: python src/parsers/split_categories.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LAYOUTS = (
    "paragraph_nlr",
    "dense_br_nlr",
    "structured_slr",
    "late_slr_font",
)
TOP_SCORE_THRESHOLD = 0.75
MARGIN_THRESHOLD = 0.5


def is_uncertain(record: dict) -> bool:
    scores = sorted(record["layout_scores"].values(), reverse=True)
    return scores[0] < TOP_SCORE_THRESHOLD or scores[0] - scores[1] < MARGIN_THRESHOLD


def split(report_path: Path, output_dir: Path) -> dict[str, int]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    buckets: dict[str, list[dict]] = {layout: [] for layout in LAYOUTS}
    buckets["uncertain"] = []

    for record in report["files"]:
        bucket = "uncertain" if is_uncertain(record) else record["category"]
        buckets[bucket].append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, records in buckets.items():
        payload = {
            "source_report": report_path.name,
            "generated_at": report["generated_at"],
            "bucket": name,
            "file_count": len(records),
            "files": records,
        }
        (output_dir / f"{name}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    return {name: len(records) for name, records in buckets.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "data" / "commonlii" / "layout-categories.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "commonlii" / "layout-categories",
    )
    args = parser.parse_args()

    counts = split(args.report.resolve(), args.output_dir.resolve())
    total = sum(counts.values())
    for name, count in counts.items():
        print(f"{name}: {count}")
    print(f"total: {total} -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
