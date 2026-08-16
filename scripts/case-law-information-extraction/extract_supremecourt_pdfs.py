"""Extract legal rules from the downloaded Supreme Court judgment PDFs (SCLR).

These are raw judgments from supremecourt.lk (data/supremecourt.lk/SCLR/),
not edited law-report headnotes — there is no `Held:` block to parse
deterministically (Track A in extract_case_rules.py never applies here).
Reuses extract_case_rules.parse_meta / validate.py / catalogue.py /
windowing.py / llm_client.py — this script adds the PDF -> text ->
case-record ingestion path those don't have, plus two compute-optimizations
on top of a straight track_B call:

  1. Skips any case where extract_supremecourt_deterministic.py already found
     a genuine (marker-triggered) principle_statement — no LLM call needed to
     re-derive something already confidently known. (`--no-skip-regex-solved`
     disables this, for an apples-to-apples yield comparison.)
  2. For the rest, if a disposition phrase can be anchored (same regex
     extract_supremecourt_deterministic.classify_disposition uses), sends
     only the case caption plus a ~2.3K-char window around that anchor
     instead of the full head+tail slice — typically a few hundred tokens
     versus ~4K. Falls back to the existing naive head+tail window when there
     is no anchor, since shrinking blindly there would just cost recall.

Deterministic fields (citation, court, year, parties, judge, disposition) come
from data/supremecourt.lk/manifest.csv and a tail-regex over the judgment
text; only statement/supporting_quote/statute_section/scope/confidence are
LLM-derived and can legitimately come back empty (model abstained, or the
quote failed grounding).

Resumable (per-case cache under output/supremecourt-lk/cache/), idempotent
(CSVs rebuilt from cache), rate-limited, and credit-guarded — same posture as
extract_case_rules.py.

Usage:
  python extract_supremecourt_pdfs.py --limit 20                 # smoke test
  python extract_supremecourt_pdfs.py --year 2024 --year 2010    # spread sample
  python extract_supremecourt_pdfs.py --escalate --max-llm-calls 2000
  python extract_supremecourt_pdfs.py --rebuild-only             # 0 credits
  python report_supremecourt_accuracy.py                         # coverage report
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

import pypdfium2 as pdfium

import config
import extract_case_rules as ecr
import extract_supremecourt_deterministic as sd  # also adds scripts/ to sys.path (needed by sd itself)
from llm_client import usage_summary

# extract_case_rules.USER_EXTRACT shows the JSON schema with placeholder-style
# hints (e.g. "<verbatim span, THIS court's own words>"). Weaker/local models
# (observed: Ollama's llama3.1:8b) sometimes copy that placeholder text
# literally instead of substituting real content, which the grounding gate
# then rejects as quote-not-found on nearly every case. Patched here (module
# attribute only, not the source file) with a corrected template that shows
# an explicit "don't copy this" instruction and never shows a bracket-style
# placeholder that reads as valid quoted text.
ecr.USER_EXTRACT = """CITATION: {citation}   COURT: {court}   YEAR: {year}
CANDIDATE STATUTES (resolve statute_section only to these source_ids; if the statute is not here, \
leave statute_section null and record statute_citation_verbatim instead):
{catalogue}
STATUTES THIS CASE ALREADY CITES (strong prior):
{linked}

JUDGMENT EXTRACT:
\"\"\"{text}\"\"\"

Return ONLY a JSON object. Every field must be REAL content taken from the JUDGMENT EXTRACT \
above -- never output the example wording shown below, it is a description of what goes in \
each field, not text to copy.

