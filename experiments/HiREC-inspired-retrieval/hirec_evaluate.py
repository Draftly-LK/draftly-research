"""Score a run against the gold file. The only module that reads gold.

Metric families, because the outputs have different shapes:

  Ranked pools -- the section-expanded candidate pool is genuinely ordered
  (sections by best seed rank, then document order within a section), so
  rank-aware metrics apply. Cutoffs go to 200 rather than 20 because the pool is
  a different-sized object from a flat top-20 hit list; the two recall@k numbers
  are not comparable to each other.

  Curated provisions -- an unordered set. No rank-aware metric is reported and
  the selection is NOT re-ranked by its earlier pool positions, which would
  invent an ordering the model never produced.

  Answerability calibration -- the confusion matrix of the model's completeness
  claim against whether the evidence really was complete. This is the block the
  variant exists to produce: the comparable koblex b1 run claimed complete on all
  20 questions, so its false-complete rate was 1.0 and its loop, had it had one,
  would never have fired.

Matching is exact on node_id, which is correct here because the gold is authored
at the corpus's own granularity.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py \
        --run-name smoke-r0-k20
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402

GOLD_PATH = config.SHARED_DATA_DIR / "smoke_test_20_gold.jsonl"
RECALL_CUTOFFS = (5, 10, 20)
RECALL_CUTOFFS_POOL = (20, 50, 100, 200)

# The comparable koblex baseline, for the calibration block.
KOBLEX_RUNS_DIR = config.SHARED_DATA_DIR.parent / "runs"


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


# --------------------------------------------------------------------------- #
# ranked retrieval
# --------------------------------------------------------------------------- #

def score_ranked(ranked: dict[str, list[str]], gold: dict[str, set[str]],
                 cutoffs: tuple[int, ...] = RECALL_CUTOFFS) -> dict:
    """Recall@k and MRR over genuinely ranked lists."""
    per_question = {}
    for qid, gold_ids in gold.items():
        if qid not in ranked:
            continue
        # A question with no gold provisions has no rank-aware metric: recall
        # has a zero denominator and MRR has nothing to find. Skipping is right
        # rather than scoring 0 or 1, both of which would be a made-up number
        # averaged into the headline. These questions are scored separately by
        # score_absent_evidence.
        if not gold_ids:
            continue
        order = ranked[qid]
        entry: dict = {"retrieved": len(order), "gold": len(gold_ids)}
        for cutoff in cutoffs:
            hit = len(gold_ids & set(order[:cutoff]))
            entry[f"recall@{cutoff}"] = round(hit / len(gold_ids), 4)
        first = next((i for i, nid in enumerate(order, start=1) if nid in gold_ids), None)
        entry["reciprocal_rank"] = round(1 / first, 4) if first else 0.0
        entry["complete_in_candidates"] = gold_ids.issubset(set(order))
        per_question[qid] = entry

    if not per_question:
        return {}
    summary = {
        f"recall@{k}": _mean([e[f"recall@{k}"] for e in per_question.values()])
        for k in cutoffs
    }
    summary["mrr"] = _mean([e["reciprocal_rank"] for e in per_question.values()])
    summary["complete_evidence_in_candidates"] = _mean(
        [float(e["complete_in_candidates"]) for e in per_question.values()])
    summary["questions"] = len(per_question)
    return {"summary": summary, "per_question": per_question}


# --------------------------------------------------------------------------- #
# set-valued selection
# --------------------------------------------------------------------------- #

def score_sets(selected: dict[str, set[str]], gold: dict[str, set[str]],
               label: str) -> dict:
    """Precision / recall / F1 / completeness / exact-set for unordered sets."""
    per_question = {}
    for qid, gold_ids in gold.items():
        if qid not in selected:
            continue
        # As in score_ranked: precision, recall and F1 are not defined against an
        # empty gold set. Scored by score_absent_evidence instead.
        if not gold_ids:
            continue
        chosen = selected[qid]
        hit = len(chosen & gold_ids)
        precision = hit / len(chosen) if chosen else 0.0
        recall = hit / len(gold_ids) if gold_ids else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0.0)
        per_question[qid] = {
            f"{label}_count": len(chosen),
            "gold": len(gold_ids),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "complete_evidence": gold_ids.issubset(chosen),
            "exact_set": chosen == gold_ids,
        }

    if not per_question:
        return {}
    summary = {
        "precision": _mean([e["precision"] for e in per_question.values()]),
        "recall": _mean([e["recall"] for e in per_question.values()]),
        "f1": _mean([e["f1"] for e in per_question.values()]),
        "complete_evidence_accuracy": _mean(
            [float(e["complete_evidence"]) for e in per_question.values()]),
        "exact_set_accuracy": _mean(
            [float(e["exact_set"]) for e in per_question.values()]),
        "questions": len(per_question),
    }
    return {"summary": summary, "per_question": per_question}


def group_by(per_question: dict, gold_meta: dict, key: str,
             metrics: list[str]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for qid, entry in per_question.items():
        grouped[str(gold_meta[qid][key])].append(entry)
    out = {}
    for value, entries in sorted(grouped.items()):
        block = {"questions": len(entries)}
        for metric in metrics:
            values = [e[metric] for e in entries if metric in e]
            if values:
                block[metric] = _mean([float(v) for v in values])
        out[value] = block
    return out


# --------------------------------------------------------------------------- #
# act selection
# --------------------------------------------------------------------------- #

def score_act_selection(selections: dict[str, list[str]],
                        gold: dict[str, set[str]],
                        seed_acts: dict[str, set[str]] | None = None) -> dict:
    """Act-level recall, and what the act filter cost.

    node_id is prefixed by act_id, so the gold act set is recoverable without
    any extra annotation. gold_provisions_excluded_by_act_filter is the decision
    metric: gold that an unscoped search would have been free to surface but the
    filter removed. Non-zero means the selector is net-harmful.
    """
    per_question = {}
    excluded_total = 0
    for qid, gold_ids in gold.items():
        if qid not in selections:
            continue
        # No gold provisions means no gold Acts, so act recall has a zero
        # denominator. Scoring it 0.0 would drag the mean down for a question
        # that had nothing to find in the first place.
        if not gold_ids:
            continue
        chosen = list(selections[qid])
        chosen_set = set(chosen)
        gold_acts = {nid.split("/")[0] for nid in gold_ids}
        lost = sorted(nid for nid in gold_ids
                      if nid.split("/")[0] not in chosen_set)
        # Only count as "excluded by the filter" what the unscoped seed could
        # have reached in the first place.
        if seed_acts is not None:
            reachable = seed_acts.get(qid, set())
            lost = [nid for nid in lost if nid.split("/")[0] in reachable]
        excluded_total += len(lost)
        hit = len(gold_acts & chosen_set)
        per_question[qid] = {
            "gold_acts": sorted(gold_acts),
            "selected_acts": chosen,
            "act_recall": round(hit / len(gold_acts), 4) if gold_acts else 0.0,
            "act_precision": round(hit / len(chosen), 4) if chosen else 0.0,
            "act_set_complete": gold_acts.issubset(chosen_set),
            "gold_provisions_lost": lost,
        }

    if not per_question:
        return {}
    return {
        "summary": {
            "act_recall": _mean([e["act_recall"] for e in per_question.values()]),
            "act_precision": _mean(
                [e["act_precision"] for e in per_question.values()]),
            "act_set_complete": _mean(
                [float(e["act_set_complete"]) for e in per_question.values()]),
            "mean_acts_selected": _mean(
                [float(len(e["selected_acts"])) for e in per_question.values()]),
            "gold_provisions_excluded_by_act_filter": excluded_total,
            "questions": len(per_question),
        },
        "note": (
            "Most of these questions cite a single Act, so act recall saturates "
            "and discriminates poorly between selectors. "
            "gold_provisions_excluded_by_act_filter is the number that matters: "
            "any value above zero means the act stage is losing evidence the "
            "unscoped search would have reached."),
        "per_question": per_question,
    }


# --------------------------------------------------------------------------- #
# calibration
# --------------------------------------------------------------------------- #

def score_calibration(claims: dict[str, tuple[bool, set[str]]],
                      gold: dict[str, set[str]],
                      absent: set[str] | None = None) -> dict:
    """Confusion matrix of a completeness claim against whether it was true.

    `claims[qid]` is (claimed_complete, ids_the_claim_was_about). Ground truth is
    `gold_ids <= ids`.

    `absent` names the questions whose evidence is not in the corpus at all. They
    need explicit handling rather than falling out of the subset test, because an
    empty gold set is a subset of everything: left alone they would score as
    "evidence was complete" on every run, which is the exact opposite of the
    truth and would quietly destroy the measurement these questions exist to
    make possible. For them the evidence can never be complete, so `actual` is
    False by construction.
    """
    absent = absent or set()
    tp = fp = fn = tn = 0
    per_question = {}
    for qid, (claimed, ids) in claims.items():
        if qid not in gold:
            continue
        actual = False if qid in absent else gold[qid].issubset(ids)
        if claimed and actual:
            tp += 1
        elif claimed and not actual:
            fp += 1
        elif not claimed and actual:
            fn += 1
        else:
            tn += 1
        per_question[qid] = {
            "claimed_complete": claimed,
            "actually_complete": actual,
            "evidence_absent_from_corpus": qid in absent,
            "missing": sorted(gold[qid] - ids),
        }

    n = tp + fp + fn + tn
    if not n:
        return {}
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denominator) if denominator else 0.0

    degenerate = None
    if fp + tn == 0:
        degenerate = (
            "false_complete_rate and recall_of_incomplete are null because the "
            "evidence was in fact complete on every question, so there is no "
            "incompleteness for the claim to be wrong about. That is not a "
            "well-calibrated flag; it is an unmeasurable one. Once the "
            "hierarchy removes the retrieval ceiling, this metric loses its "
            "ground truth -- which is itself the finding.")
    elif tp + fn == 0:
        degenerate = (
            "The evidence was incomplete on every question, so the positive "
            "class is empty and precision-side figures are unmeasurable.")

    return {
        "n": n,
        "confusion": {
            "claimed_complete_and_complete": tp,
            "claimed_complete_but_incomplete": fp,
            "claimed_incomplete_but_complete": fn,
            "claimed_incomplete_and_incomplete": tn,
        },
        "accuracy": round((tp + tn) / n, 4),
        "false_complete_rate": round(fp / (fp + tn), 4) if (fp + tn) else None,
        "recall_of_incomplete": round(tn / (fp + tn), 4) if (fp + tn) else None,
        "mcc": round(mcc, 4),
        "degenerate": degenerate,
        "per_question": per_question,
    }


def score_absent_evidence(answers: list[dict], curations: list[dict],
                          absent: set[str]) -> dict:
    """How the pipeline behaves when the answer is not in the corpus.

    This is the measurement the ranked and set metrics cannot make. For a
    question whose governing statute is absent, there is no provision to rank
    and no set to score; the only thing worth knowing is whether the pipeline
    said so or answered anyway.

    Abstaining is the correct outcome. Answering confidently from provisions
    that do not govern the question is the failure this whole variant is meant
    to be able to detect.
    """
    if not absent:
        return {
            "questions": 0,
            "note": ("No absent-evidence questions in this gold set. Until some "
                     "exist, the answerability metrics have no negative class "
                     "and cannot distinguish a well-calibrated pipeline from a "
                     "pipeline that always claims completeness."),
        }

    relevant = [a for a in answers if a["question_id"] in absent]
    abstained = [a for a in relevant if not a["answerable"]]
    answered = [a for a in relevant if a["answerable"]]
    cited_anyway = [a for a in answered if a["cited_node_ids"]]
    flagged_gap = [a for a in relevant if a.get("missing_evidence")]

    by_question = {}
    for record in curations:
        if record["question_id"] in absent:
            by_question.setdefault(record["question_id"], []).append(record)
    said_incomplete = sum(
        1 for records in by_question.values()
        if any(not r["evidence_complete"] for r in records))

    return {
        "questions": len(relevant),
        "abstained": len(abstained),
        "answered_anyway": len(answered),
        "answered_and_cited_provisions": len(cited_anyway),
        "abstention_rate": (round(len(abstained) / len(relevant), 4)
                            if relevant else None),
        "named_the_gap_in_missing_evidence": len(flagged_gap),
        "curator_said_incomplete_at_some_iteration": said_incomplete,
        "note": (
            "abstention_rate is the headline: the fraction of questions whose "
            "governing statute is not in the corpus where the pipeline declined "
            "to answer. answered_and_cited_provisions counts the dangerous "
            "cases -- an answer built on provisions that do not govern the "
            "question, presented with citations."),
        "per_question": {
            a["question_id"]: {
                "answerable": a["answerable"],
                "cited_node_ids": a["cited_node_ids"],
                "missing_evidence": a.get("missing_evidence") or [],
                "stopped_by": a.get("stopped_by"),
            }
            for a in relevant
        },
    }


def score_sub_question_coverage(curations: list[dict],
                                gold: dict[str, set[str]]) -> dict:
    """Is the coverage table honest analysis, or narration after the fact?

    Of the points marked covered, how often did the cited provisions actually
    include gold. Of the points marked not covered, how often the described gap
    really was outside the pool. A table that scores badly here is decoration,
    and deriving completeness from it buys nothing.
    """
    covered = covered_with_gold = 0
    not_covered = not_covered_truly_absent = 0
    for record in curations:
        gold_ids = gold.get(record["question_id"])
        if gold_ids is None:
            continue
        pool_ids = {n["node_id"] for n in record.get("pool", [])} or None
        for sub_question in record.get("sub_questions", []):
            ids = set(sub_question.get("covering_node_ids") or [])
            if sub_question.get("status") == "covered":
                covered += 1
                covered_with_gold += int(bool(ids & gold_ids))
            elif sub_question.get("status") == "not_covered":
                not_covered += 1
                if pool_ids is not None:
                    not_covered_truly_absent += int(bool(gold_ids - pool_ids))
    return {
        "points_marked_covered": covered,
        "covered_points_naming_gold": covered_with_gold,
        "covered_precision": round(covered_with_gold / covered, 4) if covered else None,
        "points_marked_not_covered": not_covered,
        "not_covered_with_gold_genuinely_absent": not_covered_truly_absent,
        "not_covered_precision": (round(not_covered_truly_absent / not_covered, 4)
                                  if not_covered else None),
        "note": (
            "not_covered_precision is only computable where the run recorded the "
            "pool alongside the curation; it asks whether any gold provision was "
            "genuinely outside the pool at that point, not whether this "
            "particular point's gap was."),
    }


def koblex_baseline_calibration(run_name: str, gold: dict[str, set[str]]) -> dict:
    """Recompute the koblex baseline's calibration, so the finding lands in JSON.

    Two ground truths, because the two readings differ and both are cited:
    whether the candidate pool held all the gold (what the prompt asked the model
    to judge), and whether the model's own selection did.
    """
    path = KOBLEX_RUNS_DIR / run_name / "provision_selections.jsonl"
    candidates_path = KOBLEX_RUNS_DIR / run_name / "retrieval_candidates.jsonl"
    if not path.is_file():
        return {"available": False,
                "reason": f"{config.display_path(path)} not found"}

    selections = config.load_jsonl(path)
    pool_by_qid = {}
    if candidates_path.is_file():
        pool_by_qid = {
            c["question_id"]: {n["node_id"] for n in c["candidates"]}
            for c in config.load_jsonl(candidates_path)
        }

    against_pool = {
        s["question_id"]: (bool(s["evidence_complete"]),
                           pool_by_qid.get(s["question_id"], set()))
        for s in selections if s["question_id"] in pool_by_qid
    }
    against_selection = {
        s["question_id"]: (bool(s["evidence_complete"]),
                           set(s["selected_node_ids"]))
        for s in selections
    }
    return {
        "available": True,
        "run_name": run_name,
        "claims_complete": sum(1 for s in selections if s["evidence_complete"]),
        "claims_total": len(selections),
        "against_candidate_pool": score_calibration(against_pool, gold),
        "against_own_selection": score_calibration(against_selection, gold),
    }


# --------------------------------------------------------------------------- #
# iterations
# --------------------------------------------------------------------------- #

def score_iterations(curations: list[dict], answers: list[dict],
                     gold: dict[str, set[str]]) -> dict:
    """Loop behaviour, and whether iterating helped or hurt."""
    by_question: dict[str, list[dict]] = defaultdict(list)
    for record in curations:
        by_question[record["question_id"]].append(record)
    for records in by_question.values():
        records.sort(key=lambda r: r["iteration"])

    per_iteration: dict[str, dict] = defaultdict(
        lambda: {"questions": 0, "selected": [], "recall": [], "pool_size": [],
                 "complete": [], "forced": 0, "new_gold_found": 0,
                 "gold_lost": 0})
    added, lost = [], []

    for qid, records in by_question.items():
        gold_ids = gold.get(qid)
        previous: set[str] = set()
        for record in records:
            key = str(record["iteration"])
            block = per_iteration[key]
            block["questions"] += 1
            retained = set(record.get("retained_node_ids")
                           or record["relevant_node_ids"])
            block["selected"].append(float(len(retained)))
            block["pool_size"].append(float(record["pool_size"]))
            block["complete"].append(float(record["evidence_complete"]))
            block["forced"] += int(record.get("forced_answerable", False))
            if gold_ids:
                block["recall"].append(
                    len(retained & gold_ids) / len(gold_ids))
                if record["iteration"] > 1:
                    gained = (retained & gold_ids) - (previous & gold_ids)
                    dropped = (previous & gold_ids) - (retained & gold_ids)
                    block["new_gold_found"] += len(gained)
                    block["gold_lost"] += len(dropped)
                    if gained:
                        added.append(
                            {"question_id": qid, "iteration": record["iteration"],
                             "node_ids": sorted(gained)})
                    if dropped:
                        lost.append(
                            {"question_id": qid, "iteration": record["iteration"],
                             "node_ids": sorted(dropped)})
            previous = retained

    iterations = {}
    for key in sorted(per_iteration, key=int):
        block = per_iteration[key]
        iterations[key] = {
            "questions": block["questions"],
            "mean_selected": _mean(block["selected"]),
            "mean_pool_size": _mean(block["pool_size"]),
            "selection_recall": _mean(block["recall"]),
            "complete_evidence_rate": _mean(block["complete"]),
            "forced_answerable": block["forced"],
            "new_gold_found": block["new_gold_found"],
            "gold_lost": block["gold_lost"],
        }

    histogram: dict[str, int] = {}
    stopped: dict[str, int] = {}
    for answer in answers:
        histogram[str(answer["iterations"])] = (
            histogram.get(str(answer["iterations"]), 0) + 1)
        stopped[str(answer["stopped_by"])] = (
            stopped.get(str(answer["stopped_by"]), 0) + 1)
    counts = [float(a["iterations"]) for a in answers]

    return {
        "mean_iterations": _mean(counts),
        "iteration_histogram": dict(sorted(histogram.items())),
        "stopped_by": stopped,
        "per_iteration": iterations,
        "questions_where_iteration_added_gold": added,
        "questions_where_iteration_lost_gold": lost,
        "note": (
            "gold_lost above zero means re-filtering dropped a gold provision "
            "the curator had already kept. HiREC re-filters rather than "
            "freezing accumulated evidence; --freeze-evidence is the arm that "
            "does not."),
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--run-name", dest="run_name", required=True)
    parser.add_argument("--gold", type=Path, default=GOLD_PATH)
    parser.add_argument("--baseline-run", dest="baseline_run", default=None,
                        help="A koblex run name to recompute calibration for, "
                             "e.g. smoke-b1.")
    args = parser.parse_args()

    run_dir = config.RUNS_DIR / args.run_name
    if not run_dir.is_dir():
        print(f"no such run directory: {run_dir}", file=sys.stderr)
        return 1

    gold_records = config.load_jsonl(args.gold)
    gold = {g["question_id"]: set(g["relevant_provisions"]) for g in gold_records}
    gold_meta = {g["question_id"]: g for g in gold_records}
    # Questions whose governing statute is not in the corpus. Empty gold alone
    # would be ambiguous, so the coverage field is authoritative and an empty
    # provision list is accepted as corroboration.
    absent = {g["question_id"] for g in gold_records
              if (g.get("corpus_coverage") == "absent"
                  or not g.get("relevant_provisions"))}

    metrics: dict = {
        "run_name": args.run_name,
        "gold_path": config.display_path(args.gold),
        "gold_questions": len(gold_records),
        "matching": "exact node_id",
        "notes": [],
    }

    grouping = [f"recall@{k}" for k in RECALL_CUTOFFS_POOL] + [
        "reciprocal_rank", "complete_in_candidates"]

    # -- the ceiling run -------------------------------------------------- #
    ceiling_file = run_dir / "hierarchy_pool.jsonl"
    pool_records = None
    if ceiling_file.is_file():
        pool_records = config.load_jsonl(ceiling_file)
        ranked = {r["question_id"]: [n["node_id"] for n in r["pool"]]
                  for r in pool_records}
        scored = score_ranked(ranked, gold, RECALL_CUTOFFS_POOL)
        if scored:
            scored["summary"]["complete_evidence_in_pool"] = (
                scored["summary"].pop("complete_evidence_in_candidates"))
            scored["grouped_by_question_type"] = group_by(
                scored["per_question"], gold_meta, "question_type", grouping)
            scored["grouped_by_n_hops"] = group_by(
                scored["per_question"], gold_meta, "n_hops", grouping)
            metrics["hierarchy_pool_ranked"] = scored
        seed_acts = {r["question_id"]: set(r["act_ids"]) for r in pool_records}
        act_block = score_act_selection(
            {r["question_id"]: r["act_ids"] for r in pool_records},
            gold, seed_acts)
        if act_block:
            metrics["act_selection"] = act_block
        metrics["pool_shape"] = {
            "mean_pool_size": _mean([float(r["pool_size"]) for r in pool_records]),
            "max_pool_size": max(r["pool_size"] for r in pool_records),
            "mean_pool_chars": _mean([float(r["pool_chars"]) for r in pool_records]),
            "max_pool_chars": max(r["pool_chars"] for r in pool_records),
            "mean_sections": _mean(
                [float(len(r["section_ids"])) for r in pool_records]),
            "truncated_questions": [r["question_id"] for r in pool_records
                                    if r["truncated"]],
        }

    # -- the loop run ----------------------------------------------------- #
    pools_file = run_dir / "retrieval_pools.jsonl"
    first_pools: dict[str, dict] = {}
    if pools_file.is_file():
        for record in config.load_jsonl(pools_file):
            if record["label"] != "merged":
                continue
            existing = first_pools.get(record["question_id"])
            if existing is None or record["iteration"] < existing["iteration"]:
                first_pools[record["question_id"]] = record
        if first_pools:
            ranked = {qid: [n["node_id"] for n in r["pool"]]
                      for qid, r in first_pools.items()}
            scored = score_ranked(ranked, gold, RECALL_CUTOFFS_POOL)
            if scored:
                scored["summary"]["complete_evidence_in_pool"] = (
                    scored["summary"].pop("complete_evidence_in_candidates"))
                scored["grouped_by_question_type"] = group_by(
                    scored["per_question"], gold_meta, "question_type", grouping)
                scored["grouped_by_n_hops"] = group_by(
                    scored["per_question"], gold_meta, "n_hops", grouping)
                metrics["hierarchy_pool_ranked"] = scored
            metrics["pool_shape"] = {
                "iteration": 1,
                "mean_pool_size": _mean(
                    [float(r["pool_size"]) for r in first_pools.values()]),
                "max_pool_size": max(r["pool_size"] for r in first_pools.values()),
                "mean_pool_chars": _mean(
                    [float(r["pool_chars"]) for r in first_pools.values()]),
                "max_pool_chars": max(r["pool_chars"] for r in first_pools.values()),
                "mean_sections": _mean(
                    [float(len(r["section_ids"])) for r in first_pools.values()]),
                "truncated_questions": [qid for qid, r in first_pools.items()
                                        if r["truncated"]],
            }

    acts_file = run_dir / "act_selections.jsonl"
    if acts_file.is_file() and first_pools:
        selections = config.load_jsonl(acts_file)
        seed_acts = {qid: {n["act_id"] for n in r["pool"] if n.get("act_id")}
                     for qid, r in first_pools.items()}
        act_block = score_act_selection(
            {s["question_id"]: s["selected_act_ids"] for s in selections},
            gold, seed_acts)
        if act_block:
            act_block["selector"] = (selections[0]["selector"]
                                     if selections else None)
            metrics["act_selection"] = act_block

    curations_file = run_dir / "curations.jsonl"
    answers_file = run_dir / "answers.jsonl"
    if curations_file.is_file() and answers_file.is_file():
        curations = config.load_jsonl(curations_file)
        answers = config.load_jsonl(answers_file)

        for record in curations:
            pool = first_pools.get(record["question_id"])
            if pool and record["iteration"] == pool["iteration"]:
                record["pool"] = pool["pool"]

        metrics["iterations"] = score_iterations(curations, answers, gold)

        # Calibration, at the first iteration -- the decision that actually
        # determines whether the loop runs at all.
        first = {}
        for record in curations:
            if record["question_id"] not in first or (
                    record["iteration"] < first[record["question_id"]]["iteration"]):
                first[record["question_id"]] = record
        pool_ids = {qid: {n["node_id"] for n in first_pools[qid]["pool"]}
                    for qid in first if qid in first_pools}

        def score_calibration_absent(claims, gold_map):
            return score_calibration(claims, gold_map, absent)

        calibration = {"iteration": 1}
        for label, flag in (("model_claimed", "model_claimed_complete"),
                            ("derived", "derived_complete")):
            if pool_ids:
                calibration[f"{label}_against_pool"] = score_calibration_absent(
                    {qid: (bool(r[flag]), pool_ids.get(qid, set()))
                     for qid, r in first.items()}, gold)
            calibration[f"{label}_against_selection"] = score_calibration_absent(
                {qid: (bool(r[flag]),
                       set(r.get("retained_node_ids") or r["relevant_node_ids"]))
                 for qid, r in first.items()}, gold)
        calibration["note"] = (
            "against_pool is what the curation prompt actually asks the model to "
            "judge: does the pool contain every rule the question needs. "
            "against_selection asks the stricter question of whether the "
            "evidence it will answer from is complete. Both are reported "
            "because the two readings can disagree.")
        metrics["answerability_calibration"] = calibration
        metrics["sub_question_coverage_calibration"] = (
            score_sub_question_coverage(curations, gold))
        metrics["absent_evidence"] = score_absent_evidence(
            answers, curations, absent)

        curated = {a["question_id"]: set(a["curated_node_ids"]) for a in answers}
        scored = score_sets(curated, gold, "curated")
        if scored:
            scored["ranking_note"] = (
                "Curated provisions are an unordered set. No Recall@k or MRR is "
                "reported; their earlier pool positions are deliberately not "
                "reused as a pseudo-ranking.")
            scored["grouped_by_question_type"] = group_by(
                scored["per_question"], gold_meta, "question_type",
                ["precision", "recall", "f1", "complete_evidence", "exact_set"])
            scored["grouped_by_n_hops"] = group_by(
                scored["per_question"], gold_meta, "n_hops",
                ["precision", "recall", "f1", "complete_evidence", "exact_set"])
            metrics["curated_provisions"] = scored

        cited = {a["question_id"]: set(a["cited_node_ids"]) for a in answers}
        scored = score_sets(cited, gold, "cited")
        if scored:
            summary = scored["summary"]
            metrics["answer_citations"] = {
                "citation_precision": summary["precision"],
                "citation_recall": summary["recall"],
                "citation_f1": summary["f1"],
                "citation_exact_match": summary["exact_set_accuracy"],
                "questions": summary["questions"],
                "per_question": scored["per_question"],
            }
        metrics["answerability"] = {
            "answers_written": len(answers),
            "answerable": sum(1 for a in answers if a["answerable"]),
            "abstained": sum(1 for a in answers if not a["answerable"]),
        }

    if args.baseline_run:
        metrics["koblex_baseline_calibration"] = koblex_baseline_calibration(
            args.baseline_run, gold)

    errors_file = run_dir / "errors.jsonl"
    if errors_file.is_file():
        errors = config.load_jsonl(errors_file)
        metrics["errors"] = {
            "count": len(errors),
            "by_stage": {stage: sum(1 for e in errors if e["stage"] == stage)
                         for stage in sorted({e["stage"] for e in errors})},
        }

    capped = [g["question_id"] for g in gold_records
              if len(g["relevant_provisions"]) > 5]
    if capped:
        metrics["notes"].append(
            f"With 20 questions one question moves any mean by 5 points, and "
            f"{', '.join(capped)} have more than 5 gold provisions each. "
            "Complete-evidence accuracy is the more informative headline number "
            "than any single recall cutoff.")
    metrics["notes"].append(
        "Pool recall@k is not comparable to the koblex b0/b1 recall@k: the "
        "section-expanded pool is a differently-sized object (roughly 91 records "
        "against 20-40), so its cutoffs run to 200.")
    metrics["notes"].append(
        "complete_evidence_in_pool is the ceiling for every downstream number in "
        "this file. No curation or answering metric can exceed it.")
    if absent:
        metrics["notes"].append(
            f"{len(absent)} question(s) have no gold provisions because the "
            "governing statute is not in the corpus. They are excluded from "
            "every rank-aware and set-valued metric, where an empty gold set "
            "has no defined value, and scored in the absent_evidence block "
            "instead. In the calibration block their evidence counts as never "
            "complete.")
    else:
        metrics["notes"].append(
            "No absent-evidence questions in this gold set, so the answerability "
            "metrics have no negative class: a claim of completeness is never "
            "wrong and false_complete_rate is null by construction rather than "
            "by good calibration.")

    config.write_json(metrics, run_dir / "metrics.json")

    print(f"run: {args.run_name}")
    if "hierarchy_pool_ranked" in metrics:
        print(f"  pool         : {metrics['hierarchy_pool_ranked']['summary']}")
    if "pool_shape" in metrics:
        print(f"  pool shape   : {metrics['pool_shape']}")
    if "act_selection" in metrics:
        print(f"  acts         : {metrics['act_selection']['summary']}")
    if "curated_provisions" in metrics:
        print(f"  curated      : {metrics['curated_provisions']['summary']}")
    if "answer_citations" in metrics:
        cite = {k: v for k, v in metrics["answer_citations"].items()
                if k != "per_question"}
        print(f"  citations    : {cite}")
    if "iterations" in metrics:
        block = metrics["iterations"]
        print(f"  iterations   : mean {block['mean_iterations']}, "
              f"stopped_by {block['stopped_by']}")
    if metrics.get("absent_evidence", {}).get("questions"):
        block = metrics["absent_evidence"]
        print(f"  absent-ev    : {block['questions']} questions, "
              f"abstained {block['abstained']}, "
              f"answered anyway {block['answered_anyway']}")
    if "answerability_calibration" in metrics:
        for key, value in metrics["answerability_calibration"].items():
            if isinstance(value, dict) and "confusion" in value:
                print(f"  calib {key}: {value['confusion']} "
                      f"false_complete_rate={value['false_complete_rate']}")
    print(f"wrote {config.display_path(run_dir / 'metrics.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
