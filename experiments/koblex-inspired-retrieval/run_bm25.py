"""B0 baseline: background + question -> BM25. No LLM, no API calls, free.

The retrieval query is the normalized concatenation of the background and the
question, never the question field alone.

Does not read the gold file.

Usage:
    uv run python experiments/koblex-inspired-retrieval/run_bm25.py --run-name smoke-b0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_config as config  # noqa: E402
import corpus_index  # noqa: E402

VARIANT = "b0-bm25"


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--run-name", dest="run_name", default=None)
    parser.add_argument("--top-k", dest="top_k", type=int, default=config.DEFAULT_TOP_K)
    parser.add_argument("--max-candidates", dest="max_candidates", type=int,
                        default=config.DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N questions.")
    parser.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    args = parser.parse_args()

    questions = config.load_jsonl(config.QUESTIONS_PATH)
    selected = questions[: args.limit] if args.limit else questions
    run_dir = config.resolve_run_dir(args.run_name, VARIANT)

    try:
        index = corpus_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    predictions = []
    with index:
        for item in selected:
            query_text = corpus_index.question_query_text(
                item.get("background", ""), item["question"])
            results = index.search(query_text, args.top_k)
            predictions.append({
                "question_id": item["question_id"],
                "query_text": query_text,
                "match_expression": corpus_index.match_expression(query_text),
                "retrieved": [
                    {
                        "rank": r["rank"],
                        "node_id": r["node_id"],
                        "citation": r.get("citation"),
                        "act_id": r.get("act_id"),
                        "act_title": r.get("act_title"),
                        "provision_label": r.get("provision_label"),
                        "heading": r.get("heading"),
                        "text": r.get("text"),
                        "hierarchy": r.get("hierarchy"),
                        "bm25_score": r["bm25_score"],
                    }
                    for r in results
                ],
            })
        corpus_count = index.count()

    config.write_jsonl(predictions, run_dir / "bm25_predictions.jsonl")
    config.write_json(
        config.build_run_config(
            variant=VARIANT,
            top_k=args.top_k,
            max_candidates=args.max_candidates,
            corpus_count=corpus_count,
            question_count=len(selected),
            limit=args.limit,
            include_model=False,
        ),
        run_dir / "run_config.json",
    )

    empty = sum(1 for p in predictions if not p["retrieved"])
    print(f"questions        : {len(predictions)}")
    print(f"top_k            : {args.top_k}")
    print(f"empty result sets: {empty}")
    print(f"run directory    : {config.display_path(run_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
