"""Parse every LKSC judgment with its layout parser and write records + CSVs.

Reads the per-category JSON files produced by split_categories.py, parses each
HTML file with the parser registered for its bucket, runs the semantic
extractors, and writes:

- ``records/<bucket>.jsonl`` -- full evidence-linked records, one per judgment
- ``<bucket>.csv``           -- flattened core fields per bucket
- ``judgments.csv``          -- all buckets combined

Usage: python src/parsers/parse_archive.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from extract import build_record
from layouts import PARSERS

REPO_ROOT = Path(__file__).resolve().parents[2]

BUCKETS = (
    "paragraph_nlr",
    "dense_br_nlr",
    "structured_slr",
    "late_slr_font",
    "uncertain",
)


def flatten(record: dict, text: str) -> dict:
    """Core fields for the CSV views; the full detail stays in the JSONL."""
    identity = record["identity"]
    report = record["report"]
    dates = record["dates"]
    details = record["case_details"]
    judgment = record["judgment"]
    quality = record["quality"]
    return {
        "case_id": identity["case_id"],
        "file": record["provenance"]["file"],
        "case_name": identity["case_name_raw"],
        "neutral_citation": identity["neutral_citation"],
        "deciding_court": identity["deciding_court"],
        "report_series": report["series"],
        "reported_year": report["reported_year"],
        "volume": report["volume"],
        "start_page": report["start_page"],
        "decision_date": dates["decision_date"],
        "hearing_dates": "; ".join(dates["hearing_dates"]),
        "proceeding_type": details["proceeding_type"],
        "case_numbers": "; ".join(details["case_numbers"]),
        "originating_court": details["originating_court"],
        "parties": "; ".join(
            f"{p['name']}{' and others' if p.get('and_others') else ''}"
            f" ({p['role'] or 'unknown'})"
            for p in record["parties"]
        ),
        "bench": "; ".join(
            f"{j['name']} {j['title']}" if j["title"] else j["name"]
            for j in record["bench"]
        ),
        "counsel_count": len(record["representation"]["counsel"]),
        "cur_adv_vult": record["representation"]["cur_adv_vult"],
        "catchwords": "; ".join(record["headnote"]["catchwords"]),
        "holdings_count": len(record["headnote"]["holdings"]),
        "cases_referred_count": len(record["headnote"]["cases_referred_to"]),
        "opinion_author": judgment["opinion_author"],
        "agreements_count": len(judgment["agreements"]),
        "disposition": judgment["disposition"],
        "costs_order": judgment["costs_order"],
        "cases_cited_count": len(record["authorities"]["cases_cited"]),
        "legislation_count": len(record["authorities"]["legislation"]),
        "category": record["layout"]["category"],
        "bucket": record["layout"]["bucket"],
        "confidence": record["layout"]["confidence"],
        "paragraph_count": len(record["blocks"]),
        "char_count": len(text),
        "printed_pages": " ".join(str(n) for n in report["printed_pages"]),
        "has_page_missed": quality["has_page_missed"],
        "has_encoding_errors": quality["has_encoding_errors"],
        "has_malformed_tags": quality["has_malformed_tags"],
        "text": text,
    }


def parse_bucket(
    bucket: str, categories_dir: Path, html_root: Path, records_dir: Path
) -> pd.DataFrame:
    payload = json.loads(
        (categories_dir / f"{bucket}.json").read_text(encoding="utf-8")
    )
    parse = PARSERS[bucket]

    rows = []
    with (records_dir / f"{bucket}.jsonl").open("w", encoding="utf-8") as sink:
        for meta in payload["files"]:
            path = html_root / meta["file"]
            parsed = parse(path, meta["file"])
            record = build_record(path, meta, parsed, bucket)
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            rows.append(flatten(record, parsed.text))
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--categories-dir",
        type=Path,
        default=REPO_ROOT / "data" / "commonlii" / "layout-categories",
    )
    parser.add_argument(
        "--html-root",
        type=Path,
        default=REPO_ROOT / "data" / "commonlii" / "raw" / "LKSC",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "commonlii" / "parsed",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for bucket in BUCKETS:
        frame = parse_bucket(
            bucket, args.categories_dir.resolve(), args.html_root.resolve(), records_dir
        )
        frame.to_csv(output_dir / f"{bucket}.csv", index=False)
        empty = int((frame["paragraph_count"] == 0).sum()) if not frame.empty else 0
        print(f"{bucket}: {len(frame)} files, {empty} empty parses")
        frames.append(frame)

    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["case_id"])
        .reset_index(drop=True)
    )
    combined.to_csv(output_dir / "judgments.csv", index=False)
    print(f"judgments.csv: {len(combined)} rows -> {output_dir}")

    for column in (
        "neutral_citation", "decision_date", "opinion_author", "disposition",
        "proceeding_type", "catchwords",
    ):
        coverage = combined[column].notna() & (combined[column].astype(str) != "")
        print(f"coverage {column}: {int(coverage.sum())}/{len(combined)}")

    missed = combined.loc[combined["has_page_missed"], "file"].tolist()
    if missed:
        print(f"files with 'page missed' gaps: {missed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
