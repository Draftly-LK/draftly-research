"""Repair CommonLII index rows that exist locally but vanished from year indexes.

CommonLII's database landing pages do not always list every historical year.
The local conveyancing harvest can therefore contain valid judgment files whose
``(db, year, case_no)`` key is absent from the rebuilt full citation index.

This script recovers title, citation, and URL from the saved judgment header,
adds the missing rows to the full index, and refreshes the corresponding rows in
the conveyancing manifest. It makes no network calls.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "data/legal-sources/manifests"
INDEX_PATH = MANIFESTS / "case-law-commonlii-index.csv"
CONVEYANCING_PATH = MANIFESTS / "case-law-commonlii-conveyancing.csv"

KEY_FIELDS = ("db", "year", "case_no")
CITATION_RX = re.compile(
    r"(\(\d{4}\)\s*\d*\s*Sri\s*L\.?\s*R\.?\s*\d+|\d+\s*N\.?L\.?R\.?\s*\d+)",
    re.I,
)
URL_RX = re.compile(r"https?://(?:www\.)?commonlii\.org/lk/cases/\S+?\.html", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return tuple(row[field].strip() for field in KEY_FIELDS)


def recover_metadata(row: dict[str, str]) -> dict[str, str]:
    text_path = ROOT / row["text_file"]
    text = text_path.read_text(encoding="utf-8", errors="replace")
    header = text[:2000]
    title = re.split(r"\s+Home\s*\|", header, maxsplit=1, flags=re.I)[0].strip()
    citation_match = CITATION_RX.search(title)
    url_match = URL_RX.search(text[-1000:])
    db, year, case_no = key(row)
    canonical_url = f"https://www.commonlii.org/lk/cases/{db}/{year}/{case_no}.html"
    return {
        "citation": citation_match.group(0).strip() if citation_match else "",
        "title": title[:300],
        "url": url_match.group(0).rstrip(".,)") if url_match else canonical_url,
    }


def sort_key(row: dict[str, str]) -> tuple[str, int, int]:
    return row["db"], int(row["year"]), int(row["case_no"])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def repair() -> tuple[int, int, int]:
    index_rows = read_csv(INDEX_PATH)
    conveyancing_rows = read_csv(CONVEYANCING_PATH)
    index_by_key = {key(row): row for row in index_rows}
    missing_before = [row for row in conveyancing_rows if key(row) not in index_by_key]

    for row in missing_before:
        metadata = recover_metadata(row)
        db, year, case_no = key(row)
        recovered = {
            "db": db,
            "year": year,
            "case_no": case_no,
            **metadata,
        }
        index_by_key[(db, year, case_no)] = recovered
        row.update(metadata)

    repaired_index = sorted(index_by_key.values(), key=sort_key)
    repaired_conveyancing = sorted(conveyancing_rows, key=sort_key)
    write_csv(
        INDEX_PATH,
        repaired_index,
        ["db", "year", "case_no", "citation", "title", "url"],
    )
    write_csv(
        CONVEYANCING_PATH,
        repaired_conveyancing,
        [
            "db",
            "year",
            "case_no",
            "citation",
            "title",
            "hits",
            "chars",
            "url",
            "text_file",
        ],
    )

    repaired_keys = {key(row) for row in repaired_index}
    missing_after = sum(key(row) not in repaired_keys for row in repaired_conveyancing)
    blank_metadata = sum(
        not row["title"].strip() or not row["url"].strip()
        for row in repaired_conveyancing
    )
    return len(missing_before), missing_after, blank_metadata


def main() -> None:
    before, after, blank = repair()
    print("Root cause: CommonLII year-index omissions during manifest rebuild.")
    print(f"Conveyancing rows absent from full index: {before} -> {after}")
    print(f"Conveyancing rows with blank title or URL after repair: {blank}")
    if after or blank:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
