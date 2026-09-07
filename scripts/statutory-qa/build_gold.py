"""Merge per-matter legal maps into the benchmark files.

Reads annotations/matters/<MID>/legal-map.json (+ verification-report.json),
validates each, and writes:

  annotations/proposed-gold.jsonl         every annotated question, any status
  annotations/verified-provisions.jsonl   every provision with its decision
  reserved/mixed-statute-case.jsonl, case-only.jsonl, unclear-authority.jsonl
  benchmark/private-gold.jsonl            eligible questions with gold labels
  benchmark/public-input.jsonl            retriever input only (no gold)
  review/lawyer-review-status.jsonl       one pending approval form per question
  review/lawyer-review-packets/<MID>.md
  audits/validation-report.json, authority-coverage.json,
  audits/annotation-disagreements.jsonl, audits/gold-funnel.json

Eligibility for private-gold (all must hold):
  research_status == proposed_gold, authority_requirement == statute_only,
  the matter has a completed verification pass, every indispensable provision
  is `verified` or `partially_verified`, and the map validates.
Lawyer validation is NOT among the conditions: every row is written with
lawyer_validation_status = "pending" and the benchmark is labelled
proposed_gold everywhere.

    uv run python scripts/statutory-qa/build_gold.py [--allow-unverified]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402
import validate_legal_map as V  # noqa: E402

OK_STATUS = {"verified", "partially_verified"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--allow-unverified", action="store_true", help="admit proposed provisions without a verification pass (smoke tests only)")
    args = ap.parse_args(argv)

    secs = V.sections()
    matters = {m["benchmark_matter_id"]: m for m in C.read_jsonl(C.CANDIDATES_DIR / "matters.jsonl")}
    reports, gold, public, proposed, provisions_out, reserved = [], [], [], [], [], collections.defaultdict(list)
    gold_ext, public_ext = [], []   # extended: adds needs_legal_review questions whose indispensable provisions verified
    disagreements, review_status = [], []
    funnel = collections.Counter()
    excluded = []

    for mdir in sorted(C.MATTERS_DIR.glob("M*")):
        mid = mdir.name
        if not (mdir / "legal-map.json").exists():
            continue
        rep = V.validate(mid)
        reports.append(rep)
        funnel["matters_annotated"] += 1
        if not rep["ok"]:
            excluded.append({"matter": mid, "reason": "validation_failed", "errors": rep["errors"][:5]})
            continue
        lm = C.read_json(mdir / "legal-map.json")
        vr = C.read_json(mdir / "verification-report.json") if (mdir / "verification-report.json").exists() else None
        verified_pass = bool(lm["produced_by"].get("verification_completed")) and vr is not None
        m = matters[mid]
        mq = {q["benchmark_question_id"]: q for q in m["questions"]}
        provs = {p["provision_id"]: p for p in lm["provisions"]}
        for p in lm["provisions"]:
            provisions_out.append({"benchmark_matter_id": mid, **p, "verified_pass": verified_pass})
        if vr:
            for d in vr.get("disagreements", []):
                disagreements.append({"benchmark_matter_id": mid, **d})
        for q in lm["questions"]:
            qid = q["benchmark_question_id"]
            funnel["questions_annotated"] += 1
            src = mq[qid]
            row = {
                "benchmark_question_id": qid, "benchmark_matter_id": mid, "atomic_id": src["atomic_id"],
                "paper_no": m["paper_no"], "exam_session": m["exam_session"],
                "matter_reference_date": lm["matter_reference_date"],
                "candidate_action": src["classification"]["candidate_action"],
                "authority_requirement": q["authority_requirement"],
                "research_status": q["research_status"], "block_reason": q["block_reason"],
                "verified_pass": verified_pass,
            }
            proposed.append({**row, "legal_map": q})
            funnel[f"authority_{q['authority_requirement']}"] += 1
            if q["authority_requirement"] == "mixed_statute_and_case":
                reserved["mixed-statute-case"].append({**row, "legal_issues": q["legal_issues"], "reason": q["authority_requirement_reason"]})
            elif q["authority_requirement"] == "case_only":
                reserved["case-only"].append({**row, "legal_issues": q["legal_issues"], "reason": q["authority_requirement_reason"]})
            elif q["authority_requirement"] == "unclear":
                reserved["unclear-authority"].append({**row, "legal_issues": q["legal_issues"], "reason": q["authority_requirement_reason"]})
            extended_only = False
            if q["research_status"] == "needs_legal_review" and q["authority_requirement"] == "statute_only" and verified_pass:
                ind_lr = [provs[p] for p in q["indispensable_provision_ids"]]
                if ind_lr and all(p["verification_status"] in OK_STATUS for p in ind_lr):
                    extended_only = True
                    funnel["extended_needs_legal_review_with_verified_provisions"] += 1
            if not extended_only and (q["research_status"] != "proposed_gold" or q["authority_requirement"] != "statute_only"):
                excluded.append({"question": qid, "reason": q["research_status"], "detail": q["block_reason"]})
                continue
            if not extended_only:
                funnel["statute_only_proposed_gold"] += 1
            ind = [provs[p] for p in q["indispensable_provision_ids"]]
            statuses = {p["verification_status"] for p in ind}
            if not verified_pass and not args.allow_unverified:
                excluded.append({"question": qid, "reason": "no_verification_pass"})
                continue
            bad = [p["provision_id"] for p in ind if p["verification_status"] not in OK_STATUS and not (args.allow_unverified and p["verification_status"] == "proposed")]
            if bad:
                excluded.append({"question": qid, "reason": "indispensable_not_verified", "detail": bad})
                funnel["excluded_indispensable_not_verified"] += 1
                continue
            if not extended_only:
                funnel["eligible"] += 1
            ind_secs = sorted({p["section_id"] for p in ind})
            sup_secs = sorted({provs[p]["section_id"] for p in q["supporting_provision_ids"]} - set(ind_secs))
            bg_secs = sorted({provs[p]["section_id"] for p in q["background_provision_ids"]} - set(ind_secs) - set(sup_secs))
            acts = sorted({secs[s]["act_id"] for s in ind_secs})
            principal_acts = sorted({(C.read_json if False else (lambda a: a))(secs[s]["act_id"]) for s in ind_secs})
            enr = q["enrichment"]
            background = enr["enriched_background"] if enr["applied"] and enr["enriched_background"] else src["effective_background_normalized"]
            target_gold, target_pub = (gold_ext, public_ext) if extended_only else (gold, public)
            target_gold.append({
                **row,
                "legal_hop_count": q["legal_hop_count"],
                "indispensable_section_ids": ind_secs,
                "supporting_section_ids": sup_secs,
                "background_section_ids": bg_secs,
                "gold_act_ids": acts,
                "n_indispensable_sections": len(ind_secs),
                "indispensable_provisions": ind,
                "supporting_provisions": [provs[p] for p in q["supporting_provision_ids"]],
                "reasoning_edges": q["reasoning_edges"],
                "legal_issues": q["legal_issues"],
                "gold_answer_draft": q["gold_answer_draft"],
                "answer_claims": q["answer_claims"],
                "enrichment": enr,
                "indispensable_verification": sorted(statuses),
                "lawyer_validation_status": "pending",
                "status": "needs_legal_review_provisions_verified" if extended_only else "proposed_gold_unverified_by_lawyer",
            })
            target_pub.append({
                "benchmark_question_id": qid, "benchmark_matter_id": mid,
                "paper_no": m["paper_no"], "exam_session": m["exam_session"],
                "matter_reference_date": lm["matter_reference_date"],
                "background": background,
                "question": src["question_normalized"],
                "enriched": bool(enr["applied"]),
            })
            if extended_only:
                continue
            review_status.append({
                "benchmark_question_id": qid, "benchmark_matter_id": mid,
                "reviewer_id": None, "review_date": None,
                "background_approved": False, "enrichment_approved": False, "issues_approved": False,
                "provisions_approved": False, "gold_answer_approved": False,
                "required_corrections": [], "overall_status": "pending",
            })

    for rep in reports:
        pass
    C.write_jsonl(C.ANNOTATIONS_DIR / "proposed-gold.jsonl", proposed)
    C.write_jsonl(C.ANNOTATIONS_DIR / "verified-provisions.jsonl", provisions_out)
    for name in ("mixed-statute-case", "case-only", "unclear-authority"):
        C.write_jsonl(C.RESERVED_DIR / f"{name}.jsonl", reserved.get(name, []))
    C.write_jsonl(C.BENCHMARK_DIR / "private-gold.jsonl", gold)
    C.write_jsonl(C.BENCHMARK_DIR / "public-input.jsonl", public)
    # extended = main + needs_legal_review questions with verified indispensable provisions
    C.write_jsonl(C.BENCHMARK_DIR / "private-gold-extended.jsonl", gold + gold_ext)
    C.write_jsonl(C.BENCHMARK_DIR / "public-input-extended.jsonl", public + public_ext)
    C.write_jsonl(C.REVIEW_DIR / "lawyer-review-status.jsonl", review_status)
    C.write_jsonl(C.AUDITS_DIR / "annotation-disagreements.jsonl", disagreements)
    write_review_packets(gold, proposed, matters)

    gold_matters = {g["benchmark_matter_id"] for g in gold}
    acts_counter = collections.Counter(a for g in gold for a in g["gold_act_ids"])
    coverage = {
        "status": "proposed_gold, lawyer validation pending",
        "generated": C.utc_now(),
        "gold_questions": len(gold),
        "gold_matters": len(gold_matters),
        "statutes_represented": {a: {"title": next(s["act_title"] for s in secs.values() if s["act_id"] == a), "questions": n} for a, n in acts_counter.most_common()},
        "n_statutes_represented": len(acts_counter),
        "indispensable_sections_distinct": len({s for g in gold for s in g["indispensable_section_ids"]}),
        "indispensable_sections_per_question": dict(collections.Counter(g["n_indispensable_sections"] for g in gold)),
        "hop_count_distribution": dict(collections.Counter(g["legal_hop_count"] for g in gold)),
        "keep_vs_enrich": dict(collections.Counter(g["candidate_action"] for g in gold)),
        "acts_per_question": dict(collections.Counter(len(g["gold_act_ids"]) for g in gold)),
        "indispensable_verification_statuses": dict(collections.Counter(s for g in gold for s in g["indispensable_verification"])),
        "questions_by_paper": dict(collections.Counter(g["paper_no"] for g in gold)),
    }
    C.write_json(C.AUDITS_DIR / "authority-coverage.json", coverage)
    C.write_json(C.AUDITS_DIR / "validation-report.json", {"generated": C.utc_now(), "matters": reports,
                                                           "ok": sum(r["ok"] for r in reports), "failed": sum(not r["ok"] for r in reports)})
    cf = C.read_json(C.AUDITS_DIR / "candidate-funnel.json")["funnel"] if (C.AUDITS_DIR / "candidate-funnel.json").exists() else {}
    C.write_json(C.AUDITS_DIR / "gold-funnel.json", {
        "generated": C.utc_now(),
        "candidate_funnel": cf,
        "annotation": dict(funnel),
        "eligible_gold_questions": len(gold),
        "eligible_gold_matters": len(gold_matters),
        "extended_gold_questions": len(gold) + len(gold_ext),
        "extended_gold_matters": len({g["benchmark_matter_id"] for g in gold + gold_ext}),
        "reserved": {k: len(v) for k, v in reserved.items()},
        "excluded": excluded,
        "lawyer_approved": 0,
        "allow_unverified": args.allow_unverified,
    })
    print({"annotated_matters": funnel["matters_annotated"], "annotated_questions": funnel["questions_annotated"],
           "eligible_gold": len(gold), "gold_matters": len(gold_matters), "extended_gold": len(gold) + len(gold_ext), "reserved": {k: len(v) for k, v in reserved.items()},
           "validation_failed": sum(not r["ok"] for r in reports)})
    return 0


def write_review_packets(gold, proposed, matters) -> None:
    by_m = collections.defaultdict(list)
    for g in gold:
        by_m[g["benchmark_matter_id"]].append(g)
    out_dir = C.REVIEW_DIR / "lawyer-review-packets"
    for mid, rows in sorted(by_m.items()):
        m = matters[mid]
        lines = [f"# Lawyer review packet: {mid}", "",
                 "Status: proposed gold, generated by research and verification agents. Nothing here is lawyer validated.", "",
                 f"Exam session: {m['exam_session']} (matter reference date {rows[0]['matter_reference_date']})", "",
                 "## Original background", "", m["matter_background"]["normalized"] or "(question-specific context only)", ""]
        for g in rows:
            lines += [f"## {g['benchmark_question_id']} ({g['candidate_action']}, hop count {g['legal_hop_count']})", "",
                      "### Question", "", next(q["question_normalized"] for q in m["questions"] if q["benchmark_question_id"] == g["benchmark_question_id"]), ""]
            if g["enrichment"]["applied"]:
                lines += ["### Enriched background", "", g["enrichment"]["enriched_background"] or "", "", "### Added facts", ""]
                for f in g["enrichment"]["added_facts"]:
                    lines.append(f"- {f['fact_id']} ({f['origin']}): {f['fact']} Reason: {f['reason']} Counterfactual: {f['counterfactual_effect']}")
                lines.append("")
            lines += ["### Legal issues", ""] + [f"- {i['issue_id']}: {i['issue']}" for i in g["legal_issues"]] + [""]
            lines += ["### Indispensable provisions", ""]
            for p in g["indispensable_provisions"]:
                lines.append(f"- {p['provision_id']} {p['formal_title']} {p['number_and_year']} s.{p['section']}{'(' + p['subsection'] + ')' if p['subsection'] else ''} [{p['verification_status']}] corpus `{p['section_id']}`")
                lines.append(f"  Excerpt: \"{p['relevant_excerpt']}\"")
                lines.append(f"  Why: {p['why_relevant']} Temporal: {p['temporal_note']}")
            if g["supporting_provisions"]:
                lines += ["", "### Supporting provisions", ""]
                for p in g["supporting_provisions"]:
                    lines.append(f"- {p['provision_id']} {p['formal_title']} s.{p['section']} [{p['verification_status']}] `{p['section_id']}`")
            lines += ["", "### Draft answer", ""]
            for k in ("issue", "rule", "application", "conclusion"):
                lines += [f"{k.capitalize()}: {g['gold_answer_draft'][k]}", ""]
            lines += ["### Claim to provision matrix", "", "| claim | type | provisions | facts | strength | status |", "| --- | --- | --- | --- | --- | --- |"]
            for c in g["answer_claims"]:
                lines.append(f"| {c['claim_id']} {c['claim_text'][:90]} | {c['claim_type']} | {', '.join(c['supporting_provision_ids'])} | {', '.join(c['supporting_fact_ids'])} | {c['support_strength']} | {c['verification_status']} |")
            lines += ["", "### Approval form", "", "```json", '{"reviewer_id": null, "review_date": null, "background_approved": false, "enrichment_approved": false, "issues_approved": false, "provisions_approved": false, "gold_answer_approved": false, "required_corrections": [], "overall_status": "pending"}', "```", ""]
        C.write_text(out_dir / f"{mid}.md", "\n".join(lines))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
