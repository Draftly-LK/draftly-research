"""Case-law rule extraction — orchestrator.

Two tracks (see case-law-extraction-plan.md):
  A (reported): deterministic Held-block extraction, no LLM (free).
  B (unreported / reported-without-Held): bounded LLM extraction, quote-validated,
    with cheap→strong escalation on low confidence / rejected quotes.

Resumable (per-case cache), idempotent (CSVs rebuilt from cache), rate-limited,
and credit-guarded. Nothing is trusted: every rule is status=unverified.

Usage:
  python extract_case_rules.py --track A                 # free, all reported
  python extract_case_rules.py --track B --limit 25      # sample the LLM path
  python extract_case_rules.py --track all --escalate --max-llm-calls 1500
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

import config
import catalogue
import headnote as hn
import validate as V
import windowing
from llm_client import chat_json, usage_summary

# ---------------------------------------------------------------- prompts

SYS_EXTRACT = """You are extracting the legal RULE (ratio decidendi) from a Sri Lankan \
conveyancing judgment, for a citation database. Rules:
- Return ONLY a rule directly supported by a verbatim span you copy from the text into \
"supporting_quote". Copy the quote EXACTLY as it appears.
- "statement" is your one-sentence neutral paraphrase of that quote's rule.
- If the judgment establishes no general conveyancing rule (purely fact-specific, procedural, \
or you are unsure), return {"rule": null}. Abstaining is correct and expected for many cases.
- "statute_section": ONLY if the rule construes a specific statute, choose from the CANDIDATE \
STATUTES list by its source_id (e.g. "SRC001-s2"); else null. Never invent one.
- Do not use knowledge outside the provided text. Do not cite other cases.
Output JSON only, no prose."""

USER_EXTRACT = """CITATION: {citation}   COURT: {court}   YEAR: {year}
CANDIDATE STATUTES (choose statute_section only from these source_ids):
{catalogue}
STATUTES THIS CASE ALREADY CITES (strong prior):
{linked}

JUDGMENT EXTRACT:
\"\"\"{text}\"\"\"

