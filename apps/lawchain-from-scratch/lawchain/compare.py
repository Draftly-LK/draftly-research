"""Evaluation harness comparing this module against src/draftly/retrieval.

This is the ONE deliberate exception to the independence boundary the rest
of `lawchain/` holds to: comparing against the existing engine is the whole
point of a benchmark, so importing it here is intentional, not scope creep.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable

from draftly.retrieval.evaluation import aggregate_scores, parse_expected_sections, read_gold, score_question
from draftly.retrieval.models import StatuteQuery
from draftly.retrieval.search import search as existing_search

from . import engine
from .extraction import select_statute_files
from .paths import EVAL_DIR

PAPER_REFERENCE = {
    "precision_at_5": 0.8345,
    "recall_at_5": 0.9357,
    "label": "LawChain (Atukorala, Appuhami, de Silva; ICML 2026 GlobalSouthML), Sri Lankan statutes deployment",
}


def in_scope_source_ids() -> set[str]:
    return set(select_statute_files())


def filtered_gold_rows() -> list[dict[str, str]]:
    """GOLD_CSV rows restricted to the statute scope this module indexes.

    A row is kept only if every expected section belongs to an in-scope
    statute -- mixed in/out-of-scope rows are dropped entirely so both
    engines are scored on an identical question set.
    """
    scope = in_scope_source_ids()
    rows = []
    for row in read_gold():
        expected = parse_expected_sections(row["expected_sections"])
        if not expected:
            continue
        if all(section_id.split(":", 1)[0] in scope for section_id in expected):
            rows.append(row)
    return rows


def _score_engine(rows: list[dict[str, str]], retrieve: Callable[[str, str], list[str]]) -> dict[str, Any]:
    scores = []
    predictions = []
    for row in rows:
        expected = parse_expected_sections(row["expected_sections"])
        retrieved = retrieve(row["question"], row.get("workflow_step", ""))
        predictions.append(
            {
                "question_id": row["question_id"],
                "question": row["question"],
                "expected_sections": ";".join(sorted(expected)),
                "retrieved_sections": ";".join(retrieved),
            }
        )
        scores.append(score_question(row["question_id"], expected, retrieved))
    return {"metrics": aggregate_scores(scores), "predictions": predictions, "scores": scores}


def _lawchain_retrieve(question: str, _workflow_step: str) -> list[str]:
    return [hit.section_id for hit in engine.retrieve(question, limit=10)]


def _existing_retrieve(question: str, workflow_step: str) -> list[str]:
    hits = existing_search(StatuteQuery(text=question, topic_slug=workflow_step or None, limit=10))
    return [hit.section_id for hit in hits]


def run_comparison(output_dir: Path = EVAL_DIR) -> dict[str, Any]:
    rows = filtered_gold_rows()

    lawchain_result = _score_engine(rows, _lawchain_retrieve)
    existing_result = _score_engine(rows, _existing_retrieve)

    comparison = {
        "questions": len(rows),
        "lawchain_from_scratch": lawchain_result["metrics"],
        "existing_engine_statutes_bm25_v1": existing_result["metrics"],
        "paper_reference": PAPER_REFERENCE,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    _write_csv(output_dir / "predictions-lawchain.csv", lawchain_result["predictions"])
    _write_csv(output_dir / "predictions-existing.csv", existing_result["predictions"])
    _write_csv(output_dir / "per-question-scores-lawchain.csv", lawchain_result["scores"])
    _write_csv(output_dir / "per-question-scores-existing.csv", existing_result["scores"])
    return comparison


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
