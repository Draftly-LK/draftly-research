"""Fail unless the canonical file-based retrieval store is internally complete."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
REQUIRED = {
    "documents.csv", "cases.jsonl", "topics.csv", "topic-sources.csv",
    "topics.json", "source-registry.csv", "case_statute_section_links.csv",
    "unresolved_citations.csv", "verification-sample.csv", "README.md",
}


def read_csv(filename: str) -> list[dict[str, str]]:
    with (PROCESSED / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> None:
    missing = sorted(name for name in REQUIRED if not (PROCESSED / name).is_file())
    assert not missing, f"Missing processed outputs: {missing}"

    documents = read_csv("documents.csv")
    doc_by_id = {row["doc_id"]: row for row in documents}
    assert len(doc_by_id) == len(documents), "Duplicate document IDs"
    text_paths = [row["text_path"] for row in documents]
    assert len(set(text_paths)) == len(text_paths), "Duplicate document text paths"
    assert all(path.startswith("data/processed/docs/") for path in text_paths)

    indexed_paths = set(text_paths)
    disk_paths = {
        relative(path) for path in (PROCESSED / "docs").rglob("*.md")
    }
    assert disk_paths == indexed_paths, (
        f"Document index/files differ: unindexed={len(disk_paths - indexed_paths)} "
        f"missing={len(indexed_paths - disk_paths)}"
    )
    for row in documents:
        path = ROOT / row["text_path"]
        data = path.read_bytes()
        text = data.decode("utf-8")
        assert len(re.sub(r"\s+", "", text)) >= 200, row["doc_id"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["doc_id"]
        assert row["status"] == "converted", (row["doc_id"], row["status"])

    with (PROCESSED / "cases.jsonl").open(encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle if line.strip()]
    case_by_id = {row["case_id"]: row for row in cases}
    assert len(case_by_id) == len(cases), "Duplicate case IDs"
    for case in cases:
        assert case["doc_id"] in doc_by_id, case["case_id"]
        assert case["text_path"] == doc_by_id[case["doc_id"]]["text_path"]
        assert case["text_path"].startswith("data/processed/docs/")
        assert case["status"] == "unverified"

    source_ids = {row["source_id"] for row in read_csv("source-registry.csv")}
    links = read_csv("case_statute_section_links.csv")
    link_keys = set()
    for row in links:
        key = (row["case_id"], row["source_id"], row["section"].casefold())
        assert key not in link_keys, key
        link_keys.add(key)
        assert row["case_id"] in case_by_id
        assert row["source_id"] in source_ids
        assert row["section"] and row["evidence_snippet"]
        assert row["confidence_label"] in {"explicit", "same_sentence", "nearest_unique"}
        assert row["review_status"] == "unverified"

    unresolved = read_csv("unresolved_citations.csv")
    for row in unresolved:
        assert row["case_id"] in case_by_id
        assert row["section"] and row["evidence_snippet"] and row["reason"]
        assert row["review_status"] == "unresolved"

    verification = read_csv("verification-sample.csv")
    assert len(verification) == 30
    for row in verification:
        key = (row["case_id"], row["source_id"], row["section"].casefold())
        assert key in link_keys
        assert row["case_citation"] and row["evidence_snippet"]
        assert row["extraction_status"] == "unverified"
        assert not any(row[field] for field in (
            "lawyer_decision", "lawyer_notes", "reviewed_by", "reviewed_at"
        ))

    conversion_rows, _ = _read_manifest("conversion-registry.csv")
    incomplete_conversion = [
        row["source_id"] for row in conversion_rows
        if row["status"] not in {"converted", "fallback", "fallback-pdftotext"}
    ]
    assert not incomplete_conversion, incomplete_conversion

    usage = json.loads((PROCESSED / "documentai-usage.json").read_text(encoding="utf-8"))
    assert int(usage["page_limit"]) == 2_000
    assert int(usage["pages_used"]) <= int(usage["page_limit"])
    assert len(usage["events"]) == int(usage["pages_used"])

    commonlii = [row for row in documents if row["source"] == "commonlii"]
    kinds = Counter(row["kind"] for row in documents)
    summary = {
        "documents": len(documents),
        "document_files": len(disk_paths),
        "cases": len(cases),
        "commonlii_conveyancing_joined": len(commonlii),
        "document_kinds": dict(sorted(kinds.items())),
        "section_links": len(links),
        "linked_cases": len({row["case_id"] for row in links}),
        "unresolved_mentions": len(unresolved),
        "verification_rows": len(verification),
        "document_ai_pages_used": int(usage["pages_used"]),
        "document_ai_page_limit": int(usage["page_limit"]),
    }
    assert summary["commonlii_conveyancing_joined"] == 3_703
    print(json.dumps(summary, indent=2))


def _read_manifest(filename: str) -> tuple[list[dict[str, str]], list[str]]:
    path = ROOT / "data/legal-sources/manifests" / filename
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


if __name__ == "__main__":
    main()
