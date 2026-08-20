"""Convert the flat ``judgments.csv`` parser output to JSONL.

This is a faithful re-serialisation of the CSV, not a richer record: the
nested structures live in ``parsed/<db>/records/<bucket>.jsonl`` (see
``src/parsers/parse_archive.py``) and the CSV only keeps their counts.

Usage::

    python scripts/convert_judgments_csv_to_jsonl.py                 # LKCA + LKSC
    python scripts/convert_judgments_csv_to_jsonl.py --db LKSC
    python scripts/convert_judgments_csv_to_jsonl.py --csv path/to/judgments.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PARSED_ROOT = REPO_ROOT / "data" / "commonlii" / "parsed"
DEFAULT_DBS = ("LKCA", "LKSC")


def convert(csv_path: Path, out_path: Path | None = None) -> Path:
    out_path = out_path or csv_path.with_suffix(".jsonl")

    # numpy_nullable keeps integer columns as Int64 instead of coercing them to
    # float the moment a row has a blank (reported_year 1878 -> 1878.0).
    df = pd.read_csv(csv_path, dtype_backend="numpy_nullable")

    df.to_json(out_path, orient="records", lines=True, force_ascii=False)

    print(f"{csv_path.relative_to(REPO_ROOT)} -> {out_path.relative_to(REPO_ROOT)}")
    print(f"  {len(df)} rows, {len(df.columns)} keys, {out_path.stat().st_size / 1e6:.1f} MB")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="convert a single judgments.csv")
    parser.add_argument("--out", type=Path, help="output path (with --csv)")
    parser.add_argument(
        "--db",
        action="append",
        choices=DEFAULT_DBS,
        help="database to convert; repeatable. Default: all",
    )
    args = parser.parse_args()

    if args.csv:
        convert(args.csv, args.out)
        return

    for db in args.db or DEFAULT_DBS:
        convert(PARSED_ROOT / db / "judgments.csv")


if __name__ == "__main__":
    main()
