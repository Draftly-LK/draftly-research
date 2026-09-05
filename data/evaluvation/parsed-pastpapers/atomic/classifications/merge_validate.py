"""Merge per-paper classification JSONL files, validate against the rubric, and
write atomic-classifications.jsonl + a summary. status=unverified."""
import json, sys, glob, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ATOMIC = os.path.dirname(HERE)
ALLOWED_SRC = {"shared", "group", "prior", "local"}
ALLOWED_DEP = {"required", "partial", "none", "unclear"}
ALLOWED_RICH = {"detailed", "minimal", "none", "unclear"}
ALLOWED_EQ = {"clean", "review", "malformed", "unclear"}
ALLOWED_ACT = {"keep", "enrich", "drop_candidate", "repair", "review"}
ALLOWED_MFT = {"party_identity","party_legal_capacity","property_identity","property_location",
  "instrument_type","instrument_date","registration_status","transaction_sequence",
  "consideration_or_value","default_or_breach","existing_encumbrance","relevant_document",
  "relationship_between_parties","applicable_time","other"}

def expected_action(dep, rich, eq):
    if eq == "malformed": return "repair"
    if "unclear" in (dep, rich, eq): return "review"
    if dep in ("required","partial") and rich == "detailed": return "keep"
    if dep in ("required","partial") and rich == "minimal": return "enrich"
    if dep == "none" and rich == "none": return "drop_candidate"
    return "review"

src = {}
order = []
for l in open(os.path.join(ATOMIC, "atomic-questions.jsonl"), encoding="utf-8"):
    r = json.loads(l); src[r["atomic_id"]] = r; order.append(r["atomic_id"])

out = {}
problems = []
for f in sorted(glob.glob(os.path.join(HERE, "paper-*.classified.jsonl"))):
    for i, l in enumerate(open(f, encoding="utf-8"), 1):
        l = l.strip()
        if not l: continue
        try: c = json.loads(l)
        except Exception as e:
            problems.append((f, i, f"bad json: {e}")); continue
        aid = c.get("atomic_id")
        if aid not in src: problems.append((f, i, f"unknown id {aid}")); continue
        if aid in out: problems.append((f, i, f"duplicate {aid}")); continue
        s = src[aid]
        bg_fields = [s.get("shared_background") or "", s.get("group_background") or "",
                     s.get("own_background") or "", s.get("group_lead") or "", s.get("stem") or ""] + list(s.get("prior_background") or [])
        pid = []
        if not set(c.get("context_sources", [])) <= ALLOWED_SRC: pid.append("bad context_sources")
        if c.get("context_dependency") not in ALLOWED_DEP: pid.append("bad dep")
        if c.get("scenario_richness") not in ALLOWED_RICH: pid.append("bad richness")
        if c.get("extraction_quality") not in ALLOWED_EQ: pid.append("bad eq")
        if c.get("candidate_action") not in ALLOWED_ACT: pid.append("bad action")
        exp = expected_action(c.get("context_dependency"), c.get("scenario_richness"), c.get("extraction_quality"))
        if c.get("candidate_action") != exp:
            pid.append(f"precedence: got {c.get('candidate_action')} expected {exp}"); c["candidate_action"] = exp; c.setdefault("flags", []).append("action_recomputed_by_precedence")
        if c["candidate_action"] != "enrich" and c.get("missing_fact_types"):
            pid.append("missing_fact_types on non-enrich"); c["missing_fact_types"] = []
        if not set(c.get("missing_fact_types") or []) <= ALLOWED_MFT: pid.append("bad missing_fact_types")
        # context_sources vs actual non-empty fields
        actual = set()
        if s.get("shared_background"): actual.add("shared")
        if s.get("group_background"): actual.add("group")
        if s.get("prior_background"): actual.add("prior")
        if s.get("own_background"): actual.add("local")
        extra = set(c.get("context_sources", [])) - actual
        if extra: pid.append(f"context_sources claims empty field(s) {sorted(extra)}")
        be = c.get("background_evidence")
        if be and not any(be in b for b in bg_fields): pid.append("background_evidence not verbatim")
        qe = c.get("question_evidence") or ""
        if not qe or qe not in (s.get("question") or ""):
            if qe not in (s.get("source_quote") or ""): pid.append("question_evidence not verbatim")
        dr = c.get("decision_reason") or ""
        if len(dr.split()) > 35: pid.append("decision_reason >35 words")
        conf = c.get("confidence")
        if not isinstance(conf, (int, float)) or not 0 <= conf <= 1: pid.append("bad confidence")
        for p in pid: problems.append((os.path.basename(f), aid, p))
        out[aid] = c

missing = [a for a in order if a not in out]
with open(os.path.join(ATOMIC, "atomic-classifications.jsonl"), "w", encoding="utf-8") as fh:
    for a in order:
        if a in out: fh.write(json.dumps(out[a], ensure_ascii=False) + "\n")

summary = {
  "status": "unverified",
  "total_source_items": len(order), "classified": len(out), "missing": missing,
  "candidate_action": dict(Counter(c["candidate_action"] for c in out.values())),
  "context_dependency": dict(Counter(c["context_dependency"] for c in out.values())),
  "scenario_richness": dict(Counter(c["scenario_richness"] for c in out.values())),
  "extraction_quality": dict(Counter(c["extraction_quality"] for c in out.values())),
  "low_confidence_lt_0.80": sum(1 for c in out.values() if (c.get("confidence") or 0) < 0.80),
  "per_paper_action": {},
  "validation_problem_count": len(problems),
}
pp = {}
for a, c in out.items():
    pp.setdefault(src[a]["paper_no"], Counter())[c["candidate_action"]] += 1
summary["per_paper_action"] = {str(k): dict(v) for k, v in sorted(pp.items())}
json.dump(summary, open(os.path.join(ATOMIC, "atomic-classifications.summary.json"), "w", encoding="utf-8"), indent=2)
with open(os.path.join(HERE, "validation-problems.txt"), "w", encoding="utf-8") as fh:
    for p in problems: fh.write("\t".join(map(str, p)) + "\n")
print(json.dumps(summary, indent=2))
print("problems:", len(problems))
for p in problems[:40]: print(p)
