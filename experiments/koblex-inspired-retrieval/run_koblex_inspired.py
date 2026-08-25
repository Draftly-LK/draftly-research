"""B1: LLM query generation -> BM25 -> LLM selection -> grounded answer.

Pipeline per question:

    background + question
        -> LLM generates 1-3 information needs        (reasoning: low)
        -> BM25 for each generated query, plus the background+question query
        -> merge and deduplicate candidates
        -> LLM selects the necessary real provisions  (reasoning: low)
        -> LLM answers from the selected provisions   (reasoning: medium)

The generated information needs are retrieval hypotheses. They are written to
generated_queries.jsonl for inspection and used only to build BM25 queries. They
are never passed to the selection or answering stage, never treated as evidence
and never cited.

Makes paid OpenAI calls. Requires OPENAI_API_KEY. Does not read the gold file.

Usage:
    uv run python experiments/koblex-inspired-retrieval/run_koblex_inspired.py --limit 1
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_config as config  # noqa: E402
import corpus_index  # noqa: E402
from smoke_llm import SmokeTestLLM, ValidationFailure  # noqa: E402

VARIANT = "b1-koblex-inspired"


def run_pipeline(questions, index, llm, top_k: int, max_candidates: int):
    """Returns (queries, candidates, selections, answers, errors) trace lists."""
    queries, candidates_trace, selections, answers, errors = [], [], [], [], []

    for item in questions:
        qid = item["question_id"]
        background = item.get("background", "")
        question = item["question"]
        base_query = corpus_index.question_query_text(background, question)

        # -- stage 1: generated information needs ------------------------ #
        generated: list[str] = []
        try:
            stage = llm.generate_information_needs(background, question)
            needs = stage.parsed
            generated = needs.search_queries()
            queries.append({
                "question_id": qid,
                "information_needs": [n.model_dump() for n in needs.information_needs],
                "attempts": stage.attempts,
            })
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            errors.append({"question_id": qid, "stage": "query_generation",
                           "error": type(exc).__name__, "detail": str(exc)})
            queries.append({"question_id": qid, "information_needs": [],
                            "attempts": 0})

        # -- stage 2: retrieval over base + generated queries ------------ #
        result_sets = [("background+question", index.search(base_query, top_k))]
        for position, generated_query in enumerate(generated, start=1):
            result_sets.append(
                (f"need-{position}", index.search(generated_query, top_k)))
        candidates = corpus_index.merge_candidates(result_sets, max_candidates)

        candidates_trace.append({
            "question_id": qid,
            "base_query": base_query,
            "generated_queries": generated,
            "candidate_count": len(candidates),
            "candidates": [
                {
                    "merged_rank": c["merged_rank"],
                    "node_id": c["node_id"],
                    "citation": c.get("citation"),
                    "act_id": c.get("act_id"),
                    "act_title": c.get("act_title"),
                    "provision_label": c.get("provision_label"),
                    "heading": c.get("heading"),
                    "text": c.get("text"),
                    "hierarchy": c.get("hierarchy"),
                    "bm25_score": c["bm25_score"],
                    "found_by": c["found_by"],
                }
                for c in candidates
            ],
        })

        if not candidates:
            errors.append({"question_id": qid, "stage": "retrieval",
                           "error": "NoCandidates",
                           "detail": "BM25 returned no candidates"})
            continue

        # -- stage 3: provision selection -------------------------------- #
        try:
            stage = llm.select_provisions(background, question, candidates)
            selection = stage.parsed
        except ValidationFailure as exc:
            errors.append({"question_id": qid, "stage": exc.stage,
                           "error": "ValidationFailure", "detail": exc.detail,
                           "offending_node_ids": exc.offending})
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append({"question_id": qid, "stage": "provision_selection",
                           "error": type(exc).__name__, "detail": str(exc)})
            continue

        selections.append({
            "question_id": qid,
            "selected_node_ids": selection.selected_node_ids,
            "evidence_complete": selection.evidence_complete,
            "missing_evidence": selection.missing_evidence,
            "attempts": stage.attempts,
            "candidate_count": len(candidates),
        })

        by_id = {c["node_id"]: c for c in candidates}
        provisions = [by_id[nid] for nid in selection.selected_node_ids if nid in by_id]
        if not provisions:
            errors.append({"question_id": qid, "stage": "provision_selection",
                           "error": "EmptySelection",
                           "detail": "no provisions selected; nothing to answer from"})
            continue

        # -- stage 4: grounded answer ------------------------------------ #
        try:
            stage = llm.answer(background, question, provisions)
            grounded = stage.parsed
        except ValidationFailure as exc:
            errors.append({"question_id": qid, "stage": exc.stage,
                           "error": "ValidationFailure", "detail": exc.detail,
                           "offending_node_ids": exc.offending})
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append({"question_id": qid, "stage": "final_answer",
                           "error": type(exc).__name__, "detail": str(exc)})
            continue

        answers.append({
            "question_id": qid,
            "answerable": grounded.answerable,
            "answer": grounded.answer,
            "cited_node_ids": grounded.cited_node_ids,
            "missing_evidence": grounded.missing_evidence,
            "selected_node_ids": selection.selected_node_ids,
            "attempts": stage.attempts,
        })

    return queries, candidates_trace, selections, answers, errors


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

    config.load_dotenv_if_present()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. This command makes paid API calls; "
              "export a key first.", file=sys.stderr)
        return 1

    questions = config.load_jsonl(config.QUESTIONS_PATH)
    selected = questions[: args.limit] if args.limit else questions
    run_dir = config.resolve_run_dir(args.run_name, VARIANT)

    try:
        index = corpus_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    llm = SmokeTestLLM()
    with index:
        queries, candidates, selections, answers, errors = run_pipeline(
            selected, index, llm, args.top_k, args.max_candidates)
        corpus_count = index.count()

    config.write_jsonl(queries, run_dir / "generated_queries.jsonl")
    config.write_jsonl(candidates, run_dir / "retrieval_candidates.jsonl")
    config.write_jsonl(selections, run_dir / "provision_selections.jsonl")
    config.write_jsonl(answers, run_dir / "answers.jsonl")
    config.write_jsonl(errors, run_dir / "errors.jsonl")
    config.write_json(
        config.build_run_config(
            variant=VARIANT,
            top_k=args.top_k,
            max_candidates=args.max_candidates,
            corpus_count=corpus_count,
            question_count=len(selected),
            limit=args.limit,
            include_model=True,
        ),
        run_dir / "run_config.json",
    )

    print(f"questions   : {len(selected)}")
    print(f"selections  : {len(selections)}")
    print(f"answers     : {len(answers)}")
    print(f"errors      : {len(errors)}")
    print(f"run directory: {config.display_path(run_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
