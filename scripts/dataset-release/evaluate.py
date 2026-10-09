"""Evaluate section rankings against provisional reference labels.

This file uses only the Python standard library and may be copied into a
dataset release. It does not implement a retriever.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_split(rows: list[dict]) -> None:
    ids: set[str] = set()
    matters: dict[str, str] = {}
    for row in rows:
        qid = row["benchmark_question_id"]
        mid = row["benchmark_matter_id"]
        split = row["split"]
        if qid in ids:
            raise ValueError(f"duplicate question: {qid}")
        if split not in {"development", "test"}:
            raise ValueError(f"invalid split: {split}")
        if mid in matters and matters[mid] != split:
            raise ValueError(f"matter {mid} appears in both splits")
        if not row["indispensable_section_ids"]:
            raise ValueError(f"empty reference set: {qid}")
        ids.add(qid)
        matters[mid] = split


def score(rows: list[dict], predictions: list[dict]) -> dict:
    validate_split(rows)
    by_id = {row["benchmark_question_id"]: row for row in rows}
    seen: set[str] = set()
    by_matter: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    for pred in predictions:
        qid = pred["benchmark_question_id"]
        if qid not in by_id or qid in seen:
            raise ValueError(f"unknown or duplicate prediction: {qid}")
        ranking = pred["ranked_section_ids"]
        if not isinstance(ranking, list) or not all(isinstance(x, str) for x in ranking):
            raise ValueError(f"ranking must be a list of section IDs: {qid}")
        if len(ranking) != len(set(ranking)):
            raise ValueError(f"duplicate section in ranking: {qid}")
        gold = set(by_id[qid]["indispensable_section_ids"])
        hits = len(gold & set(ranking[:20]))
        by_matter[by_id[qid]["benchmark_matter_id"]].append((float(hits == len(gold)), hits / len(gold)))
        seen.add(qid)
    if seen != set(by_id):
        raise ValueError(f"missing predictions for {len(set(by_id) - seen)} reference questions")
    means = [(sum(c for c, _ in vals) / len(vals), sum(r for _, r in vals) / len(vals)) for vals in by_matter.values()]
    return {
        "questions": len(seen),
        "matters": len(means),
        "C@20_matter_macro": sum(c for c, _ in means) / len(means),
        "Indispensable_Recall@20_matter_macro": sum(r for _, r in means) / len(means),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score(read_jsonl(args.reference), read_jsonl(args.predictions)), indent=2))


if __name__ == "__main__":
    main()
