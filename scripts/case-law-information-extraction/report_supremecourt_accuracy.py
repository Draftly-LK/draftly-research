"""Coverage report for the Supreme Court PDF rule extraction
(extract_supremecourt_pdfs.py output).

Reports YIELD (how many processed judgments produced a grounded rule vs.
abstained/rejected/errored) and ATTRIBUTE COMPLETENESS (% non-empty per
column). This is not a legal-accuracy score — nothing here has lawyer
sign-off (see the project README's "Nothing has been scored" limitation).
Grounded confidence (verbatim quote match) is the only correctness signal
available before that review happens.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "output" / "supremecourt-lk"
CACHE = OUT / "cache"
RULES_CSV = OUT / "rules.csv"
META_CSV = OUT / "case_meta.csv"


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def yield_breakdown() -> dict[str, int]:
    counts: dict[str, int] = {}
    for cache_file in CACHE.glob("*.json"):
        try:
            rec = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rec.get("rules"):
            status = "ok"
        else:
            status = rec.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def completeness(rows: list[dict], fields: list[str]) -> dict[str, str]:
    if not rows:
        return {}
    out = {}
    for field in fields:
        non_empty = sum(1 for r in rows if str(r.get(field, "")).strip())
        out[field] = f"{non_empty}/{len(rows)} ({non_empty / len(rows):.0%})"
    return out


def main() -> None:
    processed = len(list(CACHE.glob("*.json")))
    counts = yield_breakdown()
    ok = counts.get("ok", 0)

    print(f"Processed: {processed} judgment(s)")
    print(f"Yielded a grounded rule: {ok} ({ok / processed:.1%})" if processed else "Yielded: n/a")
    print("Breakdown:")
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {status}: {n}")

    rules = _read_csv(RULES_CSV)
    meta = _read_csv(META_CSV)

    print(f"\nrules.csv rows: {len(rules)}")
    for field, pct in completeness(rules, [
        "statement", "supporting_quote", "statute_section",
        "statute_citation_verbatim", "scope", "confidence",
    ]).items():
        print(f"  {field}: {pct}")

    print(f"\ncase_meta.csv rows: {len(meta)}")
    for field, pct in completeness(meta, [
        "citation", "court", "year", "parties", "judge", "disposition",
    ]).items():
        print(f"  {field}: {pct}")

    if rules:
        by_conf: dict[str, int] = {}
        for r in rules:
            by_conf[r.get("confidence", "")] = by_conf.get(r.get("confidence", ""), 0) + 1
        print(f"\nConfidence distribution (grounded rules only): {by_conf}")

    print("\nNote: yield/coverage only, not a legal-accuracy score — no lawyer "
          "verification has run on this output.")


if __name__ == "__main__":
    main()
