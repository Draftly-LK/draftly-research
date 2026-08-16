"""Extract legal rules from the downloaded Supreme Court judgment PDFs (SCLR).

These are raw judgments from supremecourt.lk (data/supremecourt.lk/SCLR/),
not edited law-report headnotes — there is no `Held:` block to parse
deterministically (Track A in extract_case_rules.py never applies here).
Every case goes through Track B (bounded, quote-grounded LLM extraction),
reusing extract_case_rules.track_B / parse_meta / validate.py / catalogue.py /
windowing.py / llm_client.py as-is — this script only adds the PDF -> text ->
case-record ingestion path those don't have.

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
import time
from pathlib import Path

import pypdfium2 as pdfium

import config
import extract_case_rules as ecr
from llm_client import usage_summary

MANIFEST = config.ROOT / "data" / "supremecourt.lk" / "manifest.csv"
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

    result = ecr.track_B(
        case, text, [], args.model_cheap, args.model_strong, args.escalate,
        budget, allow_fuzzy=args.allow_fuzzy, full_text=args.full_text,
        window_strategy=args.window,
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
    rule_rows, meta_rows, reject_rows = [], [], []
    for cache_file in sorted(CACHE.glob("*.json")):
        try:
            rec = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
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
    return {"rules": len(rule_rows), "meta": len(meta_rows), "rejects": len(reject_rows)}


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
    ap.add_argument("--window", default="naive", choices=("naive", "cue"))
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
        if done % 25 == 0:
            log(f"  processed {done} | llm_calls={budget['calls']}")
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
