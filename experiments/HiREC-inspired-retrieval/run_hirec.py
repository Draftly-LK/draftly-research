"""HiREC: hierarchical retrieval with iterative evidence curation.

Ported from paper-implementations/LOFin-bench-HiREC (the finrag_api per-query
loop, which is the clean reference; the batch implementation has a hardcoded
10-row dataset slice and an evidence-replacement line dedented out of its loop).

Per question:

    background + question
        -> acts selected (derived from the seed hits, or by LLM)
        -> BM25 seeds, scoped to those acts
        -> each seed expanded to its whole section subtree      (the pool)
        -> LLM curates in ONE call: which provisions are needed,
           whether anything is missing, and what to search next  (medium)
        -> complete?  yes -> answer
                      no  -> LLM rewrites the gap as a query     (low)
                             re-retrieve, merge, curate again
        -> LLM answers from the curated provisions only          (medium)

Faithful to HiREC: the original question is never mutated and is what the
curator and the answering stage always see; the refined query drives retrieval
only and is never evidence; accumulated evidence is re-filtered each iteration
rather than frozen; the saturation hatch treats a maximal relevant set as
complete; and exhausting the iteration budget appends one uncurated last-resort
retrieval and answers anyway rather than failing.

The refined queries are retrieval hypotheses. They are written to
refined_queries.jsonl for inspection and used only to build BM25 queries. They
are never passed to the curation or answering stage, never treated as evidence
and never cited.

Makes paid OpenAI calls. Requires OPENAI_API_KEY. Does not read the gold file.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/run_hirec.py --dry-run
    uv run python experiments/HiREC-inspired-retrieval/run_hirec.py --limit 1
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402
import hirec_hierarchy as hierarchy  # noqa: E402
import hirec_index  # noqa: E402
import hirec_schemas as schemas  # noqa: E402
from hirec_llm import HirecLLM, ValidationFailure  # noqa: E402

VARIANT = "hirec"

STOPPED_COMPLETE = "complete"
STOPPED_SATURATION = "saturation_hatch"
STOPPED_BUDGET = "budget_exhausted"


class Trace:
    """The per-run artifact lists, written out whatever happens."""

    def __init__(self):
        self.acts = []
        self.pools = []
        self.curations = []
        self.refined_queries = []
        self.answers = []
        self.errors = []

    def error(self, question_id: str, stage: str, exc: Exception,
              **extra) -> None:
        record = {"question_id": question_id, "stage": stage,
                  "error": type(exc).__name__, "detail": str(exc)}
        if isinstance(exc, ValidationFailure):
            record["error"] = "ValidationFailure"
            record["detail"] = exc.detail
            record["offending_ids"] = exc.offending
        record.update(extra)
        self.errors.append(record)


# --------------------------------------------------------------------------- #
# act selection
# --------------------------------------------------------------------------- #

def select_acts(index, llm, item, base_query, args, trace) -> list[str]:
    """The document stage of the hierarchy. Returns the act_ids to search.

    `derived` is the default and costs nothing: the acts are those of the
    unscoped BM25 seed hits. HiREC's document retriever exists to make an
    intractable corpus tractable -- thousands of filings whose PDFs cost money
    to open -- whereas this corpus is one SQLite file that BM25 sweeps in
    milliseconds. An act filter here can only remove candidates, never add them,
    so the free variant is also the safe one.
    """
    qid = item["question_id"]
    if args.act_selector == "derived":
        hits = index.search(base_query, args.seed_top_k)
        act_ids = list(dict.fromkeys(
            h["act_id"] for h in hits if h.get("act_id")))[: args.max_acts]
        trace.acts.append({"question_id": qid, "selector": "derived",
                           "selected_act_ids": act_ids, "reasoning": None,
                           "attempts": 0})
        return act_ids

    acts = index.acts()
    try:
        stage = llm.select_acts(item.get("background", ""), item["question"],
                               acts, args.max_acts)
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        trace.error(qid, "act_selection", exc)
        trace.acts.append({"question_id": qid, "selector": args.act_selector,
                           "selected_act_ids": [], "reasoning": None,
                           "attempts": 0})
        # An act stage that fails must not silently narrow the search: fall back
        # to the whole corpus rather than to nothing.
        return []
    act_ids = stage.parsed.selected_act_ids[: args.max_acts]
    trace.acts.append({"question_id": qid, "selector": args.act_selector,
                       "selected_act_ids": act_ids,
                       "reasoning": stage.parsed.reasoning,
                       "attempts": stage.attempts})
    return act_ids


# --------------------------------------------------------------------------- #
# retrieval
# --------------------------------------------------------------------------- #

def retrieve_pool(index, query_text, act_ids, args) -> tuple[hierarchy.Pool, list]:
    hits = index.search(query_text, args.seed_top_k, act_ids=act_ids or None)
    if not args.expand:
        return hierarchy.Pool(
            records=hits,
            seed_node_ids=[h["node_id"] for h in hits],
            section_ids=index.section_ids_for([h["node_id"] for h in hits]),
            section_rank={h.get("section_id"): i
                          for i, h in enumerate(hits, start=1)},
            char_count=sum(hierarchy.record_chars(h) for h in hits)), hits
    pool = hierarchy.section_pool(
        index, hits, max_records=args.max_pool_records,
        max_chars=args.max_pool_chars)
    return pool, hits


def pool_trace(qid, iteration, query_text, pool, hits, act_ids, label) -> dict:
    return {
        "question_id": qid,
        "iteration": iteration,
        "label": label,
        "query_text": query_text,
        "act_ids": list(act_ids),
        "seed_node_ids": [h["node_id"] for h in hits],
        "section_ids": pool.section_ids,
        "pool_size": len(pool.records),
        "pool_chars": pool.char_count,
        "truncated": pool.truncated,
        "dropped_section_ids": pool.dropped_section_ids,
        "pool": [
            {"pool_rank": rank, "node_id": r["node_id"],
             "citation": r.get("citation"), "act_id": r.get("act_id"),
             "section_id": r.get("section_id"), "node_type": r.get("node_type"),
             "heading": r.get("heading"), "text": r.get("text")}
            for rank, r in enumerate(pool.records, start=1)
        ],
    }


# --------------------------------------------------------------------------- #
# the loop
# --------------------------------------------------------------------------- #

def run_question(item, index, llm, args, trace) -> None:
    qid = item["question_id"]
    background = item.get("background", "")
    original_question = item["question"]          # never mutated
    base_query = hirec_index.question_query_text(background, original_question)

    act_ids = select_acts(index, llm, item, base_query, args, trace)

    retrieval_query = base_query                  # what drives retrieval
    tried_queries: list[str] = []
    carried = hierarchy.Pool(records=[])          # curated evidence so far
    stopped_by = None
    iterations_run = 0
    last_missing: list[str] = []

    for iteration in range(1, args.max_iterations + 1):
        iterations_run = iteration

        new_pool, hits = retrieve_pool(index, retrieval_query, act_ids, args)
        pool = hierarchy.merge_pools(
            carried, new_pool,
            max_records=args.max_pool_records, max_chars=args.max_pool_chars)
        trace.pools.append(pool_trace(
            qid, iteration, retrieval_query, pool, hits, act_ids, "merged"))

        if not pool.records:
            trace.error(qid, "retrieval",
                        RuntimeError("BM25 returned no candidates"),
                        iteration=iteration)
            return

        try:
            stage = llm.curate_evidence(
                background, original_question, pool, iteration)
        except Exception as exc:  # noqa: BLE001
            trace.error(qid, "evidence_curation", exc, iteration=iteration)
            return
        curation = stage.parsed

        by_id = pool.by_id()
        relevant = [by_id[n] for n in curation.relevant_node_ids if n in by_id]

        derived = schemas.derive_completeness(curation)
        xref = []
        if args.xref_precheck:
            xref = hierarchy.unresolved_references(relevant, pool)
            if xref:
                derived = False

        gate = (curation.model_claimed_complete if args.gate_on == "model"
                else derived)
        evidence_complete, forced = schemas.apply_saturation_hatch(
            gate, curation.relevant_node_ids, args.max_relevant_ids)

        # HiREC re-filters rather than freezes: the curated set replaces the
        # carried set, so a provision kept last iteration can be dropped this
        # one. --freeze-evidence keeps it instead, which is measurable here
        # (gold_lost) in a way it is not in HiREC's setting.
        if args.freeze_evidence:
            retained = list({r["node_id"]: r for r in
                             list(carried.records) + relevant}.values())
        else:
            retained = relevant
        carried = hierarchy.carried_pool(retained)

        trace.curations.append({
            "question_id": qid,
            "iteration": iteration,
            "pool_size": len(pool.records),
            "relevant_node_ids": list(curation.relevant_node_ids),
            "retained_node_ids": [r["node_id"] for r in retained],
            "model_claimed_complete": curation.model_claimed_complete,
            "derived_complete": derived,
            "evidence_complete": evidence_complete,
            "forced_answerable": forced,
            "gate_on": args.gate_on,
            "sub_questions": [s.model_dump() for s in curation.sub_questions],
            "unresolved_cross_references": list(
                curation.unresolved_cross_references),
            "xref_precheck_findings": xref,
            "sibling_accounting": curation.sibling_accounting,
            "missing_evidence": list(curation.missing_evidence),
            "refined_query": curation.refined_query,
            "attempts": stage.attempts,
        })

        last_missing = list(curation.missing_evidence)

        if evidence_complete:
            stopped_by = STOPPED_SATURATION if forced else STOPPED_COMPLETE
            break

        if iteration == args.max_iterations:
            # Budget exhausted. HiREC appends one uncurated last-resort
            # retrieval and answers anyway; so does this.
            stopped_by = STOPPED_BUDGET
            last_pool, last_hits = retrieve_pool(
                index, curation.refined_query or retrieval_query, act_ids, args)
            trace.pools.append(pool_trace(
                qid, iteration, curation.refined_query or retrieval_query,
                last_pool, last_hits, act_ids, "last_resort_retrieval"))
            carried = hierarchy.merge_pools(
                carried, last_pool,
                max_records=args.max_relevant_ids,
                max_chars=args.max_pool_chars)
            break

        # Refine: rewrite the gap into a retrieval query. The refined query
        # replaces the retrieval query and never touches any other prompt.
        try:
            rewrite = llm.transform_query(
                background, original_question, curation.missing_evidence,
                tried_queries)
            refined = rewrite.parsed.search_query
            targets = rewrite.parsed.targets
            attempts = rewrite.attempts
        except Exception as exc:  # noqa: BLE001 - fall back to the curator's own
            trace.error(qid, "query_transform", exc, iteration=iteration)
            refined = curation.refined_query
            targets = None
            attempts = 0

        trace.refined_queries.append({
            "question_id": qid, "iteration": iteration,
            "curator_refined_query": curation.refined_query,
            "rewritten_query": refined, "targets": targets,
            "missing_evidence": list(curation.missing_evidence),
            "attempts": attempts,
        })
        tried_queries.append(refined)
        retrieval_query = refined or retrieval_query

    provisions = list(carried.records)
    if not provisions:
        trace.error(qid, "evidence_curation",
                    RuntimeError("no provisions curated; nothing to answer from"),
                    iteration=iterations_run)
        return

    try:
        stage = llm.answer(background, original_question, provisions)
    except Exception as exc:  # noqa: BLE001
        trace.error(qid, "final_answer", exc, iteration=iterations_run)
        return
    grounded = stage.parsed

    trace.answers.append({
        "question_id": qid,
        "answerable": grounded.answerable,
        "answer": grounded.answer,
        "cited_node_ids": grounded.cited_node_ids,
        "missing_evidence": grounded.missing_evidence,
        "curated_node_ids": [p["node_id"] for p in provisions],
        "iterations": iterations_run,
        "stopped_by": stopped_by,
        "unmet_evidence_at_stop": last_missing if stopped_by == STOPPED_BUDGET else [],
        "attempts": stage.attempts,
    })


# --------------------------------------------------------------------------- #
# usage
# --------------------------------------------------------------------------- #

def summarize_usage(calls: list[dict], wall_elapsed: float,
                    questions: int) -> dict:
    """Latency and cost, from measured per-call records.

    Wall clock is reported alongside the sum of call latencies because they are
    different numbers and the difference is informative: the gap is time spent
    in BM25, pooling and rendering rather than waiting on the API.
    """
    def total(field: str) -> int | None:
        values = [c[field] for c in calls if c.get(field) is not None]
        return sum(values) if values else None

    input_tokens, output_tokens = total("input_tokens"), total("output_tokens")
    by_stage: dict[str, dict] = {}
    for call in calls:
        block = by_stage.setdefault(call["stage"], {
            "calls": 0, "elapsed_s": 0.0, "input_tokens": 0, "output_tokens": 0})
        block["calls"] += 1
        block["elapsed_s"] = round(block["elapsed_s"] + call["elapsed_s"], 3)
        for field in ("input_tokens", "output_tokens"):
            if call.get(field) is not None:
                block[field] += call[field]

    latencies = sorted(c["elapsed_s"] for c in calls)
    return {
        "questions": questions,
        "api_calls": len(calls),
        "failed_calls": sum(1 for c in calls if c.get("error")),
        "wall_clock_s": wall_elapsed,
        "api_time_s": round(sum(latencies), 3),
        "mean_latency_s_per_call": (round(sum(latencies) / len(latencies), 3)
                                    if latencies else None),
        "p95_latency_s_per_call": (latencies[int(0.95 * (len(latencies) - 1))]
                                   if latencies else None),
        "max_latency_s_per_call": latencies[-1] if latencies else None,
        "mean_latency_s_per_question": (round(wall_elapsed / questions, 3)
                                        if questions else None),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": total("reasoning_tokens"),
        "cost_usd": config.cost_usd(input_tokens, output_tokens),
        "cost_usd_per_question": (
            round(config.cost_usd(input_tokens, output_tokens) / questions, 6)
            if questions and config.cost_usd(input_tokens, output_tokens)
            is not None else None),
        "rates_usd_per_million": dict(config.TOKEN_RATES_USD_PER_MILLION),
        "rates_source": config.TOKEN_RATES_SOURCE,
        "by_stage": by_stage,
    }


# --------------------------------------------------------------------------- #
# dry run
# --------------------------------------------------------------------------- #

def dry_run(questions, index, args) -> int:
    """Render every first-iteration prompt and cost it. Makes no calls."""
    total_chars = 0
    per_question = []
    for item in questions:
        base_query = hirec_index.question_query_text(
            item.get("background", ""), item["question"])
        hits = index.search(base_query, args.seed_top_k)
        act_ids = list(dict.fromkeys(
            h["act_id"] for h in hits if h.get("act_id")))[: args.max_acts]
        pool, _ = retrieve_pool(index, base_query, act_ids, args)
        curation_prompt = config.prompt_text("evidence_curation").format(
            background=item.get("background", "") or "(none)",
            question=item["question"],
            pool=hierarchy.render_pool(pool),
            iteration=1)
        chars = len(curation_prompt)
        total_chars += chars
        per_question.append((item["question_id"], len(pool.records), chars))

    print(f"questions            : {len(questions)}")
    print(f"seed_top_k           : {args.seed_top_k}")
    print(f"max_iterations       : {args.max_iterations}")
    print("curation prompt, iteration 1 only:")
    print(f"  mean pool records  : "
          f"{round(sum(p for _, p, _ in per_question) / max(len(per_question), 1))}")
    print(f"  max pool records   : {max((p for _, p, _ in per_question), default=0)}")
    print(f"  mean chars         : "
          f"{round(total_chars / max(len(per_question), 1))}")
    print(f"  max chars          : {max((c for _, _, c in per_question), default=0)}")
    print(f"  approx input tokens: {round(total_chars / 4)} total, "
          f"{round(total_chars / 4 / max(len(per_question), 1))} per question")
    print("worst case over all iterations (every question runs the full budget):")
    print(f"  approx input tokens: "
          f"{round(total_chars / 4 * args.max_iterations)} for curation, plus "
          f"one answer call per question")
    print("no API calls were made")
    return 0


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--run-name", dest="run_name", default=None)
    parser.add_argument("--seed-top-k", dest="seed_top_k", type=int,
                        default=config.DEFAULT_SEED_TOP_K)
    parser.add_argument("--max-iterations", dest="max_iterations", type=int,
                        default=config.DEFAULT_MAX_ITERATIONS)
    parser.add_argument("--max-relevant-ids", dest="max_relevant_ids", type=int,
                        default=config.DEFAULT_MAX_RELEVANT_IDS)
    parser.add_argument("--max-acts", dest="max_acts", type=int,
                        default=config.DEFAULT_MAX_ACTS)
    parser.add_argument("--max-pool-records", dest="max_pool_records", type=int,
                        default=config.DEFAULT_MAX_POOL_RECORDS)
    parser.add_argument("--max-pool-chars", dest="max_pool_chars", type=int,
                        default=config.DEFAULT_MAX_POOL_CHARS)
    parser.add_argument("--act-selector", dest="act_selector",
                        choices=("derived", "llm"), default="derived")
    parser.add_argument("--gate-on", dest="gate_on",
                        choices=("derived", "model"), default="derived",
                        help="Which completeness signal the loop gates on.")
    parser.add_argument("--curation-effort", dest="curation_effort",
                        choices=("low", "medium", "high"), default=None)
    parser.add_argument("--no-section-expansion", dest="expand",
                        action="store_false",
                        help="Ablation: pool is the flat BM25 hit list.")
    parser.add_argument("--negative-prior", dest="negative_prior",
                        action="store_true",
                        help="Tell the curator to assume incompleteness. Off by "
                             "default: it manufactures false incompletes.")
    parser.add_argument("--xref-precheck", dest="xref_precheck",
                        action="store_true",
                        help="Force incompleteness on unresolved statutory "
                             "cross-references. Not HiREC.")
    parser.add_argument("--freeze-evidence", dest="freeze_evidence",
                        action="store_true",
                        help="Never drop curated evidence. HiREC re-filters.")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",
                        help="Render and cost the prompts, make no calls.")
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

    try:
        index = hirec_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.dry_run:
        with index:
            return dry_run(selected, index, args)

    config.load_dotenv_if_present()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. This command makes paid API calls; "
              "export a key first.", file=sys.stderr)
        index.close()
        return 1

    run_dir = config.resolve_run_dir(args.run_name, VARIANT)
    llm = HirecLLM(curation_effort=args.curation_effort,
                   negative_prior=args.negative_prior)
    trace = Trace()

    wall_started = time.perf_counter()
    with index:
        for item in selected:
            llm.for_question(item["question_id"])
            run_question(item, index, llm, args, trace)
        corpus_count = index.count()
    wall_elapsed = round(time.perf_counter() - wall_started, 3)

    config.write_jsonl(trace.acts, run_dir / "act_selections.jsonl")
    config.write_jsonl(trace.pools, run_dir / "retrieval_pools.jsonl")
    config.write_jsonl(trace.curations, run_dir / "curations.jsonl")
    config.write_jsonl(trace.refined_queries, run_dir / "refined_queries.jsonl")
    config.write_jsonl(trace.answers, run_dir / "answers.jsonl")
    config.write_jsonl(trace.errors, run_dir / "errors.jsonl")
    config.write_jsonl(llm.calls, run_dir / "usage.jsonl")
    config.write_json(summarize_usage(llm.calls, wall_elapsed, len(selected)),
                      run_dir / "usage_summary.json")
    config.write_json(
        config.build_run_config(
            variant=VARIANT,
            corpus_count=corpus_count,
            question_count=len(selected),
            limit=args.limit,
            questions_path=args.questions,
            include_model=True,
            extra={
                "seed_top_k": args.seed_top_k,
                "max_iterations": args.max_iterations,
                "max_relevant_ids": args.max_relevant_ids,
                "max_acts": args.max_acts,
                "max_pool_records": args.max_pool_records,
                "max_pool_chars": args.max_pool_chars,
                "act_selector": args.act_selector,
                "gate_on": args.gate_on,
                "section_expansion": args.expand,
                "curation_effort": (args.curation_effort
                                    or config.REASONING_EFFORT["evidence_curation"]),
                "negative_prior": args.negative_prior,
                "xref_precheck": args.xref_precheck,
                "freeze_evidence": args.freeze_evidence,
                "hirec_fidelity": config.fidelity_ledger(
                    negative_prior=args.negative_prior,
                    xref_precheck=args.xref_precheck,
                    freeze_evidence=args.freeze_evidence,
                    gate_on=args.gate_on,
                    act_selector=args.act_selector),
            },
        ),
        run_dir / "run_config.json",
    )

    stops = {}
    for answer in trace.answers:
        stops[answer["stopped_by"]] = stops.get(answer["stopped_by"], 0) + 1
    iters = [a["iterations"] for a in trace.answers] or [0]
    print(f"questions    : {len(selected)}")
    print(f"answers      : {len(trace.answers)}")
    print(f"curations    : {len(trace.curations)}")
    print(f"mean iters   : {round(sum(iters) / len(iters), 2)}")
    print(f"stopped by   : {stops}")
    print(f"errors       : {len(trace.errors)}")
    usage = summarize_usage(llm.calls, wall_elapsed, len(selected))
    print(f"api calls    : {usage['api_calls']}")
    print(f"tokens       : {usage['input_tokens']} in / "
          f"{usage['output_tokens']} out")
    print(f"latency      : {usage['wall_clock_s']}s wall, "
          f"{usage['mean_latency_s_per_question']}s per question")
    print(f"cost         : ${usage['cost_usd']} "
          f"(rates unverified -- see usage_summary.json)")
    print(f"run directory: {config.display_path(run_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
