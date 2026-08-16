"""Finalize the conveyancing case set into one clean CSV.

Takes data/supremecourt.lk/case_data.csv (Stage 1's deterministic output,
already carrying is_conveyancing/conveyancing_signal from
extract_supremecourt_deterministic.classify_conveyancing) and:

  1. Non-conveyancing cases (is_conveyancing=False): never touched by the LLM.
  2. "High-confidence" cases (conveyancing_signal=statute+keyword): trusted
     as conveyancing without an LLM confirmation call. If disposition and
     principle_statement are already both filled by regex, no LLM call at
     all -- 99 of 865 cases need nothing further.
  3. "Uncertain" cases (conveyancing_signal=keyword-only or statute-only):
     get exactly one LLM call that both confirms/rejects the classification
     AND backfills disposition/principle_statement in the same response --
     one call handles both jobs, not two.
  4. High-confidence cases still missing disposition or principle_statement
     get the same call, minus the classification question (already certain).

Every call uses the same compute-optimized window as extract_supremecourt_pdfs.py
(anchored on the disposition-phrase match when found, ~2.3K chars; falls back
to the naive head+tail window only when there's no anchor) -- never the whole
judgment. Grounded the same way: any supporting_quote must be a verbatim
substring of the full text (validate.py) or it's rejected, same as the
existing rule-extraction pipeline.

Output: rewrites data/supremecourt.lk/case_data.csv in place, filtered to
confirmed-conveyancing rows only, with LLM-backfilled fields applied. Also
writes data/supremecourt.lk/rejected_non_conveyancing.csv listing every case
removed and why, so the exclusion is auditable, not silent.

Resumable (per-case cache under output/supremecourt-lk/finalize-cache/).

Usage:
  python finalize_conveyancing_cases.py --limit 30       # smoke test
  python finalize_conveyancing_cases.py                  # full run
  python finalize_conveyancing_cases.py --rebuild-only    # 0 credits
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import config
import extract_case_rules as ecr
import extract_supremecourt_pdfs as sp

CASE_DATA_CSV = config.ROOT / "data" / "supremecourt.lk" / "case_data.csv"
REJECTED_CSV = config.ROOT / "data" / "supremecourt.lk" / "rejected_non_conveyancing.csv"

OUT = Path(__file__).resolve().parent / "output" / "supremecourt-lk"
FIN_CACHE = OUT / "finalize-cache"
RUN_LOG = OUT / "finalize-run.log"
FIN_CACHE.mkdir(parents=True, exist_ok=True)

SYS_PROMPT = """You are analyzing a Sri Lankan Supreme Court judgment for a conveyancing-law \
case database. Conveyancing law covers: deeds, notarial practice, prescription, servitudes, \
fideicommissum, partition, mortgages/hypothecs, gifts, wills, co-ownership, land registration, \
powers of attorney, state lands, and related property-transfer matters.

Tasks, in this order:
1. Decide whether this judgment's MAIN subject matter is a conveyancing-law dispute as defined \
above. A case that only mentions land/property incidentally (e.g. a criminal, labour, tax, or \
election-petition case where a witness happens to own land) is NOT conveyancing. If not \
conveyancing, set "is_conveyancing": false and set "disposition" to "" and "rule" to null -- do \
not do tasks 2 or 3.
2. If conveyancing, state the case's disposition using EXACTLY one of: allowed, dismissed, \
set-aside, remitted, affirmed, acquitted, relief-granted, leave-granted, leave-refused, refused, \
unclear.
3. If conveyancing, extract the legal RULE (ratio decidendi):
- Return ONLY a rule directly supported by a verbatim span you copy from the text into \
"supporting_quote". Copy the quote EXACTLY as it appears. The quote MUST be THIS court's own \
statement of the rule -- NOT a quotation of another case, NOT counsel's/party's submission.
- "statement" is your one-sentence neutral paraphrase of that quote's rule.
- Only capture the RATIO. If obiter or purely fact-specific/procedural, or you are unsure, \
return "rule": null. Abstaining is correct and expected for many cases.
- "statute_section": resolve to a CANDIDATE source_id ONLY when that EXACT statute is in the \
CANDIDATE STATUTES list. Otherwise null. NEVER guess.
Do not use knowledge outside the provided text. Output JSON only, no prose."""

USER_TEMPLATE = """CITATION: {citation}   COURT: {court}   YEAR: {year}
CANDIDATE STATUTES (resolve statute_section only to these source_ids):
{catalogue}