{{"rule": {{"statement": "your one-sentence paraphrase of the rule",
"supporting_quote": "the exact sentence(s), copied character-for-character from the JUDGMENT EXTRACT above, that state the rule",
"statute_citation_verbatim": "the statute name and section exactly as written in the judgment, or null",
"statute_section": "a candidate source_id like SRC001-s2 if and only if that exact statute is in the CANDIDATE STATUTES list, else null",
"scope": "ratio", "confidence": "high"}}}}
If this judgment establishes no general rule (fact-specific, procedural, or you are unsure), \
return exactly: {{"rule": null}}"""

MANIFEST = config.ROOT / "data" / "supremecourt.lk" / "manifest.csv"
CASE_DATA_CSV = config.ROOT / "data" / "supremecourt.lk" / "case_data.csv"
PDF_ROOT = config.ROOT / "data" / "supremecourt.lk"

OUT = Path(__file__).resolve().parent / "output" / "supremecourt-lk"
CACHE = OUT / "cache"
TEXT_CACHE = OUT / "text-cache"
RULES_CSV = OUT / "rules.csv"
META_CSV = OUT / "case_meta.csv"
REJECTS_CSV = OUT / "extract-rejects.csv"
USAGE_JSON = OUT / "usage.json"
RUN_LOG = OUT / "run.log"

for d in (OUT, CACHE, TEXT_CACHE):
    d.mkdir(parents=True, exist_ok=True)

RULE_FIELDS = ecr.FIELDS
META_FIELDS = ["case_id", "citation", "court", "year", "reported", "parties",
               "judge", "disposition"]


def log(msg: str) -> None:
    print(msg, flush=True)
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def load_manifest_rows(source: str = "SCLR") -> list[dict]:
    with MANIFEST.open(encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh)
                if row.get("source") == source and row.get("status") == "ok"]


def load_regex_solved_filenames() -> set[str]:
    """Cases where the deterministic pass (extract_supremecourt_deterministic.py)
    already found a genuine, marker-triggered principle statement. No LLM call
    needed for these -- calling one anyway would just be spending compute to
    re-derive something already confidently known."""
    if not CASE_DATA_CSV.exists():
        return set()
    with CASE_DATA_CSV.open(encoding="utf-8") as fh:
        return {row["filename"] for row in csv.DictReader(fh)
                if row.get("principle_statement", "not-stated") != "not-stated"}


_CONVEYANCING_MAP: dict[str, bool] | None = None


def load_conveyancing_map() -> dict[str, bool]:
    """filename -> is_conveyancing, from case_data.csv's own classifier
    (extract_supremecourt_deterministic.classify_conveyancing: substantive
    statute citation OR keyword threshold over the full text -- see that
    module for why each half is defined the way it is). Loaded once and
    reused, since Stage 1 already computed this for every case; the LLM
    pass shouldn't need to re-derive it."""
    global _CONVEYANCING_MAP
    if _CONVEYANCING_MAP is None:
        _CONVEYANCING_MAP = {}
        if CASE_DATA_CSV.exists():
            with CASE_DATA_CSV.open(encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    _CONVEYANCING_MAP[row["filename"]] = row.get("is_conveyancing") == "True"
    return _CONVEYANCING_MAP


def is_conveyancing(filename: str) -> bool:
    return load_conveyancing_map().get(filename, False)


def find_disposition_anchor(text: str) -> tuple[int, int] | None:
    """Absolute (start, end) span of whatever disposition pattern
    extract_supremecourt_deterministic.classify_disposition would match, or
    None if nothing matched (mirrors that function's own tail window so the
    two stay consistent)."""
    tail_len = 6000
    tail = text[-tail_len:]
    offset = len(text) - len(tail)
    tail_lower = tail.lower()
    for pat, _label in sd.DISPOSITION_PATTERNS:
        m = re.search(pat, tail_lower)
        if m:
            return offset + m.start(), offset + m.end()
    return None


def build_targeted_window(text: str) -> str:
    """Compute-optimized window: if the deterministic pass can anchor on a
    disposition phrase, send only the caption (~900 chars, for case context)
    plus a tight span around that anchor (~2.3K chars) -- typically a few
    hundred tokens versus the ~4K-token naive head+tail window. Falls back to
    the existing naive window when there's no anchor, since in that case we
    genuinely don't know where in the judgment the rule sits and shrinking
    blindly would just cost recall."""
    anchor = find_disposition_anchor(text)
    if anchor is None:
        return ecr._naive_window(text)  # noqa: SLF001 -- deliberate reuse, not a private-API violation across packages
    start, end = anchor
    lo = max(0, start - 1800)
    hi = min(len(text), end + 700)
    head = text[:900]
    return head + "\n\n[...]\n\n" + text[lo:hi]


def track_b_windowed(case: dict, full_text: str, window_text: str, model_cheap: str,
                     model_strong: str, escalate: bool, budget, allow_fuzzy: bool = False) -> dict:
    """Same call/validate/escalate shape as extract_case_rules.track_B, but
    takes a pre-built window instead of deriving one from the full text --
    needed so build_targeted_window's smaller, anchored window is what
    actually gets sent, not track_B's own head+tail slice."""
    user = ecr.USER_EXTRACT.format(
        citation=case.get("citation", ""), court=case.get("court", ""),
        year=case.get("year", ""), catalogue=ecr.catalogue.catalogue_lines(),
        linked="(none recorded)", text=window_text,
    )

    def _attempt(model):
        budget["calls"] += 1
        return ecr.chat_json(ecr.SYS_EXTRACT, user, model)

    if not budget["allow"]():
        return {"track": "B", "status": "budget-exhausted"}
    j = _attempt(model_cheap)
    used = model_cheap
    if not j:
        return {"track": "B", "status": "llm-error", "model": model_cheap}
    if j.get("rule") in (None, "null"):
        return {"track": "B", "status": "abstained", "model": model_cheap}

    ok, cleaned, why = ecr.V.validate_rule(j["rule"], full_text, allow_fuzzy=allow_fuzzy)
    if escalate and (not ok or cleaned.get("confidence") != "high") and budget["allow"]():
        j2 = _attempt(model_strong)
        used = model_strong
        if j2 and j2.get("rule") not in (None, "null"):
            ok2, cleaned2, why2 = ecr.V.validate_rule(j2["rule"], full_text, allow_fuzzy=allow_fuzzy)
            if ok2 and (not ok or cleaned2.get("confidence") == "high"):
                ok, cleaned, why = ok2, cleaned2, why2
    if not ok:
        return {"track": "B", "status": "reject:" + why, "model": used, "rejected_rule": j.get("rule")}
    cleaned["method"] = "llm-extract"
    return {"track": "B", "status": "ok", "model": used, "rules": [cleaned]}


def case_id_for(row: dict) -> str:
    return f"sc-{row['year']}-{Path(row['filename']).stem}"


def pdf_to_text(row: dict) -> str:
    cache_file = TEXT_CACHE / (row["filename"] + ".txt")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="ignore")
    pdf_path = PDF_ROOT / "SCLR" / row["year"] / row["filename"]
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
        text = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
    except Exception as exc:  # noqa: BLE001
        log(f"  [warn] pdf parse {pdf_path}: {exc}")
        return ""
    cache_file.write_text(text, encoding="utf-8")
    return text


