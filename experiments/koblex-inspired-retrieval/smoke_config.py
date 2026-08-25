"""Shared paths, model settings and run bookkeeping for the smoke test.

Deliberately does not know the gold file exists -- it defines no gold path and
never names one. evaluate.py is the only module that does, which keeps the
runtime/evaluation split structural rather than a convention someone has to
remember. A test scans the runtime modules for that filename, so even a mention
in a comment here would fail the suite.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA_DIR = HERE / "data"
PROMPTS_DIR = HERE / "prompts"
RUNS_DIR = HERE / "runs"

CORPUS_PATH = DATA_DIR / "statute.jsonl"
QUESTIONS_PATH = DATA_DIR / "smoke_test_20_questions.jsonl"
INDEX_DB_PATH = DATA_DIR / "bm25_index.sqlite3"

DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_TOP_K = 20
DEFAULT_MAX_CANDIDATES = 40

PROMPT_VERSION = "v1"
PROMPT_FILES = {
    "query_generation": "query_generation.md",
    "provision_selection": "provision_selection.md",
    "grounded_answer": "grounded_answer.md",
}

# Reasoning effort per pipeline stage.
REASONING_EFFORT = {
    "query_generation": "low",
    "provision_selection": "low",
    "final_answer": "medium",
}


def load_dotenv_if_present() -> None:
    """Best-effort .env load so OPENAI_API_KEY can live outside the shell."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_file, override=False)


def model_name() -> str:
    return os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def display_path(path: Path) -> str:
    """Repo-relative when possible, absolute otherwise (temp dirs, other drives)."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# --------------------------------------------------------------------------- #
# jsonl helpers
# --------------------------------------------------------------------------- #

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    payload = ("\n".join(lines) + "\n") if lines else ""
    path.write_text(payload, encoding="utf-8", newline="\n")


def write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- #
# prompts
# --------------------------------------------------------------------------- #

def prompt_text(name: str) -> str:
    return (PROMPTS_DIR / PROMPT_FILES[name]).read_text(encoding="utf-8")


def prompt_hashes() -> dict[str, str]:
    digests = {}
    for name, filename in sorted(PROMPT_FILES.items()):
        path = PROMPTS_DIR / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        digests[name] = digest
    return digests


# --------------------------------------------------------------------------- #
# runs
# --------------------------------------------------------------------------- #

def resolve_run_dir(run_name: str | None, variant: str) -> Path:
    name = run_name or f"{utc_timestamp()}-{variant}"
    directory = RUNS_DIR / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_run_config(
    *,
    variant: str,
    top_k: int,
    max_candidates: int,
    corpus_count: int,
    question_count: int,
    limit: int | None,
    include_model: bool,
) -> dict:
    """Run provenance. Never records the API key."""
    config: dict[str, Any] = {
        "variant": variant,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "top_k": top_k,
        "max_candidates": max_candidates,
        "corpus_path": display_path(CORPUS_PATH),
        "corpus_records": corpus_count,
        "question_path": display_path(QUESTIONS_PATH),
        "question_count": question_count,
        "limit": limit,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": prompt_hashes(),
    }
    if include_model:
        config["model"] = model_name()
        config["reasoning_effort"] = dict(REASONING_EFFORT)
    else:
        config["model"] = None
        config["reasoning_effort"] = None
    return config