Return JSON exactly:
{{"rule": {{"statement": "...", "supporting_quote": "<verbatim span from the extract>", \
"statute_section": "SRCxxx-sN or null", "scope": "ratio|obiter|fact-specific", \
"confidence": "high|medium|low"}}}}
OR
{{"rule": null}}"""

SYS_NORMALIZE = """You are a legal editor. Given the verbatim HELD passage of a Sri Lankan \
case, restate the legal rule(s) as neutral one-sentence statements. Do not add facts not in \
the passage. Output JSON only."""

USER_NORMALIZE = """HELD:
\"\"\"{held}\"\"\"
Return JSON: {{"rules": [{{"statement": "<one sentence>", "scope": "ratio|obiter|fact-specific"}}]}}"""

# ---------------------------------------------------------------- io helpers


def log(msg: str) -> None:
    print(msg, flush=True)
    with config.RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def load_cases() -> list[dict]:
    rows = [json.loads(l) for l in config.CASES.open(encoding="utf-8")]
    return [r for r in rows if str(r.get("conveyancing_match", "")).lower() in ("true", "1")]


def load_links() -> dict[str, list[str]]:
    m: dict[str, list[str]] = {}
    if not config.LINKS.exists():
        return m
    with config.LINKS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cid = r.get("case_id")
            sid = r.get("source_id", "")
            sec = r.get("section", "")
            if not cid or not sid:
                continue
            ref = f"{sid}-s{sec}" if sec else sid
            m.setdefault(cid, [])
            if ref not in m[cid]:
                m[cid].append(ref)
    return m


def read_text(case: dict) -> str:
    p = Path(case.get("text_path", ""))
    for cand in (config.ROOT / p, p):
        if cand.exists():
            return cand.read_text(encoding="utf-8", errors="ignore")
    return ""


def parse_meta(case: dict, text: str) -> dict:
    title = case.get("title", "")
    title = re.sub(r"\s*-\s*(NLR|SLR|Sri LR).*$", "", title, flags=re.I).strip(" .-")
    parties = title
    disp = ""
    tail = text[-4000:].lower()
    for pat, label in [(r"appeal is allowed|appeal.{0,20}allowed", "allowed"),
                       (r"appeal is dismissed|appeal.{0,20}dismissed", "dismissed"),
                       (r"application is dismissed", "dismissed"),
                       (r"set aside", "set-aside"), (r"remitted|sent back", "remitted"),
                       (r"affirmed|judgment.{0,20}affirmed", "affirmed")]:
        if re.search(pat, tail):
            disp = label
            break
    return {"case_id": case["case_id"], "citation": case.get("citation", ""),
            "court": case.get("court", ""), "year": case.get("year", ""),
            "reported": case.get("source") == "commonlii",
            "parties": parties, "disposition": disp}

# ---------------------------------------------------------------- tracks


def track_A(case: dict, text: str, normalize: bool, model: str) -> dict:
    got = hn.extract_headnote(text)
    if not got:
        return {"track": "A->B", "status": "no-headnote"}
    rules = []
    for holding in hn.split_holdings(got["held"]):
        stmt = holding
        if normalize:
            j = chat_json(SYS_NORMALIZE, USER_NORMALIZE.format(held=holding), model)
            if j and j.get("rules"):
                stmt = j["rules"][0].get("statement", holding)
        rules.append({"statement": re.sub(r"\s+", " ", stmt).strip(),
                      "supporting_quote": got["held"], "statute_section": "",
                      "section_status": "none", "scope": "ratio",
                      "confidence": "high", "method": "headnote"})
    return {"track": "A", "status": "ok", "model": model if normalize else "",
            "catchwords": got.get("catchwords", ""), "rules": rules}


def track_B(case: dict, text: str, links: list[str], model_cheap: str,
            model_strong: str, escalate: bool, budget) -> dict:
    window = windowing.build_window(text)
    user = USER_EXTRACT.format(
        citation=case.get("citation", ""), court=case.get("court", ""),
        year=case.get("year", ""), catalogue=catalogue.catalogue_lines(),
        linked=", ".join(links) if links else "(none recorded)", text=window)

    def _attempt(model):
        budget["calls"] += 1
        return chat_json(SYS_EXTRACT, user, model)

    if not budget["allow"]():
        return {"track": "B", "status": "budget-exhausted"}
    j = _attempt(model_cheap)
    used = model_cheap
    if not j:
        return {"track": "B", "status": "llm-error", "model": model_cheap}
    if j.get("rule") in (None, "null"):
        return {"track": "B", "status": "abstained", "model": model_cheap}

    ok, cleaned, why = V.validate_rule(j["rule"], text)
    # escalate on rejection or low confidence
    if escalate and (not ok or cleaned.get("confidence") == "low") and budget["allow"]():
        j2 = _attempt(model_strong)
        used = model_strong
        if j2 and j2.get("rule") not in (None, "null"):
            ok2, cleaned2, why2 = V.validate_rule(j2["rule"], text)
            if ok2:
                ok, cleaned, why = ok2, cleaned2, why2
    if not ok:
        return {"track": "B", "status": "reject:" + why, "model": used}
    cleaned["method"] = "llm-extract"
    return {"track": "B", "status": "ok", "model": used, "rules": [cleaned]}

# ---------------------------------------------------------------- orchestration


def process(case: dict, links_map, args, budget) -> dict:
    text = read_text(case)
    meta = parse_meta(case, text) if text else {"case_id": case["case_id"]}
    if not text:
        return {"case_id": case["case_id"], "status": "no-text", "meta": meta, "rules": []}

    reported = case.get("source") == "commonlii"
    want = args.track
    result = None
    if reported and want in ("A", "all"):
        result = track_A(case, text, args.normalize, args.model_cheap)
        if result.get("status") == "no-headnote" and want == "all":
            result = None  # fall through to B
    if result is None and want in ("B", "all"):
        result = track_B(case, text, links_map.get(case["case_id"], []),
                         args.model_cheap, args.model_strong, args.escalate, budget)
    if result is None:
        result = {"track": want, "status": "skipped"}

    result["case_id"] = case["case_id"]
    result["meta"] = meta
    result.setdefault("rules", [])
    # stamp shared fields onto each rule
    for i, ru in enumerate(result["rules"], 1):
        ru["rule_id"] = f"draftly-rule-{case['case_id']}-{i}"
        ru["case_id"] = case["case_id"]
        ru["citation"] = case.get("citation", "")
        ru["court"] = case.get("court", "")
        ru["year"] = case.get("year", "")
        ru["status"] = "unverified"
    return result


def rebuild_outputs() -> tuple[int, int, int]:
    rule_rows, meta_rows, reject_rows = [], [], []
    for cf in sorted(config.CACHE.glob("*.json")):
        rec = json.loads(cf.read_text(encoding="utf-8"))
        if rec.get("meta"):
            meta_rows.append(rec["meta"])
        if rec.get("rules"):
            rule_rows.extend(rec["rules"])
        else:
            reject_rows.append({"case_id": rec.get("case_id"), "track": rec.get("track", ""),
                                "status": rec.get("status", ""), "model": rec.get("model", "")})
    _write(config.RULES_CSV, ["rule_id", "case_id", "citation", "court", "year", "statement",
            "supporting_quote", "statute_section", "section_status", "scope", "confidence",
            "method", "status"], rule_rows)
    _write(config.META_CSV, ["case_id", "citation", "court", "year", "reported", "parties",
            "disposition"], meta_rows)
    _write(config.REJECTS_CSV, ["case_id", "track", "status", "model"], reject_rows)
    return len(rule_rows), len(meta_rows), len(reject_rows)


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["A", "B", "all"], default="all")
    ap.add_argument("--limit", type=int, default=0, help="max cases this run (0=all)")
    ap.add_argument("--source", choices=["commonlii", "official-courts", "all"], default="all")
    ap.add_argument("--escalate", action="store_true", help="retry hard cases on strong model")
    ap.add_argument("--normalize", action="store_true", help="LLM-normalize Track A headnotes")
    ap.add_argument("--model-cheap", default=config.MODEL_CHEAP)
    ap.add_argument("--model-strong", default=config.MODEL_STRONG)
    ap.add_argument("--max-llm-calls", type=int, default=200, help="credit guard (0=unlimited)")
    ap.add_argument("--force", action="store_true", help="ignore cache, recompute")
    args = ap.parse_args()

    cases = load_cases()
    if args.source != "all":
        cases = [c for c in cases if c.get("source") == args.source]
    links_map = load_links()
    budget = {"calls": 0, "max": args.max_llm_calls,
              "allow": lambda: args.max_llm_calls == 0 or budget["calls"] < args.max_llm_calls}

    log(f"[start] cases={len(cases)} track={args.track} source={args.source} "
        f"escalate={args.escalate} max_llm_calls={args.max_llm_calls}")
    done = 0
    for c in cases:
        if args.limit and done >= args.limit:
            break
        cache_f = config.CACHE / f"{c['case_id']}.json"
        if cache_f.exists() and not args.force:
            continue
        rec = process(c, links_map, args, budget)
        cache_f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        done += 1
        if done % 25 == 0:
            log(f"  processed {done} | llm_calls={budget['calls']}")
        time.sleep(config.DELAY_S if rec.get("track", "").startswith("B") and rec.get("model") else 0)

    rules, meta, rejects = rebuild_outputs()
    config.USAGE_JSON.write_text(json.dumps(usage_summary(), indent=2), encoding="utf-8")
    log(f"[done] new_processed={done} llm_calls={budget['calls']} | "
        f"rules={rules} meta={meta} rejects={rejects}")
    log(f"[usage] {json.dumps(usage_summary())}")
    print(f"OUTPUTS -> {config.OUT}")


if __name__ == "__main__":
    main()
