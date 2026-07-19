"""Judge-then-filter: build judging packs, merge verdicts, emit rules_vetted.csv.

The ablation study proved quote-grounding is necessary but not sufficient
(~58% usable). This stage sends every CLEANED rule to a strong LLM judge
(Codex GPT-5.5 workers, per user decision) scoring the six dimensions from the
holdout study, then keeps only usable=true.

  python judge_rules.py build            # packs of 25 -> output/judge/pack-N.json
  python judge_rules.py merge            # part-N.jsonl verdicts -> rules_vetted.csv

Worker contract (one Codex worker per pack): read pack-N.json, judge each rule
against the ACTUAL judgment text at its text_path, write part-N.jsonl with one
JSON object per rule: {rule_id, statement_correct, quote_supports, is_ratio,
qualifications_ok, statute_correct, usable, reason}. Strict, lean-false.
"""

from __future__ import annotations

import argparse
import csv
import json
import math

import config
from extract_case_rules import load_cases, log

JUDGE_DIR = config.OUT / "judge"
PACK_SIZE = 25
DIMS = ("statement_correct", "quote_supports", "is_ratio",
        "qualifications_ok", "statute_correct", "usable")


def cmd_build(args) -> None:
    rows = list(csv.DictReader((config.OUT / "rules_cleaned.csv").open(encoding="utf-8")))
    text_paths = {c["case_id"]: c.get("text_path", "") for c in load_cases()}
    JUDGE_DIR.mkdir(exist_ok=True)
    packs = math.ceil(len(rows) / PACK_SIZE)
    for n in range(packs):
        chunk = rows[n * PACK_SIZE : (n + 1) * PACK_SIZE]
        payload = [
            {
                "rule_id": r["rule_id"],
                "case_id": r["case_id"],
                "citation": r["citation"],
                "statement": r["statement"],
                "supporting_quote": r["supporting_quote"],
                "statute_section": r["statute_section"],
                "method": r["method"],
                "text_path": text_paths.get(r["case_id"], ""),
            }
            for r in chunk
        ]
        (JUDGE_DIR / f"pack-{n:03d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    log(f"[judge build] rules={len(rows)} packs={packs} -> {JUDGE_DIR}")
    print(f"PACKS {packs}")


def cmd_merge(args) -> None:
    verdicts: dict[str, dict] = {}
    for pf in sorted(JUDGE_DIR.glob("part-*.jsonl")):
        for line in pf.read_text(encoding="utf-8").splitlines():
            try:
                v = json.loads(line)
                if v.get("rule_id"):
                    verdicts[v["rule_id"]] = v
            except Exception:
                pass
    rows = list(csv.DictReader((config.OUT / "rules_cleaned.csv").open(encoding="utf-8")))
    judged = [r for r in rows if r["rule_id"] in verdicts]
    vetted = [r for r in judged if verdicts[r["rule_id"]].get("usable") is True]
    rates = {}
    for d in DIMS:
        k = sum(1 for r in judged if verdicts[r["rule_id"]].get(d) is True)
        rates[d] = {"k": k, "n": len(judged), "rate": round(k / len(judged), 3) if judged else None}

    fields = list(rows[0].keys()) + ["judge_reason"]
    out = config.OUT / "rules_vetted.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in vetted:
            writer.writerow({**r, "judge_reason": str(verdicts[r["rule_id"]].get("reason", ""))[:300]})
    summary = {
        "cleaned_rules": len(rows),
        "judged": len(judged),
        "pending": len(rows) - len(judged),
        "vetted_usable": len(vetted),
        "dimension_rates_among_judged": rates,
        "note": "Judge is an LLM proxy (Codex GPT-5.5); lawyer labels remain the authoritative gate.",
    }
    (config.OUT / "judge-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"[judge merge] judged={len(judged)}/{len(rows)} vetted={len(vetted)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("build", "merge"))
    args = ap.parse_args()
    (cmd_build if args.cmd == "build" else cmd_merge)(args)