def build_case(row: dict) -> dict:
    return {
        "case_id": case_id_for(row),
        "citation": row["case_no"],
        "court": "Supreme Court",
        "year": row["year"],
        "title": row["parties"],
        "source": "supremecourt.lk",
    }


def process(row: dict, args, budget) -> dict:
    case = build_case(row)
    text = pdf_to_text(row)
    if not text:
        return {"case_id": case["case_id"], "status": "no-text", "meta": {}, "rules": []}

    meta = ecr.parse_meta(case, text)
    meta["parties"] = row["parties"]
    meta["judge"] = row["judge"]
    meta["reported"] = False

    if not args.skip_conveyancing_filter and not is_conveyancing(row["filename"]):
        # No LLM call: this case never had a shot at the conveyancing corpus in
        # the first place, so spending the expensive step on it is wasted compute.
        return {"case_id": case["case_id"], "status": "skipped-not-conveyancing", "meta": meta, "rules": []}

    if args.full_text:
        window = text[:config.FULL_TEXT_MAX_CHARS]
    elif args.window == "cue":
        window = ecr.windowing.build_window(text)
    else:
        window = build_targeted_window(text)  # anchored + small when possible, naive fallback otherwise
    result = track_b_windowed(
        case, text, window, args.model_cheap, args.model_strong, args.escalate,
        budget, allow_fuzzy=args.allow_fuzzy,
    )
    result["case_id"] = case["case_id"]
    result["meta"] = meta
    result.setdefault("rules", [])
    for i, rule in enumerate(result["rules"], 1):
        rule["rule_id"] = f"draftly-sc-rule-{case['case_id']}-{i}"
        rule["case_id"] = case["case_id"]
        rule["citation"] = case["citation"]
        rule["court"] = case["court"]
        rule["year"] = case["year"]
        rule["status"] = "unverified"
    return result


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rebuild_outputs() -> dict:
    # case_id -> filename, so a cache record (which only stores case_id) can be
    # matched back to its cached judgment text for the conveyancing check below.
    case_id_to_filename = {case_id_for(row): row["filename"] for row in load_manifest_rows("SCLR")}

    rule_rows, meta_rows, reject_rows = [], [], []
    excluded_non_conveyancing = 0
    for cache_file in sorted(CACHE.glob("*.json")):
        try:
            rec = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        case_id = rec.get("case_id", "")
        filename = case_id_to_filename.get(case_id)
        # Deliverable CSVs are conveyancing-only regardless of when a case was
        # processed -- some early cases predate the conveyancing filter existing.
        if filename and not is_conveyancing(filename):
            excluded_non_conveyancing += 1
            continue
        if rec.get("meta"):
            meta_rows.append({"case_id": rec["case_id"], **rec["meta"]})
        if rec.get("rules"):
            rule_rows.extend(rec["rules"])
        else:
            reject_rows.append({"case_id": rec.get("case_id"), "status": rec.get("status", ""),
                                "model": rec.get("model", "")})
    _write(RULES_CSV, RULE_FIELDS, rule_rows)
    _write(META_CSV, META_FIELDS, meta_rows)
    _write(REJECTS_CSV, ["case_id", "status", "model"], reject_rows)
    return {"rules": len(rule_rows), "meta": len(meta_rows), "rejects": len(reject_rows),
            "excluded_non_conveyancing": excluded_non_conveyancing}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="max cases this run (0=all)")
    ap.add_argument("--year", action="append", help="restrict to one or more years; repeatable")
    ap.add_argument("--escalate", action="store_true", help="retry hard cases on strong model")
    ap.add_argument("--model-cheap", default=config.MODEL_CHEAP)
    ap.add_argument("--model-strong", default=config.MODEL_STRONG)
    ap.add_argument("--max-llm-calls", type=int, default=200, help="credit guard (0=unlimited)")
    ap.add_argument("--force", action="store_true", help="ignore cache, recompute")
    ap.add_argument("--allow-fuzzy", action="store_true", help="accept near-verbatim quotes")
    ap.add_argument("--full-text", action="store_true", help="send the whole judgment (capped)")
    ap.add_argument("--window", default="naive", choices=("naive", "cue"),
                    help="fallback window strategy for cases with no disposition anchor")
    ap.add_argument("--no-skip-regex-solved", action="store_true",
                    help="also call the LLM on cases the deterministic pass already solved "
                    "(for A/B comparison; normally skipped to save compute)")
    ap.add_argument("--skip-conveyancing-filter", action="store_true",
                    help="also call the LLM on non-conveyancing cases (this corpus is scoped "
                    "to conveyancing; normally filtered out before the LLM step)")
    ap.add_argument("--rebuild-only", action="store_true", help="just rebuild CSVs from cache")
    args = ap.parse_args()

    if args.rebuild_only:
        out = rebuild_outputs()
        print(f"REBUILT {out} -> {OUT}")
        return

    rows = load_manifest_rows("SCLR")
    if args.year:
        wanted = set(args.year)
        rows = [r for r in rows if r["year"] in wanted]

    if not args.no_skip_regex_solved:
        solved = load_regex_solved_filenames()
        before = len(rows)
        rows = [r for r in rows if r["filename"] not in solved]
        log(f"[skip] {before - len(rows)} case(s) already have a regex-found principle_statement "
            f"(data/supremecourt.lk/case_data.csv) -- no LLM call needed for those")

    if not args.skip_conveyancing_filter:
        # Informational only -- the real per-case skip happens in process() (and is cached, so a
        # rerun doesn't redo this check); this just gives an upfront count of what's coming.
        conveyancing_n = sum(1 for r in rows if is_conveyancing(r["filename"]))
        log(f"[filter] {conveyancing_n}/{len(rows)} case(s) pass the conveyancing classifier "
            f"(data/supremecourt.lk/case_data.csv is_conveyancing: substantive statute citation "
            f"OR keyword threshold) -- only those will reach the LLM")

    budget = {"calls": 0, "max": args.max_llm_calls,
              "allow": lambda: args.max_llm_calls == 0 or budget["calls"] < args.max_llm_calls}

    log(f"[start] cases={len(rows)} escalate={args.escalate} max_llm_calls={args.max_llm_calls}")
    done = 0
    for row in rows:
        if args.limit and done >= args.limit:
            break
        case_id = case_id_for(row)
        cache_file = CACHE / f"{case_id}.json"
        if cache_file.exists() and not args.force:
            continue
        rec = process(row, args, budget)
        cache_file.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        done += 1
        if done % 10 == 0:
            log(f"  processed {done} | last_case={case_id} | llm_calls={budget['calls']}")
            rebuild_outputs()  # periodic flush so interim progress is inspectable mid-run
        time.sleep(config.DELAY_S)
        if not budget["allow"]():
            log(f"[budget] reached {budget['calls']} calls; stopping")
            break

    out = rebuild_outputs()
    USAGE_JSON.write_text(json.dumps(usage_summary(), indent=2), encoding="utf-8")
    log(f"[done] new_processed={done} llm_calls={budget['calls']} | {out}")
    log(f"[usage] {json.dumps(usage_summary())}")
    print(f"OUTPUTS -> {OUT}")


if __name__ == "__main__":
    main()
