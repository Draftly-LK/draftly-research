"""Select the keep/enrich candidate pool, group it into matters and split it
into Tier A (immediate processing) and Tier B (manual review).

Reuses the matter-building logic of scripts/pastpaper-dataset/
build_selected_matters.py with a wider predicate, so effective backgrounds,
normalisation and ordering are computed exactly as for the earlier
44-matter set.

Outputs (all status=unverified):

  candidates/keep-enrich-candidates.jsonl   one row per candidate question
  candidates/matters.jsonl                  one row per matter, all its questions
  candidates/tier-a.jsonl                   question ids + tier reasons
  candidates/tier-b-review.jsonl
  audits/candidate-funnel.json

    uv run python scripts/statutory-qa/select_candidates.py
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "pastpaper-dataset"))

import sq_common as C  # noqa: E402
import build_selected_matters as bsm  # noqa: E402

CANDIDATE_ACTIONS = {"keep", "enrich"}
TIER_A = {
    "candidate_action": sorted(CANDIDATE_ACTIONS),
    "extraction_quality": "clean",
    "confidence_min": 0.80,
    "context_dependency": ["required", "partial"],
}


def _candidate_failed(c: dict[str, Any]) -> list[str]:
    failed = []
    if c["candidate_action"] not in CANDIDATE_ACTIONS:
        failed.append(f"candidate_action={c['candidate_action']}")
    return failed


def tier_a_failures(c: dict[str, Any]) -> list[str]:
    failed = []
    if c["extraction_quality"] != TIER_A["extraction_quality"]:
        failed.append(f"extraction_quality={c['extraction_quality']}")
    if float(c["confidence"]) < TIER_A["confidence_min"]:
        failed.append(f"confidence={c['confidence']}")
    if c["context_dependency"] not in TIER_A["context_dependency"]:
        failed.append(f"context_dependency={c['context_dependency']}")
    return failed


def main() -> int:
    questions = C.read_jsonl(C.ATOMIC_QUESTIONS)
    classifications = C.read_jsonl(C.ATOMIC_CLASSIFICATIONS)
    by_c = {c["atomic_id"]: c for c in classifications}

    # Widen the selection predicate without editing the shared module.
    bsm.failed_predicates = _candidate_failed  # type: ignore[assignment]
    bsm.SELECTION_STATUS = "candidate"

    # First pass: discover matters the shared builder quarantines for
    # background-boundary problems. Those go straight to Tier B review.
    quarantined: list[dict[str, Any]] = []
    try:
        matters, flat, audit = bsm.build(questions, classifications, None, None)
    except bsm.ValidationError as exc:
        quarantined = list(exc.report.get("quarantined_records") or [])
        if not quarantined:
            raise
        bad_ids = {aid for rec in quarantined for aid in rec["atomic_ids"]}

        def _failed(c: dict[str, Any], _bad=bad_ids) -> list[str]:
            out = _candidate_failed(c)
            if c["atomic_id"] in _bad:
                out.append("quarantined_background_boundary")
            return out

        bsm.failed_predicates = _failed  # type: ignore[assignment]
        matters, flat, audit = bsm.build(questions, classifications, None, None)
    audit["quarantined_records"] = quarantined

    sessions = C.paper_sessions()
    tier_a_rows, tier_b_rows = [], []
    for row in flat:
        c = by_c[row["atomic_id"]]
        failures = tier_a_failures(c)
        row["tier"] = "A" if not failures else "B"
        row["tier_b_reasons"] = failures
        row["matter_reference_date"] = sessions[row["paper_no"]]["date"]
        row["exam_session"] = sessions[row["paper_no"]]["session"]
        row["missing_fact_types"] = list(c.get("missing_fact_types") or [])
        (tier_a_rows if not failures else tier_b_rows).append({
            "benchmark_question_id": row["benchmark_question_id"],
            "benchmark_matter_id": row["benchmark_matter_id"],
            "atomic_id": row["atomic_id"],
            "candidate_action": c["candidate_action"],
            "tier_b_reasons": failures,
        })

    tier_by_q = {r["benchmark_question_id"]: r for r in flat}
    for m in matters:
        m["matter_reference_date"] = sessions[m["paper_no"]]["date"]
        m["exam_session"] = sessions[m["paper_no"]]["session"]
        for q in m["questions"]:
            fr = tier_by_q[q["benchmark_question_id"]]
            q["tier"] = fr["tier"]
            q["tier_b_reasons"] = fr["tier_b_reasons"]
            q["missing_fact_types"] = fr["missing_fact_types"]
        tiers = {q["tier"] for q in m["questions"]}
        m["matter_tier"] = "A" if "A" in tiers else "B"
        m["tier_a_question_count"] = sum(q["tier"] == "A" for q in m["questions"])

    C.write_jsonl(C.CANDIDATES_DIR / "keep-enrich-candidates.jsonl", flat)
    C.write_jsonl(C.CANDIDATES_DIR / "matters.jsonl", matters)
    C.write_jsonl(C.CANDIDATES_DIR / "tier-a.jsonl", tier_a_rows)
    by_q_src = {q["atomic_id"]: q for q in questions}
    for rec in quarantined:
        for aid in rec["atomic_ids"]:
            tier_b_rows.append({
                "benchmark_question_id": None,
                "benchmark_matter_id": None,
                "atomic_id": aid,
                "candidate_action": by_c[aid]["candidate_action"],
                "tier_b_reasons": ["quarantined_background_boundary: " + "; ".join(rec["reason"])],
                "grouping_key": rec["grouping_key"],
                "paper_no": by_q_src[aid]["paper_no"],
            })
    C.write_jsonl(C.CANDIDATES_DIR / "tier-b-review.jsonl", tier_b_rows)
    for m in matters:
        C.write_json(C.CANDIDATES_DIR / "matters" / f"{m['benchmark_matter_id']}.json", m)

    action = collections.Counter(c["candidate_action"] for c in classifications)
    funnel = {
        "status": "unverified",
        "generated": C.utc_now(),
        "inputs": {
            "atomic_questions": {"path": C.rel(C.ATOMIC_QUESTIONS), "sha256": C.sha256_file(C.ATOMIC_QUESTIONS), "rows": len(questions)},
            "atomic_classifications": {"path": C.rel(C.ATOMIC_CLASSIFICATIONS), "sha256": C.sha256_file(C.ATOMIC_CLASSIFICATIONS), "rows": len(classifications)},
        },
        "classification_actions": dict(action),
        "candidate_predicate": {"candidate_action": sorted(CANDIDATE_ACTIONS)},
        "tier_a_predicate": TIER_A,
        "funnel": {
            "source_questions": len(questions),
            "keep_enrich_candidates": len(flat) + sum(len(r["atomic_ids"]) for r in quarantined),
            "quarantined_background_boundary_questions": sum(len(r["atomic_ids"]) for r in quarantined),
            "quarantined_matters": len(quarantined),
            "buildable_candidates": len(flat),
            "candidate_matters": len(matters),
            "tier_a_questions": len(tier_a_rows),
            "tier_a_matters": sum(m["matter_tier"] == "A" for m in matters),
            "tier_b_questions": len(tier_b_rows),
            "matters_with_only_tier_b": sum(m["matter_tier"] == "B" for m in matters),
        },
        "tier_a_by_action": dict(collections.Counter(r["candidate_action"] for r in tier_a_rows)),
        "tier_b_reasons": dict(collections.Counter(reason for r in tier_b_rows for reason in r["tier_b_reasons"])),
        "questions_per_matter": audit["questions_per_matter_distribution"],
        "questions_by_paper": audit["questions_by_paper"],
        "background_conflicts": audit["background_conflicts"],
        "quarantined_records": audit["quarantined_records"],
        "normalization_changes": len(audit["normalization_changes"]),
    }
    C.write_json(C.AUDITS_DIR / "candidate-funnel.json", funnel)
    C.write_json(C.AUDITS_DIR / "candidate-selection-audit.json", audit)
    print(funnel["funnel"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
