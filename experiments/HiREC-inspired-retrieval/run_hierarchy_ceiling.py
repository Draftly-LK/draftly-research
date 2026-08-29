"""R0 baseline: background + question -> BM25 -> section-subtree expansion.

No LLM, no API calls, free. This is the retrieval ceiling: every provision the
curation stages could possibly choose is in the pool this run writes, so no
downstream run's complete-evidence figure can exceed this one's.

Worth running at several seed values, since it costs nothing. Measured over the
20 smoke questions: K=5 puts the complete gold evidence in the pool for 16
questions, K=10 for 18, K=20 for all 20.

The retrieval query is the normalized concatenation of the background and the
question, never the question field alone.

Does not read the gold file.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py \
        --run-name smoke-r0-k20 --seed-top-k 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402
import hirec_hierarchy as hierarchy  # noqa: E402
import hirec_index  # noqa: E402

VARIANT = "r0-hierarchy-ceiling"


def pool_record(item: dict, query_text: str, pool: hierarchy.Pool,
                seed_hits: list[dict]) -> dict:
    return {
        "question_id": item["question_id"],
        "query_text": query_text,
        "match_expression": hirec_index.match_expression(query_text),
        "seed": [
            {"rank": h["rank"], "node_id": h["node_id"],
             "section_id": h.get("section_id"), "act_id": h.get("act_id"),
             "bm25_score": h["bm25_score"]}
            for h in seed_hits
        ],
        "act_ids": sorted({h.get("act_id") for h in seed_hits if h.get("act_id")}),
        "section_ids": pool.section_ids,
        "pool_size": len(pool.records),
        "pool_chars": pool.char_count,
        "truncated": pool.truncated,
        "dropped_section_ids": pool.dropped_section_ids,
        "pool": [
            {
                "pool_rank": rank,
                "node_id": r["node_id"],
                "citation": r.get("citation"),
                "act_id": r.get("act_id"),
                "act_title": r.get("act_title"),
                "section_id": r.get("section_id"),
                "node_type": r.get("node_type"),
                "provision_label": r.get("provision_label"),
                "heading": r.get("heading"),
                "text": r.get("text"),
                "hierarchy": r.get("hierarchy"),
                "seeded": r["node_id"] in set(pool.seed_node_ids),
            }
            for rank, r in enumerate(pool.records, start=1)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--run-name", dest="run_name", default=None)
    parser.add_argument("--seed-top-k", dest="seed_top_k", type=int,
                        default=config.DEFAULT_SEED_TOP_K)
    parser.add_argument("--max-pool-records", dest="max_pool_records", type=int,
                        default=config.DEFAULT_MAX_POOL_RECORDS)
    parser.add_argument("--max-pool-chars", dest="max_pool_chars", type=int,
                        default=config.DEFAULT_MAX_POOL_CHARS)
    parser.add_argument("--no-section-expansion", dest="expand",
                        action="store_false",
                        help="Skip expansion; pool is the flat BM25 hit list.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N questions.")
    parser.add_argument("--questions", type=Path,
                        default=config.QUESTIONS_PATH,
                        help="Question set to run. Defaults to the smoke set; "
                             "point it at a past-paper set to evaluate that.")
    parser.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    args = parser.parse_args()

    questions = config.load_jsonl(args.questions)
    selected = questions[: args.limit] if args.limit else questions
    run_dir = config.resolve_run_dir(args.run_name, VARIANT)

    try:
        index = hirec_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    records = []
    with index:
        for item in selected:
            query_text = hirec_index.question_query_text(
                item.get("background", ""), item["question"])
            hits = index.search(query_text, args.seed_top_k)
            if args.expand:
                pool = hierarchy.section_pool(
                    index, hits,
                    max_records=args.max_pool_records,
                    max_chars=args.max_pool_chars)
            else:
                pool = hierarchy.Pool(
                    records=hits,
                    seed_node_ids=[h["node_id"] for h in hits],
                    section_ids=index.section_ids_for([h["node_id"] for h in hits]),
                    section_rank={},
                    char_count=sum(hierarchy.record_chars(h) for h in hits))
            records.append(pool_record(item, query_text, pool, hits))
        corpus_count = index.count()

    config.write_jsonl(records, run_dir / "hierarchy_pool.jsonl")
    config.write_json(
        config.build_run_config(
            variant=VARIANT,
            corpus_count=corpus_count,
            question_count=len(selected),
            limit=args.limit,
            questions_path=args.questions,
            include_model=False,
            extra={
                "seed_top_k": args.seed_top_k,
                "section_expansion": args.expand,
                "max_pool_records": args.max_pool_records,
                "max_pool_chars": args.max_pool_chars,
            },
        ),
        run_dir / "run_config.json",
    )

    sizes = [r["pool_size"] for r in records] or [0]
    print(f"questions     : {len(records)}")
    print(f"seed_top_k    : {args.seed_top_k}")
    print(f"expansion     : {'section subtree' if args.expand else 'off'}")
    print(f"mean pool size: {round(sum(sizes) / len(sizes))}")
    print(f"max pool size : {max(sizes)}")
    print(f"truncated     : {sum(1 for r in records if r['truncated'])}")
    print(f"run directory : {config.display_path(run_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
