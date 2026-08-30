"""Shared paths, model settings and run bookkeeping for the HiREC variant.

Deliberately does not know the gold file exists -- it defines no gold path and
never names one. hirec_evaluate.py is the only module that does, which keeps the
runtime/evaluation split structural rather than a convention someone has to
remember. A test scans the runtime modules for that filename, so even a mention
in a comment here would fail the suite.

The corpus and the question set are read from the koblex experiment's data
directory. Sharing the inputs rather than copying them is what makes these runs
comparable to that experiment's b0 and b1 runs; a copy would drift. The index
database is private to this experiment because its schema differs.
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

# Shared, read-only inputs.
SHARED_DATA_DIR = ROOT / "experiments" / "koblex-inspired-retrieval" / "data"
CORPUS_PATH = SHARED_DATA_DIR / "statute.jsonl"
QUESTIONS_PATH = SHARED_DATA_DIR / "smoke_test_20_questions.jsonl"

# Private to this experiment: the schema carries act_id, section_id and ordinal.
INDEX_DB_PATH = DATA_DIR / "hirec_index.sqlite3"

DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"

# Retrieval.
DEFAULT_SEED_TOP_K = 20          # BM25 hits used as section seeds
DEFAULT_MAX_ACTS = 3
DEFAULT_MAX_POOL_RECORDS = 220   # above the measured max expanded pool of 179
DEFAULT_MAX_POOL_CHARS = 120_000

# Curation loop.
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_MAX_RELEVANT_IDS = 25

PROMPT_VERSION = "v1"
PROMPT_FILES = {
    "act_selection": "act_selection.md",
    "query_transform": "query_transform.md",
    "evidence_curation": "evidence_curation.md",
    "grounded_answer": "grounded_answer.md",
}

# Reasoning effort per pipeline stage. evidence_curation runs at medium where the
# comparable koblex selection stage ran at low; that is a recorded divergence,
# not an oversight -- see DIVERGENT_ALWAYS.
REASONING_EFFORT = {
    "act_selection": "low",
    "query_transform": "low",
    "evidence_curation": "medium",
    "final_answer": "medium",
}

# USD per million tokens, for turning measured token counts into a cost figure.
#
# VERIFY THESE AGAINST THE CURRENT PRICE LIST BEFORE QUOTING A COST ANYWHERE.
# Token counts in usage.jsonl are measured and authoritative; the money figure
# derived from them is only as good as this table, which is a hand-entered
# constant that goes stale silently. Every cost number reported carries the
# rates that produced it, so a stale figure can at least be recomputed.
TOKEN_RATES_USD_PER_MILLION = {
    "input": 0.25,
    "output": 2.00,
}
TOKEN_RATES_SOURCE = (
    "hand-entered gpt-5-mini-class list price, not verified against the "
    "provider price list on any particular date")


def cost_usd(input_tokens: int | None, output_tokens: int | None) -> float | None:
    """Cost from measured tokens. None when the counts are unavailable."""
    if input_tokens is None or output_tokens is None:
        return None
    rates = TOKEN_RATES_USD_PER_MILLION
    return round(
        (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1e6,
        6)


# Appended to the curation prompt only under --negative-prior, so the prompt
# file's hash stays stable when the flag is off.
NEGATIVE_PRIOR_BLOCK = (
    "\n\n## Additional instruction\n\n"
    "Most questions about Sri Lankan statute require more than one provision. "
    "Treat the pool as incomplete until every point you listed has at least one "
    "node_id attached to it.\n"
)


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
# fidelity ledger
# --------------------------------------------------------------------------- #

# What this port keeps from HiREC as implemented in
# paper-implementations/LOFin-bench-HiREC/finrag_api/finrag_single_query.py.
FAITHFUL = [
    "hierarchical retrieval: document -> page -> passage becomes "
    "act -> section -> provision",
    "one LLM inference per iteration does filter, answerability, "
    "missing-information and complementary question together",
    "the original question is never mutated and is what the curator and the "
    "answering stage always see",
    "the refined query drives retrieval only; it is never evidence and is never "
    "shown to the curator or the answering stage",
    "accumulated evidence is re-filtered each iteration rather than frozen",
    "saturation hatch: an incomplete verdict that nonetheless marks "
    "max_relevant_ids provisions relevant is treated as complete",
    "budget exhaustion appends one uncurated last-resort retrieval and answers "
    "anyway rather than failing",
]

# Where it deliberately departs, and why. Recorded per run so no calibration
# number is ever read without knowing which of these was on.
DIVERGENT_ALWAYS = [
    "completeness is derived from the coverage table rather than taken from the "
    "model's boolean, and both values are recorded; the comparable koblex run "
    "reported complete on all 20 questions including 3 that were not",
    "the curation schema forces a per-point coverage table, a cross-reference "
    "list and sibling accounting to be emitted before the completeness boolean",
    "curation runs at reasoning effort medium; the comparable koblex selection "
    "stage ran at low",
    "the answer is a separate stage rather than a field of the curation call, "
    "which preserves the citation gate and comparability with koblex b1",
    "structured outputs with one corrective retry, rather than parsing a "
    "hash-delimited text blob",
    "max_iterations 3, not HiREC's 4: a K=20 section pool already contains all "
    "gold, so a fourth round has nothing to find",
    "max_relevant_ids 25, not HiREC's 10: gold sets reach 9 provisions and "
    "pools reach 179 records, so a threshold of 10 would fire the saturation "
    "hatch on nearly every question",
    "the curator sees a whole-section pool of up to max_pool_records provisions "
    "rather than 10 flat chunks",
    "no query transform on the first iteration: the koblex b1 run measured that "
    "generated queries cost 4 points of recall@20",
    "the list of queries already tried is fed back to the rewriting stage to "
    "prevent it repeating a query; it is deliberately withheld from the curator, "
    "so no generated string can reach a prompt that judges or cites evidence",
]


def fidelity_ledger(*, negative_prior: bool, xref_precheck: bool,
                    freeze_evidence: bool, gate_on: str,
                    act_selector: str) -> dict:
    """The faithful/divergent ledger for one run's flag combination."""
    divergent = list(DIVERGENT_ALWAYS)
    if negative_prior:
        divergent.append(
            "--negative-prior: the curation prompt is told to treat the pool as "
            "incomplete until every point has a node_id attached. This shifts "
            "the prior and will manufacture false incompletes.")
    if xref_precheck:
        divergent.append(
            "--xref-precheck: a deterministic cross-reference scan can force "
            "incompleteness independently of the model. Not HiREC at all; it "
            "exploits the fact that statutes cross-reference machine-readably.")
    if freeze_evidence:
        divergent.append(
            "--freeze-evidence: curated evidence accumulates and is never "
            "dropped. HiREC re-filters, which can lose a provision it kept "
            "earlier.")
    if gate_on == "model":
        divergent.append(
            "--gate-on model: the loop gates on the model's own boolean. That "
            "is the faithful HiREC behaviour and is expected to stop after one "
            "iteration on every question.")
    if act_selector != "derived":
        divergent.append(
            f"--act-selector {act_selector}: an explicit act-selection stage "
            "rather than deriving the act set from the BM25 seed hits.")
    return {"faithful": list(FAITHFUL), "divergent": divergent}


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
    corpus_count: int,
    question_count: int,
    limit: int | None,
    include_model: bool,
    questions_path: Path | None = None,
    extra: dict | None = None,
) -> dict:
    """Run provenance. Never records the API key."""
    config: dict[str, Any] = {
        "variant": variant,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_path": display_path(CORPUS_PATH),
        "corpus_records": corpus_count,
        "question_path": display_path(questions_path or QUESTIONS_PATH),
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
    if extra:
        config.update(extra)
    return config
