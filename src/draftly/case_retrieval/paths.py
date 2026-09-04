from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PROCESSED = REPO_ROOT / "data" / "processed"

CASES_JSONL = DATA_PROCESSED / "cases.jsonl"
CASE_TOPIC_LINKS_CSV = DATA_PROCESSED / "legal-case-index" / "case_topic_links.csv"
RESOLVED_LINKS_CSV = REPO_ROOT / "scripts" / "case-law-statute-linking" / "output" / "resolved_links.csv"
RULES_CSV = REPO_ROOT / "scripts" / "case-law-information-extraction" / "output" / "rules_high_confidence.csv"
COMMONLII_JUDGMENTS_JSONL = {
    "LKCA": REPO_ROOT / "data" / "commonlii" / "parsed" / "LKCA" / "judgments.jsonl",
    "LKSC": REPO_ROOT / "data" / "commonlii" / "parsed" / "LKSC" / "judgments.jsonl",
}

INDEX_DIR = DATA_PROCESSED / "retrieval-indexes" / "cases-conveyancing-bm25-v1"
INDEX_POINTER = INDEX_DIR / "active.json"
EVAL_DIR = REPO_ROOT / "evaluation" / "runs" / "similar-case-retrieval-v1"


def fingerprinted_index_db(fingerprint: str, generation: str) -> Path:
    return INDEX_DIR / f"cases-{fingerprint[:16]}-{generation}.sqlite"
