from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .index import build_index
from .models import StatuteQuery
from .paths import EVAL_DIR, GOLD_CSV
from .search import search


def run_evaluation(output_dir: Path = EVAL_DIR) -> dict[str, Any]:
    build_index(force=False)
    rows = read_gold()
    predictions = []
    scores = []
    for row in rows:
        expected = parse_expected_sections(row["expected_sections"])
        hits = search(StatuteQuery(text=row["question"], topic_slug=row["workflow_step"], limit=10))
        retrieved = [hit.section_id for hit in hits]
        predictions.append(
            {
                "question_id": row["question_id"],
                "question": row["question"],
                "workflow_step": row["workflow_step"],
                "expected_sections": ";".join(sorted(expected)),
                "retrieved_sections": ";".join(retrieved),
                "top_hit": retrieved[0] if retrieved else "",
            }
        )
        scores.append(score_question(row["question_id"], expected, retrieved))

    metrics = aggregate_scores(scores)
    metrics["label"] = "development-only: gold rows are unverified"
    metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "predictions.csv", predictions)
    write_csv(output_dir / "per-question-scores.csv", scores)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "config.json").write_text(
        json.dumps(
            {
                "run_id": "statutes-bm25-v1",
                "corpus": "statutes-and-amendments-only",
                "gold": str(GOLD_CSV),
                "notes": "Excludes NOT_FOUND labels from positive-authority counts.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics


def read_gold() -> list[dict[str, str]]:
    with GOLD_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def parse_expected_sections(value: str) -> set[str]:
    result = set()
    for item in value.split(";"):
        item = item.strip()
        if not item or item.endswith(":NOT_FOUND"):
            continue
        result.add(item)
    return result


def score_question(question_id: str, expected: set[str], retrieved: list[str]) -> dict[str, Any]:
    retrieved_set_at = {k: set(retrieved[:k]) for k in (1, 5, 10)}
    first_rank = next((index + 1 for index, section_id in enumerate(retrieved) if section_id in expected), 0)
    return {
        "question_id": question_id,
        "n_expected": len(expected),
        "recall_at_1": recall(expected, retrieved_set_at[1]),
        "precision_at_5": len(expected & retrieved_set_at[5]) / 5,
        "recall_at_5": recall(expected, retrieved_set_at[5]),
        "recall_at_10": recall(expected, retrieved_set_at[10]),
        "all_recall_at_5": float(bool(expected) and expected.issubset(retrieved_set_at[5])),
        "all_recall_at_10": float(bool(expected) and expected.issubset(retrieved_set_at[10])),
        "mrr": 1.0 / first_rank if first_rank else 0.0,
        "ndcg_at_10": ndcg_at_10(expected, retrieved),
    }


def aggregate_scores(scores: list[dict[str, Any]]) -> dict[str, float]:
    keys = [
        "recall_at_1",
        "precision_at_5",
        "recall_at_5",
        "recall_at_10",
        "all_recall_at_5",
        "all_recall_at_10",
        "mrr",
        "ndcg_at_10",
    ]
    return {key: round(sum(float(row[key]) for row in scores) / len(scores), 4) for key in keys} | {
        "questions": len(scores)
    }


def recall(expected: set[str], retrieved: set[str]) -> float:
    if not expected:
        return 0.0
    return len(expected & retrieved) / len(expected)


def ndcg_at_10(expected: set[str], retrieved: list[str]) -> float:
    if not expected:
        return 0.0
    dcg = 0.0
    for index, section_id in enumerate(retrieved[:10]):
        if section_id in expected:
            dcg += 1.0 / math.log2(index + 2)
    ideal_hits = min(len(expected), 10)
    ideal = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / ideal if ideal else 0.0


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

