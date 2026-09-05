"""Run the 20-query similar-case-retrieval test set and write an eval run.

There is no similar-case gold set (no hand-labeled "case X is similar to
fact pattern Y" set exists for this corpus), so this does not compute IR
metrics like the statute engine's evaluation.py does. It runs
`find_similar()` over each of the 20 queries from `build_test_set.py` and
records outcome + hits; appropriateness grading is a separate, human/LLM
step (see RESULTS.md), not computed here.

`--variant` selects one of the architecture ablation configurations
documented in RESULTS.md, by setting case_retrieval's env-var toggles
before running:

    v1              baseline                            (all toggles off)
    v2              verified-only statute/topic bridge   (GRAPH_VERIFIED_ONLY)
    v3              IDF-weighted lexical corroboration   (LEXICAL_IDF)
    v4              v2 + v3 combined
    v1-rebaseline   baseline rerun after catchwords were added to the
                    index/lexical/dense channels unconditionally (see
                    corpus.py) -- v5/v6/v7 below are measured against this,
                    not the original v1, since the code underneath v1
                    changed
    v5              catchword-phrase case<->case edges   (CATCHWORD_EDGES)
    v6              fanout-discounted section edges      (GRAPH_FANOUT_WEIGHT)
    v7              catchword-derived statute links      (CATCHWORD_STATUTE_LINKS)
    v8              best-of v5/v6/v7 combined (only meaningful once those
                    are measured)

Usage:
    uv run python scripts/similar-case-retrieval/run_eval.py --variant v1
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_ALL_OFF = {
    "DRAFTLY_CASE_GRAPH_VERIFIED_ONLY": "0",
    "DRAFTLY_CASE_LEXICAL_IDF": "0",
    "DRAFTLY_CASE_GRAPH_FANOUT_WEIGHT": "0",
    "DRAFTLY_CASE_CATCHWORD_EDGES": "0",
    "DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS": "0",
}


def _toggles(**on: str) -> dict[str, str]:
    merged = dict(_ALL_OFF)
    merged.update(on)
    return merged


VARIANTS = {
    "v1": _toggles(),
    "v2": _toggles(DRAFTLY_CASE_GRAPH_VERIFIED_ONLY="1"),
    "v3": _toggles(DRAFTLY_CASE_LEXICAL_IDF="1"),
    "v4": _toggles(DRAFTLY_CASE_GRAPH_VERIFIED_ONLY="1", DRAFTLY_CASE_LEXICAL_IDF="1"),
    "v1-rebaseline": _toggles(),
    "v5": _toggles(DRAFTLY_CASE_CATCHWORD_EDGES="1"),
    "v6": _toggles(DRAFTLY_CASE_GRAPH_FANOUT_WEIGHT="1"),
    "v7": _toggles(DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS="1"),
    "v8": _toggles(
        DRAFTLY_CASE_CATCHWORD_EDGES="1", DRAFTLY_CASE_GRAPH_FANOUT_WEIGHT="1", DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS="1"
    ),
}

SCRIPT_DIR = Path(__file__).resolve().parent
TEST_QUERIES = SCRIPT_DIR / "test_queries.jsonl"
RUNS_DIR = Path(__file__).resolve().parents[2] / "evaluation" / "runs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="v1")
    args = parser.parse_args()
    os.environ.update(VARIANTS[args.variant])

    # Imported after the env vars are set: build_index()/find_similar() read
    # the toggles lazily on each call, but importing after setting them here
    # keeps this script's behavior obviously correct even if that changes.
    from draftly.case_retrieval.index import build_index
    from draftly.case_retrieval.models import CaseQuery
    from draftly.case_retrieval.search import find_similar

    output_dir = RUNS_DIR / f"similar-case-retrieval-{args.variant}"

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

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "predictions.csv", predictions)

    metrics = {
        "variant": args.variant,
        "variant_toggles": VARIANTS[args.variant],
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
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "config.json").write_text(
        json.dumps(
            {
                "run_id": f"similar-case-retrieval-{args.variant}",
                "corpus": "conveyancing-flagged-cases-only",
                "queries": str(TEST_QUERIES),
                "variant_toggles": VARIANTS[args.variant],
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