JUDGMENT EXTRACT:
\"\"\"{text}\"\"\"

Return ONLY a JSON object. Every field must be REAL content from the JUDGMENT EXTRACT above -- \
never copy this schema's example wording, it describes what goes in each field.

{{"is_conveyancing": true or false,
"disposition": "one of: allowed, dismissed, set-aside, remitted, affirmed, acquitted, relief-granted, leave-granted, leave-refused, refused, unclear -- or \\"\\" if not conveyancing",
"rule": {{"statement": "your one-sentence paraphrase", "supporting_quote": "verbatim span from the JUDGMENT EXTRACT", "statute_citation_verbatim": "statute+section as written, or null", "statute_section": "SRCxxx-sN if in the candidate list, else null", "scope": "ratio", "confidence": "high"}} or null}}"""

VALID_DISPOSITIONS = {"allowed", "dismissed", "set-aside", "remitted", "affirmed", "acquitted",
                       "relief-granted", "leave-granted", "leave-refused", "refused", "unclear"}


def log(msg: str) -> None:
    print(msg, flush=True)
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def load_case_data() -> list[dict]:
    with CASE_DATA_CSV.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def needs_llm(row: dict) -> bool:
    uncertain = row["conveyancing_signal"] in ("keyword-only", "statute-only")
    missing_field = row["disposition"] == "unclassified" or row["principle_statement"] == "not-stated"
    return uncertain or missing_field


def call_llm(row: dict, text: str, model: str, budget: dict) -> dict:
    window = sp.build_targeted_window(text)
    user = USER_TEMPLATE.format(
        citation=row["case_no"], court="Supreme Court", year=row["year"],
        catalogue=ecr.catalogue.catalogue_lines(), text=window,
    )
    if not budget["allow"]():
        return {"status": "budget-exhausted"}
    budget["calls"] += 1
    j = ecr.chat_json(SYS_PROMPT, user, model)
    if not j:
        return {"status": "llm-error"}

    is_conv = j.get("is_conveyancing")
    if is_conv is False:
        return {"status": "ok", "is_conveyancing": False}

    disposition = str(j.get("disposition", "")).strip().lower()
    if disposition not in VALID_DISPOSITIONS:
        disposition = ""

    rule = j.get("rule")
    cleaned_rule = None
    if rule and isinstance(rule, dict):
        ok, cleaned, _why = ecr.V.validate_rule(rule, text, allow_fuzzy=False)
        if ok:
            cleaned_rule = cleaned

    return {"status": "ok", "is_conveyancing": True, "disposition": disposition, "rule": cleaned_rule}


def apply_result(row: dict, result: dict) -> tuple[dict, str]:
    """Returns (updated_row, disposition: 'kept'|'dropped')."""
    row = dict(row)
    flags = row["extraction_flags"].split("; ") if row["extraction_flags"] != "none" else []
    flags = [f for f in flags if not f.startswith("llm=")]

    if result.get("status") != "ok":
        flags.append(f"llm={result.get('status')}")
        row["extraction_flags"] = "; ".join(flags) or "none"
        # LLM couldn't confirm an uncertain case -- don't silently keep it as conveyancing.
        was_uncertain = row["conveyancing_signal"] in ("keyword-only", "statute-only")
        return row, ("dropped" if was_uncertain else "kept")

    if result.get("is_conveyancing") is False:
        return row, "dropped"

    if row["disposition"] == "unclassified" and result.get("disposition"):
        row["disposition"] = result["disposition"]
        row["disposition_evidence"] = "llm-classified"
        flags.append("disposition=llm-filled")

    rule = result.get("rule")
    if row["principle_statement"] == "not-stated" and rule:
        row["principle_statement"] = rule["statement"]
        flags.append("principle_statement=llm-filled")
        if row["statutes_cited"] == "none" and rule.get("statute_section"):
            row["statutes_cited"] = rule["statute_section"]

    row["extraction_flags"] = "; ".join(flags) if flags else "none"
    return row, "kept"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-llm-calls", type=int, default=1000)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rebuild-only", action="store_true")
    args = ap.parse_args()

    rows = load_case_data()
    conveyancing = [r for r in rows if r["is_conveyancing"] == "True"]
    non_conveyancing = [r for r in rows if r["is_conveyancing"] != "True"]
    log(f"[start] total={len(rows)} conveyancing={len(conveyancing)} non_conveyancing={len(non_conveyancing)}")

    if not args.rebuild_only:
        to_process = [r for r in conveyancing if needs_llm(r)]
        log(f"[plan] {len(to_process)}/{len(conveyancing)} conveyancing case(s) need an LLM call "
            f"({len(conveyancing) - len(to_process)} already complete + high-confidence)")

        budget = {"calls": 0, "allow": lambda: budget["calls"] < args.max_llm_calls}
        done = 0
        for row in to_process:
            if args.limit and done >= args.limit:
                break
            cache_file = FIN_CACHE / f"{row['case_id']}.json"
            if cache_file.exists() and not args.force:
                continue
            text = sp.pdf_to_text({"filename": row["filename"], "year": row["year"]})
            result = call_llm(row, text, config.MODEL_CHEAP, budget) if text else {"status": "no-text"}
            cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            done += 1
            if done % 25 == 0:
                log(f"  processed {done}/{len(to_process)} | llm_calls={budget['calls']}")
            time.sleep(config.DELAY_S)
            if not budget["allow"]():
                log(f"[budget] reached {budget['calls']} calls; stopping")
                break
        log(f"[done] new_processed={done} llm_calls={budget['calls']}")

    # ---- rebuild: apply every cached result, split kept vs pending vs dropped.
    # Cases still awaiting an LLM call (pending) are written back into
    # case_data.csv unchanged -- NEVER silently dropped just because a run was
    # partial (--limit, interrupted, budget reached). Only a case with an
    # actual verdict (kept or dropped) leaves the "still in case_data.csv" set.
    kept_rows, pending_rows, dropped_rows = [], [], []
    for row in conveyancing:
        if not needs_llm(row):
            kept_rows.append(row)
            continue
        cache_file = FIN_CACHE / f"{row['case_id']}.json"
        if not cache_file.exists():
            pending_rows.append(row)
            continue
        result = json.loads(cache_file.read_text(encoding="utf-8"))
        updated, verdict = apply_result(row, result)
        (kept_rows if verdict == "kept" else dropped_rows).append(updated)

    for row in non_conveyancing:
        dropped_rows.append(row)

    fields = list(rows[0].keys())
    with CASE_DATA_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept_rows + pending_rows)

    with REJECTED_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dropped_rows)

    log(f"[rebuilt] case_data.csv kept={len(kept_rows)} pending={len(pending_rows)} "
        f"rejected_non_conveyancing.csv dropped={len(dropped_rows)}")
    print(f"case_data.csv: {len(kept_rows)} confirmed + {len(pending_rows)} still pending -> {CASE_DATA_CSV}")
    print(f"REJECTED: {len(dropped_rows)} case(s) -> {REJECTED_CSV}")
    if pending_rows:
        print(f"NOTE: {len(pending_rows)} case(s) still need an LLM call -- rerun to continue, "
              f"case_data.csv is not yet the final conveyancing-only set.")


if __name__ == "__main__":
    main()
