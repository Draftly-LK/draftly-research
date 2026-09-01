"""Evaluate the statute retrieval engine on the IL-PCSR-style LSR gold set.

Legal Statute Retrieval (LSR), per IL-PCSR ("Legal Corpus for Prior Case
and Statute Retrieval", EMNLP 2025): given a case with its statute citation
masked out, retrieve the statute provision it actually cites. The gold set
is built by ``scripts/legal-statute-retrieval/00_build_lsr_gold.py`` from
this repo's own verified case-to-statute links; nothing here trains a
model -- it benchmarks the existing BM25+dense+graph engine (``search()``)
against that task, reusing the scoring functions already used for the
statutes-only gold set in ``evaluation.py``.

Every gold row carries a ``temporal_status`` (``applicable`` /
``superseded-since-judgment`` / ``history-unknown``, from
``build_section_versions.py``). Metrics are reported both overall and
per status, because the index holds only the current text of each section:
a case whose section changed after judgment (``superseded-since-judgment``)
is being asked to retrieve text that is not the version the court applied,
which will suppress its recall for reasons that have nothing to do with the
retrieval method -- see ``data/processed/temporal-alignment-report.md``.
Splitting the metric keeps that limitation visible instead of averaging it
away.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evaluation import aggregate_scores, score_question, write_csv
from .index import build_index
from .models import StatuteQuery
from .paths import DATA_PROCESSED, REPO_ROOT
from .search import search

LSR_GOLD_JSONL = DATA_PROCESSED / "lsr_gold.jsonl"
LSR_EVAL_DIR = REPO_ROOT / "evaluation" / "runs" / "statute-retrieval-lsr-v1"

TEMPORAL_STATUSES = ("applicable", "superseded-since-judgment", "history-unknown")


@dataclass(frozen=True)
class LsrGoldRow:
    query_id: str
    case_id: str
    section_id: str
    query_text: str
    query_construction: str
    case_year: int | None
    temporal_status: str


def load_lsr_gold(path: Path = LSR_GOLD_JSONL) -> list[LsrGoldRow]:
    rows: list[LsrGoldRow] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rows.append(
                LsrGoldRow(
                    query_id=record["query_id"],
                    case_id=record["case_id"],
                    section_id=record["section_id"],
                    query_text=record["query_text"],
                    query_construction=record["query_construction"],
                    case_year=record.get("case_year"),
                    temporal_status=record["temporal_status"],
                )
            )
    return rows


def run_lsr_evaluation(
    gold_path: Path = LSR_GOLD_JSONL,
    output_dir: Path = LSR_EVAL_DIR,
) -> dict[str, Any]:
    build_index(force=False)
    gold_rows = load_lsr_gold(gold_path)

    predictions: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    scores_by_status: dict[str, list[dict[str, Any]]] = {status: [] for status in TEMPORAL_STATUSES}

    for row in gold_rows:
        hits = search(StatuteQuery(text=row.query_text, limit=10))
        retrieved = [hit.section_id for hit in hits]

        expected = {row.section_id}
        score = score_question(row.query_id, expected, retrieved)
        score["temporal_status"] = row.temporal_status
        scores.append(score)
        scores_by_status.setdefault(row.temporal_status, []).append(score)

        predictions.append(
            {
                "query_id": row.query_id,
                "case_id": row.case_id,
                "expected_section": row.section_id,
                "retrieved_sections": ";".join(retrieved),
                "top_hit": retrieved[0] if retrieved else "",
                "query_construction": row.query_construction,
                "temporal_status": row.temporal_status,
            }
        )

    metrics: dict[str, Any] = {"overall": aggregate_scores(scores) if scores else {"questions": 0}}
    for status, status_scores in scores_by_status.items():
        metrics[status] = aggregate_scores(status_scores) if status_scores else {"questions": 0}
    metrics["label"] = "development-only: derived gold, small sample, not lawyer-verified"
    metrics["generated_at"] = datetime.now(timezone.utc).isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "predictions.csv", predictions)
    write_csv(output_dir / "per-question-scores.csv", scores)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "config.json").write_text(
        json.dumps(
            {
                "run_id": "statute-retrieval-lsr-v1",
                "task": "legal-statute-retrieval (IL-PCSR-derived)",
                "gold": str(gold_path),
                "notes": (
                    "Gold built from verified case-to-statute links only; expected_section "
                    "is a single section ID per query, not a set."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics
