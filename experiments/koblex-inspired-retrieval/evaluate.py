"""Score a run against the gold file. The only module that reads gold.

Two metric families, because the two outputs have different shapes:

  Ranked BM25 candidates -- B0's retrieved list and B1's merged candidate list
  are genuinely ordered by score, so rank-aware metrics apply: Recall@5/10/20
  and MRR.

  GPT-selected provisions -- an unordered set. No rank-aware metric is reported
  and the selection is NOT re-ranked by its earlier BM25 positions, which would
  invent an ordering the model never produced. Instead: precision, recall, F1,
  complete-evidence accuracy and exact-set accuracy.

Matching is exact on node_id, which is correct here because the gold is authored
at the corpus's own granularity (27 of 44 gold IDs are section records, the other
17 are paragraph/proviso/subsection/closing_text records).

Usage:
    uv run python experiments/koblex-inspired-retrieval/evaluate.py --run-name smoke-b0
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_config as config  # noqa: E402

GOLD_PATH = config.DATA_DIR / "smoke_test_20_gold.jsonl"
RECALL_CUTOFFS = (5, 10, 20)


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


# --------------------------------------------------------------------------- #
# ranked retrieval
# --------------------------------------------------------------------------- #

def score_ranked(ranked: dict[str, list[str]], gold: dict[str, set[str]]) -> dict:
    """Recall@k and MRR over genuinely ranked lists."""
    per_question = {}
    for qid, gold_ids in gold.items():
        if qid not in ranked:
            continue
        order = ranked[qid]
        entry: dict = {"retrieved": len(order), "gold": len(gold_ids)}
        for cutoff in RECALL_CUTOFFS:
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
        for k in RECALL_CUTOFFS
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
            if values and isinstance(values[0], bool):
                block[metric] = _mean([float(v) for v in values])
            elif values:
                block[metric] = _mean([float(v) for v in values])
        out[value] = block
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--run-name", dest="run_name", required=True)
    parser.add_argument("--gold", type=Path, default=GOLD_PATH)
    args = parser.parse_args()

    run_dir = config.RUNS_DIR / args.run_name
    if not run_dir.is_dir():
        print(f"no such run directory: {run_dir}", file=sys.stderr)
        return 1

    gold_records = config.load_jsonl(args.gold)
    gold = {g["question_id"]: set(g["relevant_provisions"]) for g in gold_records}
    gold_meta = {g["question_id"]: g for g in gold_records}

    metrics: dict = {
        "run_name": args.run_name,
        "gold_path": config.display_path(args.gold),
        "gold_questions": len(gold_records),
        "matching": "exact node_id",
        "notes": [],
    }

    # -- ranked: B0 -------------------------------------------------------- #
    bm25_file = run_dir / "bm25_predictions.jsonl"
    if bm25_file.is_file():
        ranked = {
            p["question_id"]: [r["node_id"] for r in p["retrieved"]]
            for p in config.load_jsonl(bm25_file)
        }
        scored = score_ranked(ranked, gold)
        if scored:
            scored["grouped_by_question_type"] = group_by(
                scored["per_question"], gold_meta, "question_type",
                [f"recall@{k}" for k in RECALL_CUTOFFS] + ["reciprocal_rank"])
            scored["grouped_by_n_hops"] = group_by(
                scored["per_question"], gold_meta, "n_hops",
                [f"recall@{k}" for k in RECALL_CUTOFFS] + ["reciprocal_rank"])
            metrics["b0_bm25_ranked"] = scored

    # -- ranked: B1 merged candidates -------------------------------------- #
    candidates_file = run_dir / "retrieval_candidates.jsonl"
    if candidates_file.is_file():
        ranked = {
            c["question_id"]: [n["node_id"] for n in c["candidates"]]
            for c in config.load_jsonl(candidates_file)
        }
        scored = score_ranked(ranked, gold)
        if scored:
            scored["grouped_by_question_type"] = group_by(
                scored["per_question"], gold_meta, "question_type",
                [f"recall@{k}" for k in RECALL_CUTOFFS] + ["reciprocal_rank"])
            scored["grouped_by_n_hops"] = group_by(
                scored["per_question"], gold_meta, "n_hops",
                [f"recall@{k}" for k in RECALL_CUTOFFS] + ["reciprocal_rank"])
            metrics["b1_merged_candidates_ranked"] = scored

    # -- sets: B1 selection ------------------------------------------------ #
    selections_file = run_dir / "provision_selections.jsonl"
    if selections_file.is_file():
        selected = {
            s["question_id"]: set(s["selected_node_ids"])
            for s in config.load_jsonl(selections_file)
        }
        scored = score_sets(selected, gold, "selected")
        if scored:
            scored["ranking_note"] = (
                "Selections are an unordered set. No Recall@k or MRR is reported; "
                "their earlier BM25 positions are deliberately not reused as a "
                "pseudo-ranking.")
            scored["grouped_by_question_type"] = group_by(
                scored["per_question"], gold_meta, "question_type",
                ["precision", "recall", "f1", "complete_evidence", "exact_set"])
            scored["grouped_by_n_hops"] = group_by(
                scored["per_question"], gold_meta, "n_hops",
                ["precision", "recall", "f1", "complete_evidence", "exact_set"])
            metrics["b1_selected_provisions"] = scored

    # -- answers ----------------------------------------------------------- #
    answers_file = run_dir / "answers.jsonl"
    if answers_file.is_file():
        answers = config.load_jsonl(answers_file)
        cited = {a["question_id"]: set(a["cited_node_ids"]) for a in answers}
        scored = score_sets(cited, gold, "cited")
        if scored:
            summary = scored["summary"]
            metrics["b1_answer_citations"] = {
                "citation_precision": summary["precision"],
                "citation_recall": summary["recall"],
                "citation_f1": summary["f1"],
                "citation_exact_match": summary["exact_set_accuracy"],
                "questions": summary["questions"],
                "per_question": scored["per_question"],
            }
        metrics["b1_answerability"] = {
            "answers_written": len(answers),
            "answerable": sum(1 for a in answers if a["answerable"]),
            "abstained": sum(1 for a in answers if not a["answerable"]),
        }

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
            f"Recall@5 is arithmetically capped for {', '.join(capped)}: more "
            "than 5 gold provisions, so 5/n is the ceiling regardless of "
            "retrieval quality. With 20 questions one question moves the mean "
            "by 5 points, so Recall@20 and complete-evidence accuracy are the "
            "more informative headline numbers.")
    metrics["notes"].append(
        "complete_evidence_in_candidates on a ranked block is a ceiling: it is "
        "the fraction of questions where every gold provision was present "
        "anywhere in the retrieved list, i.e. the best the selection stage "
        "could possibly achieve.")

    config.write_json(metrics, run_dir / "metrics.json")

    print(f"run: {args.run_name}")
    for block in ("b0_bm25_ranked", "b1_merged_candidates_ranked",
                  "b1_selected_provisions"):
        if block in metrics:
            print(f"  {block}: {metrics[block]['summary']}")
    if "b1_answer_citations" in metrics:
        cite = {k: v for k, v in metrics["b1_answer_citations"].items()
                if k != "per_question"}
        print(f"  b1_answer_citations: {cite}")
    print(f"wrote {config.display_path(run_dir / 'metrics.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
