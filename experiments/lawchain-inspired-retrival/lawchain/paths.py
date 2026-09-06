from __future__ import annotations

from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]

FINALIZED_DIR = REPO_ROOT / "data" / "legal-sources" / "library" / "finalized"
SOURCE_REGISTRY_CSV = REPO_ROOT / "data" / "processed" / "source-registry.csv"

CACHE_DIR = MODULE_ROOT / ".cache"
LEXICAL_CACHE_DIR = CACHE_DIR
DENSE_CACHE_DIR = CACHE_DIR
GRAPH_CACHE_DIR = CACHE_DIR

EVAL_DIR = REPO_ROOT / "evaluation" / "runs" / "lawchain-v1"


def lexical_cache_path(fingerprint: str) -> Path:
    return LEXICAL_CACHE_DIR / f"lexical-{fingerprint[:16]}.pkl"


def dense_cache_dir(fingerprint: str) -> Path:
    return DENSE_CACHE_DIR / f"dense-{fingerprint[:16]}"


def graph_cache_path(fingerprint: str) -> Path:
    return GRAPH_CACHE_DIR / f"graph-{fingerprint[:16]}.pkl"
