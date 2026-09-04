"""Check a question set and its gold file before anything is run against them.

Free, offline, no API calls. This is the self-check to run after writing
questions or adding gold provision IDs, and before asking anyone to review
them. It catches the mistakes that are cheap to make and expensive to find
later: a node_id that does not exist, a question with no gold at all, a
duplicated question_id, an n_hops that contradicts the number of provisions.

It deliberately does NOT judge whether a question is good, whether the gold is
legally correct, or whether the answer text is right. Those need a human who
can read the statute. What this proves is only that the files are internally
consistent and that every ID resolves against the corpus.

Exit code is 1 when there is at least one error, so it can gate a commit.
Warnings do not fail the run; they are things to look at, not necessarily
things to fix.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py
    uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py \
        --questions path/to/questions.jsonl --gold path/to/gold.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402
import hirec_hierarchy as hierarchy  # noqa: E402
import hirec_index  # noqa: E402

DEFAULT_GOLD = config.SHARED_DATA_DIR / "smoke_test_20_gold.jsonl"

QUESTION_FIELDS = {"question_id", "paper_id", "background", "question"}
GOLD_FIELDS = {"question_id", "question_type", "answer", "relevant_provisions",
               "citations", "n_hops", "corpus_coverage"}
QUESTION_TYPES = {"recall", "application", "calculation"}
COVERAGE_VALUES = {"complete", "partial", "absent"}


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


# --------------------------------------------------------------------------- #
# structural checks
# --------------------------------------------------------------------------- #

def check_questions(questions: list[dict], report: Report) -> None:
    seen = Counter(q.get("question_id") for q in questions)
    for qid, count in seen.items():
        if count > 1:
            report.error(str(qid), f"question_id appears {count} times")

    for index, item in enumerate(questions):
        where = item.get("question_id") or f"question #{index + 1}"
        missing = QUESTION_FIELDS - set(item)
        if missing:
            report.error(where, f"missing field(s): {sorted(missing)}")
        extra = set(item) - QUESTION_FIELDS
        if extra:
            report.warn(where, f"unexpected field(s): {sorted(extra)}")
        if not (item.get("question") or "").strip():
            report.error(where, "question text is empty")
        if not (item.get("background") or "").strip():
            report.warn(where, "background is empty; retrieval uses background "
                               "and question together, so an empty background "
                               "makes the question harder to retrieve for")
        if (item.get("question") or "").strip().endswith(":"):
            report.warn(where, "question ends in a colon; it may be truncated")


def check_gold(gold: list[dict], questions: list[dict], report: Report) -> None:
    question_ids = {q.get("question_id") for q in questions}
    gold_ids = [g.get("question_id") for g in gold]

    for qid, count in Counter(gold_ids).items():
        if count > 1:
            report.error(str(qid), f"gold record appears {count} times")

    for qid in question_ids - set(gold_ids):
        report.error(str(qid), "question has no gold record")
    for qid in set(gold_ids) - question_ids:
        report.error(str(qid), "gold record has no matching question")

    for index, record in enumerate(gold):
        where = record.get("question_id") or f"gold #{index + 1}"
        missing = GOLD_FIELDS - set(record)
        if missing:
            report.error(where, f"missing field(s): {sorted(missing)}")

        provisions = record.get("relevant_provisions") or []
        coverage_value = (record.get("corpus_coverage") or "").strip()
        # An absent-evidence question is a legitimate and valuable kind of gold:
        # the correct behaviour is to abstain, so there is nothing to cite and an
        # empty list is the answer. Every other coverage value needs provisions.
        if not provisions and coverage_value != "absent":
            report.error(where, "relevant_provisions is empty; a question with "
                                "no gold provisions must set corpus_coverage to "
                                "'absent'")
        if provisions and coverage_value == "absent":
            report.error(where, "corpus_coverage is 'absent' but "
                                f"{len(provisions)} provision(s) are listed; "
                                "absent means the rule is not in the corpus")
        if len(set(provisions)) != len(provisions):
            duplicated = [p for p, c in Counter(provisions).items() if c > 1]
            report.error(where, f"relevant_provisions repeats: {duplicated}")

        question_type = record.get("question_type")
        if question_type not in QUESTION_TYPES:
            report.error(where, f"question_type {question_type!r} is not one of "
                                f"{sorted(QUESTION_TYPES)}")

        coverage = record.get("corpus_coverage")
        if coverage not in COVERAGE_VALUES:
            report.error(where, f"corpus_coverage {coverage!r} is not one of "
                                f"{sorted(COVERAGE_VALUES)}")

        n_hops = record.get("n_hops")
        if not isinstance(n_hops, int) or n_hops < 1:
            report.error(where, f"n_hops {n_hops!r} must be an integer of 1 or more")

        # Not one citation per provision: the established convention groups
        # them ("Registration of Title Act, ss 12-13" covers two node IDs). Only
        # an empty list, or more citations than provisions, is suspicious. A
        # warning that fires on well-formed data just teaches people to ignore
        # warnings.
        citations = record.get("citations") or []
        if provisions and not citations:
            report.warn(where, "no citations recorded")
        elif len(citations) > len(provisions):
            report.warn(where, f"{len(citations)} citations but only "
                               f"{len(provisions)} provisions")
        if (not (record.get("answer") or "").strip()
                and coverage_value != "absent"):
            report.warn(where, "answer text is empty")


# --------------------------------------------------------------------------- #
# corpus checks
# --------------------------------------------------------------------------- #

def check_against_corpus(gold: list[dict], questions: list[dict],
                         index, report: Report, seed_top_k: int) -> dict:
    """Resolve every gold ID, and see whether retrieval can reach it at all."""
    corpus_ids = index.node_ids()
    acts = {a["act_id"] for a in index.acts()}
    by_question = {q["question_id"]: q for q in questions}
    reachable_counts = []

    for record in gold:
        where = record.get("question_id") or "?"
        provisions = record.get("relevant_provisions") or []

        for node_id in provisions:
            if node_id not in corpus_ids:
                act_id = str(node_id).split("/")[0]
                hint = ("that Act is not in the corpus"
                        if act_id not in acts
                        else "the Act is in the corpus but that provision is not; "
                             "check the section number and the node path")
                report.error(where, f"gold provision {node_id!r} does not exist "
                                    f"-- {hint}")

        gold_acts = {str(p).split("/")[0] for p in provisions}
        unknown = gold_acts - acts
        if unknown:
            report.error(where, f"gold names unknown act_id(s): {sorted(unknown)}")

        n_hops = record.get("n_hops")
        # An absent-evidence question legitimately has n_hops with no provisions:
        # the hop count describes the question, not the corpus.
        if (isinstance(n_hops, int) and n_hops > len(provisions)
                and coverage_value != "absent"):
            report.warn(where, f"n_hops is {n_hops} but only "
                               f"{len(provisions)} provisions are listed")

        # Can retrieval reach it? Not a pass/fail -- a question whose gold BM25
        # cannot surface is still a legitimate question, and is in fact the kind
        # we most need. But it should be a deliberate choice, not a surprise.
        item = by_question.get(record.get("question_id"))
        if item and provisions:
            query = hirec_index.question_query_text(
                item.get("background", ""), item.get("question", ""))
            hits = index.search(query, seed_top_k)
            pool = hierarchy.section_pool(
                index, hits,
                max_records=config.DEFAULT_MAX_POOL_RECORDS,
                max_chars=config.DEFAULT_MAX_POOL_CHARS)
            present = set(pool.node_ids)
            found = [p for p in provisions if p in corpus_ids and p in present]
            reachable_counts.append(len(found) / len(provisions))
            missing = [p for p in provisions
                       if p in corpus_ids and p not in present]
            if missing:
                report.warn(
                    where,
                    f"{len(missing)} gold provision(s) are in the corpus but "
                    f"outside the retrieved pool at seed_top_k={seed_top_k}: "
                    f"{missing}. If that is intentional set corpus_coverage "
                    f"accordingly; otherwise the question may be unanswerable "
                    f"by this pipeline.")
            if record.get("corpus_coverage") == "complete" and not found:
                report.error(where, "corpus_coverage says complete but no gold "
                                    "provision is retrievable at all")

    return {
        "mean_gold_reachable": (round(sum(reachable_counts) / len(reachable_counts), 4)
                                if reachable_counts else None),
        "questions_fully_reachable": sum(1 for r in reachable_counts if r == 1.0),
        "questions_checked": len(reachable_counts),
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--questions", type=Path, default=config.QUESTIONS_PATH)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    parser.add_argument("--seed-top-k", dest="seed_top_k", type=int,
                        default=config.DEFAULT_SEED_TOP_K)
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Emit the report as JSON instead of text.")
    args = parser.parse_args()

    report = Report()
    for path, label in ((args.questions, "questions"), (args.gold, "gold")):
        if not path.is_file():
            print(f"missing {label} file: {path}", file=sys.stderr)
            return 1

    try:
        questions = config.load_jsonl(args.questions)
    except json.JSONDecodeError as exc:
        print(f"{args.questions} is not valid JSONL: {exc}", file=sys.stderr)
        return 1
    try:
        gold = config.load_jsonl(args.gold)
    except json.JSONDecodeError as exc:
        print(f"{args.gold} is not valid JSONL: {exc}", file=sys.stderr)
        return 1

    check_questions(questions, report)
    check_gold(gold, questions, report)

    reach = {}
    try:
        index = hirec_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        report.warn("index", f"{exc}; corpus checks were skipped")
    else:
        with index:
            reach = check_against_corpus(
                gold, questions, index, report, args.seed_top_k)

    if args.as_json:
        print(json.dumps({
            "questions": len(questions),
            "gold_records": len(gold),
            "errors": report.errors,
            "warnings": report.warnings,
            "reachability": reach,
        }, indent=2))
        return 1 if report.errors else 0

    print(f"questions    : {len(questions)}")
    print(f"gold records : {len(gold)}")
    if reach:
        print(f"gold reachable at seed_top_k={args.seed_top_k}: "
              f"{reach['questions_fully_reachable']}/{reach['questions_checked']} "
              f"questions fully, mean {reach['mean_gold_reachable']}")
    print()
    if report.warnings:
        print(f"WARNINGS ({len(report.warnings)}) -- look, but not necessarily fix:")
        for line in report.warnings:
            print(f"  ! {line}")
        print()
    if report.errors:
        print(f"ERRORS ({len(report.errors)}) -- these must be fixed:")
        for line in report.errors:
            print(f"  x {line}")
        print()
        print("Not ready. Fix the errors above and run this again.")
        return 1

    print("No errors. The files are internally consistent and every gold ID "
          "resolves.")
    print("This does NOT mean the gold is legally correct -- that still needs a "
          "human who has read the statute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
