"""Create a deterministic lawyer-review sample of citation edges."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TARGETS = {"explicit": 15, "same_sentence": 9, "nearest_unique": 6}
FIELDS = [
    "sample_id", "case_id", "case_citation", "case_title", "source_id",
    "statute_title", "section", "confidence", "confidence_label",
    "evidence_snippet", "extraction_status", "lawyer_decision",
    "lawyer_notes", "reviewed_by", "reviewed_at",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stable_key(row: dict[str, str]) -> str:
    value = "|".join((row["case_id"], row["source_id"], row["section"]))
    return hashlib.sha256(f"draftly-lawyer-sample-v1|{value}".encode()).hexdigest()


def choose(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    rows = sorted(rows, key=stable_key)
    chosen: list[dict[str, str]] = []
    used_cases: set[str] = set()
    used_sources: set[str] = set()
    for require_new_source, require_new_case in ((True, True), (False, True), (False, False)):
        for row in rows:
            if len(chosen) >= count:
                return chosen
            if row in chosen:
                continue
            if require_new_source and row["source_id"] in used_sources:
                continue
            if require_new_case and row["case_id"] in used_cases:
                continue
            chosen.append(row)
            used_cases.add(row["case_id"])
            used_sources.add(row["source_id"])
    return chosen


def main() -> None:
    sources = {
        row["source_id"]: row["official_title"]
        for row in read_csv(PROCESSED / "source-registry.csv")
    }
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PROCESSED / "case_statute_section_links.csv"):
        if not all((row["case_id"], row["case_citation"], row["source_id"],
                    row["section"], row["evidence_snippet"])):
            continue
        grouped[row["confidence_label"]].append(row)

    selected: list[dict[str, str]] = []
    for label, count in TARGETS.items():
        sample = choose(grouped[label], count)
        if len(sample) != count:
            raise RuntimeError(f"Could only select {len(sample)}/{count} {label} edges")
        selected.extend(sample)

    output = []
    for index, row in enumerate(selected, 1):
        output.append({
            "sample_id": f"VERIFY-{index:03d}",
            "case_id": row["case_id"],
            "case_citation": row["case_citation"],
            "case_title": row["case_title"],
            "source_id": row["source_id"],
            "statute_title": sources[row["source_id"]],
            "section": row["section"],
            "confidence": row["confidence"],
            "confidence_label": row["confidence_label"],
            "evidence_snippet": row["evidence_snippet"],
            "extraction_status": "unverified",
            "lawyer_decision": "",
            "lawyer_notes": "",
            "reviewed_by": "",
            "reviewed_at": "",
        })

    destination = PROCESSED / "verification-sample.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(
        f"verification_rows={len(output)} cases={len({r['case_id'] for r in output})} "
        f"sources={len({r['source_id'] for r in output})}"
    )


if __name__ == "__main__":
    main()
