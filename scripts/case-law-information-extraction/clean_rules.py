"""Rule-quality repair: headnote normalization + deterministic hygiene.

Why: rules_high_confidence.csv carried 72% mechanical red flags (audit
2026-07-19) — raw un-normalized `Held:` fragments as statements (the $0 Track A
run skipped --normalize), OCR page-number tails, mojibake, and corpus leaks.
Quote grounding was never the problem; statement quality was.

Two subcommands:

  python clean_rules.py normalize   # LLM pass (NVIDIA 8B), resumable, updates
                                    # Track-A cache records in place; quotes are
                                    # untouched so grounding stays intact
  python clean_rules.py clean       # $0 deterministic pass over the rebuilt
                                    # rules.csv -> rules_cleaned.csv + clean-audit.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time

import config
from extract_case_rules import SYS_NORMALIZE, USER_NORMALIZE, load_links, log
from llm_client import chat_json, usage_summary

# ---------------------------------------------------------------- text repair

# UTF-8 bytes mis-decoded as cp1252 (curly quotes/dashes) + stray replacement chars
MOJIBAKE = {
    "â€™": "'", "â€˜": "'",
    "â€œ": '"', "â€": '"', "â€": '"',
    "â€”": "—", "â€“": "–",
    "Â ": " ", "â€¦": "...",
}
PAGE_TAIL_RE = re.compile(r"[.,;:]?\s*\d{2,4}\s*$")
SENTENCE_END_RE = re.compile(r"[.!?\"')\]]\s*$")
# LLM meta-answers that pass shape checks but are not rules
META_STATEMENT_RE = re.compile(
    r"(did not (?:provide|state|establish)|no clear (?:legal )?rule|cannot (?:be )?determin|"
    r"the passage (?:does not|doesn't)|insufficient (?:information|context)|"
    r"unable to (?:extract|identify)|this (?:passage|text|excerpt) (?:is|does))",
    re.IGNORECASE,
)
CONVEYANCING_RE = re.compile(
    r"\b(deed|land|title|property|notar|partition|mortgage|lease|prescript|possession|"
    r"donation|gift|testament|will|estate|heir|convey|transfer|servitude|co-own|registr|"
    r"fideicommiss|usufruct|laesio|planta|crown|state land|vindicat|dominium|encumbranc|"
    r"boundar|survey|lot|allotment|decree|eject)\w*\b",
    re.IGNORECASE,
)


def fix_text(value: str) -> str:
    for bad, good in MOJIBAKE.items():
        value = value.replace(bad, good)
    # lone replacement char between letters is almost always an apostrophe
    value = re.sub(r"(?<=\w)�(?=\w)", "'", value)
    value = value.replace("�", " ")
    return re.sub(r"\s+", " ", value).strip()


def strip_page_tail(statement: str) -> str:
    # trailing law-report page numbers ("... the Respondent. 274")
    stripped = PAGE_TAIL_RE.sub("", statement).rstrip()
    # only accept the strip when it leaves a sentence-like ending
    return stripped if len(stripped) >= 25 else statement


# ---------------------------------------------------------------- normalize (LLM)

def cmd_normalize(args) -> None:
    """Rewrite each Track-A rule statement (raw Held fragment) into one clean
    rule sentence via the cheap model. Resumable: records are marked
    `normalized`; quotes and grounding are never modified."""
    done = calls = updated = failed = 0
    cache_files = sorted(config.CACHE.glob("*.json"))
    for cf in cache_files:
        try:
            rec = json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rec.get("track") != "A" or not rec.get("rules") or rec.get("normalized"):
            continue
        if args.limit and done >= args.limit:
            break
        done += 1
        changed = False
        for rule in rec["rules"]:
            raw = strip_page_tail(fix_text(rule.get("statement", "")))
            if not raw:
                continue
            calls += 1
            j = chat_json(SYS_NORMALIZE, USER_NORMALIZE.format(held=raw[:1600]), args.model)
            candidate = ""
            if j and isinstance(j.get("rules"), list) and j["rules"]:
                candidate = re.sub(r"\s+", " ", str(j["rules"][0].get("statement", ""))).strip()
            # accept only a clean, sentence-shaped rule; otherwise keep the repaired raw
            if 25 <= len(candidate) <= 350 and candidate[0].isupper():
                rule["statement"] = candidate
                rule["normalized"] = True
                changed = True
            else:
                rule["statement"] = raw
                rule["normalized"] = False
                failed += 1
            scope = j.get("rules", [{}])[0].get("scope") if j else None
            if scope in ("ratio", "obiter", "fact-specific"):
                rule["scope"] = scope
        rec["normalized"] = True
        cf.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        updated += changed
        if done % 50 == 0:
            log(f"[normalize] cases={done} calls={calls} updated={updated} weak={failed}")
        time.sleep(config.DELAY_S)
    log(f"[normalize done] cases={done} calls={calls} updated={updated} weak={failed}")
    log(f"[usage] {json.dumps(usage_summary())}")


# ---------------------------------------------------------------- clean ($0)

def cmd_clean(args) -> None:
    links = load_links()
    src = config.OUT / "rules.csv"
    rows = list(csv.DictReader(src.open(encoding="utf-8")))
    kept, audit = [], []

    def drop(row, reason):
        audit.append({"rule_id": row["rule_id"], "action": "drop", "reason": reason,
                      "statement": row["statement"][:160]})

    seen_statements: set[tuple[str, str]] = set()
    for row in rows:
        original = row["statement"]
        statement = strip_page_tail(fix_text(original))
        quote = fix_text(row["supporting_quote"])
        repaired = statement != original or quote != row["supporting_quote"]
        row["statement"], row["supporting_quote"] = statement, quote

        if len(statement) < 25:
            drop(row, "fragment-too-short"); continue
        if statement[0].islower():
            drop(row, "starts-mid-sentence"); continue
        if len(statement) > 60 and not SENTENCE_END_RE.search(statement) and statement.rsplit(" ", 1)[-1].islower():
            drop(row, "truncated-mid-word"); continue
        if len(statement) > 450:
            drop(row, "narrative-not-rule"); continue
        if META_STATEMENT_RE.search(statement):
            drop(row, "llm-meta-answer"); continue
        # corpus-leak filter: nothing conveyancing-shaped AND the case cites no statute
        if not CONVEYANCING_RE.search(statement + " " + quote) and not links.get(row["case_id"]):
            drop(row, "off-topic-leak"); continue
        key = (row["case_id"], statement.lower())
        if key in seen_statements:
            drop(row, "duplicate-in-case"); continue
        seen_statements.add(key)
        if repaired:
            audit.append({"rule_id": row["rule_id"], "action": "repair",
                          "reason": "mojibake/page-tail/whitespace", "statement": statement[:160]})
        kept.append(row)

    out = config.OUT / "rules_cleaned.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(kept)
    audit_path = config.OUT / "clean-audit.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["rule_id", "action", "reason", "statement"])
        writer.writeheader()
        writer.writerows(audit)
    dropped = sum(1 for a in audit if a["action"] == "drop")
    reasons = {}
    for a in audit:
        if a["action"] == "drop":
            reasons[a["reason"]] = reasons.get(a["reason"], 0) + 1
    log(f"[clean] in={len(rows)} kept={len(kept)} dropped={dropped} repaired={len(audit)-dropped}")
    log(f"[clean] drop reasons: {json.dumps(reasons)}")
    print(f"WROTE {out} and {audit_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("normalize", "clean"))
    ap.add_argument("--model", default=config.MODEL_CHEAP)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    (cmd_normalize if args.cmd == "normalize" else cmd_clean)(args)
