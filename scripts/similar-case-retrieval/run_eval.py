"""Run the 20-query similar-case-retrieval test set and write an eval run.

There is no similar-case gold set (no hand-labeled "case X is similar to
fact pattern Y" set exists for this corpus), so this does not compute IR
metrics like the statute engine's evaluation.py does. It runs
`find_similar()` over each of the 20 queries from `build_test_set.py` and
records outcome + hits; appropriateness grading is a separate, human/LLM
step (see RESULTS.md), not computed here.

Usage:
    uv run python scripts/similar-case-retrieval/run_eval.py
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from draftly.case_retrieval.index import build_index
from draftly.case_retrieval.models import CaseQuery
from draftly.case_retrieval.search import find_similar

SCRIPT_DIR = Path(__file__).resolve().parent
TEST_QUERIES = SCRIPT_DIR / "test_queries.jsonl"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "evaluation" / "runs" / "similar-case-retrieval-v1"


def main() -> None:
    queries = [json.loads(line) for line in TEST_QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    stats = build_index(force=False)

    predictions = []
    outcome_counts: dict[str, int] = {}
    for query in queries:
        result = find_similar(CaseQuery(text=query["query_text"], limit=5))
        outcome_counts[result.outcome] = outcome_counts.get(result.outcome, 0) + 1
        predictions.append(
            {
                "query_id": query["query_id"],
                "source_paper": query["source_paper"],
                "source_question": query["source_question"],
                "source_part": query["source_part"],
                "outcome": result.outcome,
                "reason": result.reason,
                "hit_count": len(result.hits),
                "hit_case_ids": ";".join(hit.case_id for hit in result.hits),
                "top_hit_score": result.hits[0].score if result.hits else "",
            }
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "predictions.csv", predictions)

    metrics = {
        "queries": len(queries),
        "outcome_counts": outcome_counts,
        "similar_cases_found_rate": round(outcome_counts.get("similar_cases_found", 0) / len(queries), 4),
        "mean_hits_when_found": round(
            sum(row["hit_count"] for row in predictions if row["outcome"] == "similar_cases_found")
            / max(outcome_counts.get("similar_cases_found", 0), 1),
            2,
        ),
        "corpus_fingerprint": stats.fingerprint,
        "label": "development-only: no similar-case gold set exists; appropriateness is graded separately (RESULTS.md)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "config.json").write_text(
        json.dumps(
            {
                "run_id": "similar-case-retrieval-v1",
                "corpus": "conveyancing-flagged-cases-only",
                "queries": str(TEST_QUERIES),
                "notes": (
                    "Queries are exam fact patterns from src/questions.md (see "
                    "build_test_set.py for selection rationale), not a labeled gold set."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
