"""Run the statute QA agent over src/questions.md in one configuration.

Usage:
  python evaluation/qa-agent/run_eval.py baseline    # lexical-only, no graph, no corrective
  python evaluation/qa-agent/run_eval.py upgraded    # dense + graph + corrective loop
  python evaluation/qa-agent/run_eval.py --score     # compare finished runs against gold

Both runs use the same harness (draftly.retrieval.qa_evaluation), full-answer
mode, resumable checkpoints. Scoring is objective: gold-labels.json only encodes
sections/statutes EXPLICITLY named in the question text.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

RUN_DIR = ROOT / "evaluation" / "qa-agent"
GOLD = json.loads((RUN_DIR / "gold-labels.json").read_text(encoding="utf-8"))

CONFIGS = {
    "baseline": {
        "DRAFTLY_DISABLE_DENSE": "1",
        "DRAFTLY_DISABLE_GRAPH": "1",
        "DRAFTLY_SKIP_CORRECTIVE": "1",
    },
    "upgraded": {
        "DRAFTLY_DISABLE_DENSE": "0",
        "DRAFTLY_DISABLE_GRAPH": "0",
        "DRAFTLY_SKIP_CORRECTIVE": "0",
    },
}


def run(config_name: str) -> None:
    os.environ.update(CONFIGS[config_name])
    from draftly.retrieval.answering import answer
    from draftly.retrieval.qa_evaluation import run_qa_evaluation
    from draftly.retrieval.search import search

    metrics = run_qa_evaluation(
        ROOT / "src" / "questions.md",
        RUN_DIR / config_name,
        retrieve=lambda text: [hit.to_dict(include_text=False) for hit in search(text)],
        answer=answer,
        mode="full_answer",
        config={"configuration": config_name, **CONFIGS[config_name]},
        resume=True,
    )
    print(json.dumps({"config": config_name, "answer_quality": metrics["answer_quality"]}, indent=2))


def _collect_ids(record: dict) -> set[str]:
    ids: set[str] = set()

    def walk(value):
        if isinstance(value, dict):
            if value.get("section_id"):
                ids.add(str(value["section_id"]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(record.get("retrieval"))
    walk((record.get("answer") or {}).get("hits"))
    return ids


def score(config_name: str) -> dict | None:
    path = RUN_DIR / config_name / "results.jsonl"
    if not path.exists():
        return None
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    section_hits = section_total = 0
    source_hits = source_total = 0
    verified_claims = 0
    parts_total = parts_covered = 0
    outcomes: dict[str, int] = {}
    for record in records:
        qid = record["question_id"]
        retrieved = _collect_ids(record)
        retrieved_sources = {section.split(":", 1)[0] for section in retrieved}
        gold = GOLD.get(qid)
        if gold:
            for section in gold.get("expected_sections", []):
                section_total += 1
                section_hits += int(section in retrieved)
            for source in gold.get("expected_sources", []):
                source_total += 1
                source_hits += int(source in retrieved_sources)
        answer_payload = record.get("answer") or {}
        outcomes[str(answer_payload.get("outcome"))] = outcomes.get(str(answer_payload.get("outcome")), 0) + 1
        claims = answer_payload.get("claims") or []
        verified_claims += sum(1 for claim in claims if claim.get("verified"))
        analysis = record.get("analysis") or {}
        part_numbers = {str(part["number"]) for part in analysis.get("subquestions", [])}
        parts_total += len(part_numbers)
        parts_covered += len(part_numbers & {str(claim.get("part")) for claim in claims if claim.get("verified")})
    return {
        "config": config_name,
        "questions": len(records),
        "explicit_section_recall": f"{section_hits}/{section_total}"
        + (f" = {section_hits / section_total:.0%}" if section_total else ""),
        "named_statute_coverage": f"{source_hits}/{source_total}"
        + (f" = {source_hits / source_total:.0%}" if source_total else ""),
        "verified_claims": verified_claims,
        "part_coverage": f"{parts_covered}/{parts_total}"
        + (f" = {parts_covered / parts_total:.0%}" if parts_total else ""),
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    argument = sys.argv[1] if len(sys.argv) > 1 else "--score"
    if argument in CONFIGS:
        run(argument)
    else:
        for name in CONFIGS:
            result = score(name)
            print(json.dumps(result, indent=2) if result else f"{name}: no results yet")
