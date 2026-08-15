"""Re-check cached reject:quote-not-found records against the current validator,
with no LLM calls. Recovers rules that were only rejected because of a
validator bug (e.g. the model wrapping its quote in literal quote-marks).

Usage:
    python revalidate_rejects.py [--allow-fuzzy]
"""
from __future__ import annotations

import argparse
import json

import config
import validate as V
from extract_case_rules import load_cases, log, rebuild_outputs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-fuzzy", action="store_true")
    args = ap.parse_args()

    by_id = {c["case_id"]: c for c in load_cases()}
    text_paths = {c["case_id"]: c.get("text_path", "") for c in by_id.values()}
    checked = recovered = 0

    for cf in sorted(config.CACHE.glob("*.json")):
        try:
            rec = json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not str(rec.get("status", "")).startswith("reject:"):
            continue
        rr = rec.get("rejected_rule")
        if not rr:
            continue
        case = by_id.get(rec.get("case_id"))
        if not case:
            continue
        from extract_case_rules import read_text
        text = read_text(case)
        if not text:
            continue
        checked += 1
        ok, cleaned, why = V.validate_rule(rr, text, allow_fuzzy=args.allow_fuzzy)
        if not ok:
            continue
        cleaned["method"] = "llm-extract"
        cleaned["rule_id"] = f"draftly-rule-{rec['case_id']}-1"
        cleaned["case_id"] = rec["case_id"]
        cleaned["citation"] = case.get("citation", "")
        cleaned["court"] = case.get("court", "")
        cleaned["year"] = case.get("year", "")
        cleaned["status"] = "unverified"
        rec["status"] = "ok"
        rec["rules"] = [cleaned]
        rec.pop("rejected_rule", None)
        cf.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        recovered += 1

    out = rebuild_outputs()
    log(f"[revalidate] checked={checked} recovered={recovered} | {out}")
    print(f"checked={checked} recovered={recovered} -> {out}")


if __name__ == "__main__":
    main()
