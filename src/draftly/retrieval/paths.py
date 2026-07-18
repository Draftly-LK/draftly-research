from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
DOCS_CSV = DATA_PROCESSED / "documents.csv"
SOURCE_REGISTRY_CSV = DATA_PROCESSED / "source-registry.csv"
TOPICS_CSV = DATA_PROCESSED / "topics.csv"
TOPIC_SOURCES_CSV = DATA_PROCESSED / "topic-sources.csv"
GOLD_CSV = DATA_PROCESSED / "retrieval_eval_gold.csv"
INDEX_DIR = DATA_PROCESSED / "retrieval-indexes" / "statutes-bm25-v1"
INDEX_DB = INDEX_DIR / "statutes.sqlite"
EVAL_DIR = REPO_ROOT / "evaluation" / "runs" / "statutes-bm25-v1"

