"""Validate one matter's legal-map.json against the schema and the corpus.

Checks (a pass means "internally consistent and traceable", never "legally
right"):

  * schema (data/evaluvation/statutory-qa-v1/schemas/legal-map.schema.json)
  * every provision.section_id exists in corpus/sections.jsonl and its act_id,
    section number and title agree with the corpus row
  * every relevant_excerpt is a verbatim substring of the corpus section body
    (whitespace and quote style normalised)
  * every provision id referenced by a question exists and is unique
  * indispensable / supporting / background sets are disjoint
  * a statute_only proposed_gold question has >= 1 indispensable provision and
    every rule claim cites >= 1 provision; conclusions and applications cite a
    provision or a scenario fact
  * hop count >= 1 when indispensable provisions exist
  * the answer cites no case law (regex on " v. ", "NLR", "SLR", "S.C.")
  * enrich questions carry enrichment.applied == true with >= 1 added fact;
    keep questions carry enrichment.applied == false
  * the matter's question ids match candidates/matters/<MID>.json Tier A ids
  * every question in the map is either proposed_gold, blocked or reserved

    uv run python scripts/statutory-qa/validate_legal_map.py M001 [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

CASE_RE = re.compile(r"(\b[A-Z][a-z]+ v\.? [A-Z][a-z]+\b|\bN\.?L\.?R\.?\b|\bS\.?L\.?R\.?\b|\bSri\s*L\.?R\b|\bC\.?L\.?W\b|\bAIR\b)")
_SECTIONS = None


def sections():
    global _SECTIONS
    if _SECTIONS is None:
        _SECTIONS = {s["section_id"]: s for s in C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")}
    return _SECTIONS


def validate(matter_id: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    path = C.MATTERS_DIR / matter_id / "legal-map.json"
    if not path.exists():
        return {"matter": matter_id, "ok": False, "errors": [f"missing {C.rel(path)}"], "warnings": []}
    try:
        lm = C.read_json(path)
    except json.JSONDecodeError as exc:
        return {"matter": matter_id, "ok": False, "errors": [f"invalid JSON: {exc}"], "warnings": []}
    schema = C.read_json(C.SCHEMAS_DIR / "legal-map.schema.json")
    for err in sorted(jsonschema.Draft202012Validator(schema).iter_errors(lm), key=lambda e: list(e.path)):
        errors.append(f"schema: {'/'.join(str(p) for p in err.path)}: {err.message[:200]}")
    if errors:
        return {"matter": matter_id, "ok": False, "errors": errors, "warnings": warnings}

    if lm["benchmark_matter_id"] != matter_id:
        errors.append(f"benchmark_matter_id {lm['benchmark_matter_id']} != {matter_id}")

    secs = sections()
    prov_ids = [p["provision_id"] for p in lm["provisions"]]
    if len(prov_ids) != len(set(prov_ids)):
        errors.append("duplicate provision_id")
    provs = {p["provision_id"]: p for p in lm["provisions"]}
    for p in lm["provisions"]:
        s = secs.get(p["section_id"])
        if s is None:
            errors.append(f"{p['provision_id']}: unknown section_id {p['section_id']}")
            continue
        if s["act_id"] != p["act_id"]:
            errors.append(f"{p['provision_id']}: act_id {p['act_id']} != corpus {s['act_id']}")
        if C.normalize_ws(p["section"]).casefold() != C.normalize_ws(s["section_number"]).casefold():
            errors.append(f"{p['provision_id']}: section {p['section']!r} != corpus {s['section_number']!r}")
        if not C.excerpt_in(p["relevant_excerpt"], s["body"]):
            errors.append(f"{p['provision_id']}: relevant_excerpt is not a verbatim substring of {p['section_id']}")
        if s["act_title"].casefold() not in p["formal_title"].casefold() and p["formal_title"].casefold() not in s["act_title"].casefold():
            warnings.append(f"{p['provision_id']}: formal_title {p['formal_title']!r} differs from corpus title {s['act_title']!r}")

    matter_file = C.CANDIDATES_DIR / "matters" / f"{matter_id}.json"
    tier_a_ids, actions = set(), {}
    if matter_file.exists():
        m = C.read_json(matter_file)
        for q in m["questions"]:
            actions[q["benchmark_question_id"]] = q["classification"]["candidate_action"]
            if q["tier"] == "A":
                tier_a_ids.add(q["benchmark_question_id"])
    qids = [q["benchmark_question_id"] for q in lm["questions"]]
    if len(qids) != len(set(qids)):
        errors.append("duplicate benchmark_question_id")
    if tier_a_ids and set(qids) != tier_a_ids:
        errors.append(f"question ids {sorted(qids)} != Tier A ids {sorted(tier_a_ids)}")

    used: set[str] = set()
    for q in lm["questions"]:
        qid = q["benchmark_question_id"]
        ind, sup, bg = set(q["indispensable_provision_ids"]), set(q["supporting_provision_ids"]), set(q["background_provision_ids"])
        for pid in ind | sup | bg:
            if pid not in provs:
                errors.append(f"{qid}: unknown provision id {pid}")
        used |= ind | sup | bg
        if ind & sup or ind & bg or sup & bg:
            errors.append(f"{qid}: provision role sets overlap")
        if q["research_status"] == "proposed_gold":
            if q["authority_requirement"] != "statute_only":
                errors.append(f"{qid}: proposed_gold but authority_requirement={q['authority_requirement']}")
            if not ind:
                errors.append(f"{qid}: proposed_gold with no indispensable provisions")
            if q["legal_hop_count"] < 1:
                errors.append(f"{qid}: hop count must be >= 1")
            if not q["answer_claims"]:
                errors.append(f"{qid}: no answer_claims")
            for role in ("rule", "conclusion"):
                if not any(c["claim_type"] == role for c in q["answer_claims"]):
                    warnings.append(f"{qid}: no {role} claim")
            ga = q["gold_answer_draft"]
            for k in ("issue", "rule", "application", "conclusion"):
                if len(ga[k].strip()) < 20:
                    errors.append(f"{qid}: gold_answer_draft.{k} too short")
            text = " ".join(ga.values())
            m = CASE_RE.search(text)
            if m:
                errors.append(f"{qid}: answer appears to cite case law ({m.group(0)!r})")
            cited = set()
            for c in q["answer_claims"]:
                cited |= set(c["supporting_provision_ids"])
                for pid in c["supporting_provision_ids"]:
                    if pid not in provs:
                        errors.append(f"{c['claim_id']}: unknown provision {pid}")
                if c["claim_type"] == "rule" and not c["supporting_provision_ids"]:
                    errors.append(f"{c['claim_id']}: rule claim without supporting provision")
                if c["claim_type"] in ("application", "conclusion") and not c["supporting_provision_ids"] and not c["supporting_fact_ids"]:
                    errors.append(f"{c['claim_id']}: {c['claim_type']} claim with neither provision nor fact support")
            missing = ind - cited
            if missing:
                warnings.append(f"{qid}: indispensable provisions never cited by a claim: {sorted(missing)}")
        elif q["research_status"] in ("reserved",) and q["authority_requirement"] == "statute_only":
            errors.append(f"{qid}: reserved but statute_only")
        elif q["research_status"] != "proposed_gold" and not q["block_reason"]:
            errors.append(f"{qid}: {q['research_status']} without block_reason")
        for e in q["reasoning_edges"]:
            for pid in (e["from_provision_id"], e["to_provision_id"]):
                if pid not in provs:
                    errors.append(f"{qid}: reasoning edge references unknown {pid}")
        action = actions.get(qid)
        enr = q["enrichment"]
        if action == "enrich" and q["research_status"] == "proposed_gold":
            if not enr["applied"] or not enr["added_facts"] or not enr["enriched_background"]:
                errors.append(f"{qid}: enrich question must carry applied enrichment with added facts")
        if action == "keep" and enr["applied"]:
            warnings.append(f"{qid}: keep question carries enrichment")
        for f in enr["added_facts"]:
            for pid in f["activates_provision_ids"]:
                if pid not in provs:
                    errors.append(f"{f['fact_id']}: unknown provision {pid}")
        ref_year = int(lm["matter_reference_date"][:4])
        for pid in ind:
            p = provs.get(pid)
            if p and p["applicable_to_matter_date"] is False:
                errors.append(f"{qid}: indispensable {pid} marked not applicable to matter date")
            if p:
                s = secs.get(p["section_id"])
                if s and s.get("in_force_from_year") and s["in_force_from_year"] > ref_year:
                    warnings.append(f"{qid}: {pid} ({p['section_id']}) in force from {s['in_force_from_year']} but matter date is {lm['matter_reference_date']}")
    unused = set(provs) - used
    if unused:
        warnings.append(f"provisions not used by any question: {sorted(unused)}")
    return {"matter": matter_id, "ok": not errors, "errors": errors, "warnings": warnings,
            "questions": len(lm["questions"]),
            "proposed_gold": sum(q["research_status"] == "proposed_gold" for q in lm["questions"]),
            "provisions": len(provs)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("matter_ids", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rc = 0
    for mid in args.matter_ids:
        r = validate(mid)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            print(f"{mid}: {'OK' if r['ok'] else 'FAIL'}  errors={len(r['errors'])} warnings={len(r['warnings'])}")
            for e in r["errors"]:
                print("  ERROR", e)
            for w in r["warnings"]:
                print("  warn ", w)
        rc |= 0 if r["ok"] else 1
    return rc


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
