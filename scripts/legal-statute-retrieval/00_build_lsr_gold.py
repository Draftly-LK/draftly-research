"""Build an IL-PCSR-style statute-retrieval gold set from verified case links.

IL-PCSR ("Legal Corpus for Prior Case and Statute Retrieval", EMNLP 2025)
formulates Legal Statute Retrieval (LSR) as: given a case, mask the statute
citation it actually relies on, and treat the surrounding text as a query.
This script builds that gold set from data this repo already has:

    scripts/case-law-statute-linking/output/resolved_links.csv
        band == "verified" rows -- a citation was located and grounded in
        the case text, per scripts/case-law-information-extraction/validate.py.
    scripts/case-law-information-extraction/output/rules.csv
        supplies the verbatim `supporting_quote` (guaranteed a literal
        substring of the source judgment at extraction time) and the
        `statute_citation_verbatim` phrase to mask out of it.
    data/processed/cases.jsonl
        supplies each case's judgment text path and decision year.

For each verified link, the query is the text window around the located
quote with the citation phrase replaced by a placeholder (CLERC/IL-PCSR's
masking pattern). Where the verbatim quote can't be relocated in the stored
markdown -- text drifts between extraction input and committed output do
happen here, e.g. OCR replacement characters -- the row falls back to using
the quote itself as the query, and is tagged accordingly so the eval report
can state the fallback rate honestly rather than hide it.

Every gold row also carries `temporal_status`, reusing
build_section_versions.py's `grade_link` so "does the case's decision year
predate a later amendment to this exact section" is answered the same way
here as it is for the existing case-to-section link table -- not
reimplemented, and not skipped just because this is a different pipeline.

Deterministic, no LLM calls, re-running produces byte-identical output.

    python scripts/legal-statute-retrieval/00_build_lsr_gold.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from build_section_versions import grade_link, read_actions, statutes_with_history  # noqa: E402

RESOLVED_LINKS = ROOT / "scripts/case-law-statute-linking/output/resolved_links.csv"
RULES_CSV = ROOT / "scripts/case-law-information-extraction/output/rules.csv"
CASES_JSONL = ROOT / "data/processed/cases.jsonl"

OUT_GOLD = ROOT / "data/processed/lsr_gold.jsonl"
OUT_SKIPPED = ROOT / "data/processed/lsr_gold_skipped.csv"

WINDOW_CHARS = 400
PLACEHOLDER = "[CITATION]"

WINDOW_CITATION_MASKED = "window-citation-masked"
WINDOW_QUOTE_MASKED = "window-quote-masked"
HELD_SENTENCE_FALLBACK = "held-sentence-fallback"


def normalize(text: str) -> str:
    """Collapse whitespace and drop encoding-artifact characters so a quote
    extracted from one text rendering can still be located in another."""
    text = text.replace("�", "").replace("\xad", "")
    return re.sub(r"\s+", " ", text).strip()


def load_rules() -> dict[str, dict[str, str]]:
    with RULES_CSV.open(encoding="utf-8", newline="") as handle:
        return {row["rule_id"]: row for row in csv.DictReader(handle)}


def load_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {}
    with CASES_JSONL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            cases[row["case_id"]] = row
    return cases


def load_verified_links() -> list[dict[str, str]]:
    with RESOLVED_LINKS.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("band") == "verified"]


def build_query(case_text: str, quote: str, citation: str) -> tuple[str, str]:
    """Return (query_text, query_construction).

    Mirrors CLERC/IL-PCSR: mask the citation, keep the surrounding sentence
    as the retrieval query. Falls back to the bare quote when the quote
    can't be relocated in the stored case text at all.
    """
    norm_text = normalize(case_text)
    norm_quote = normalize(quote)
    norm_citation = normalize(citation)

    index = norm_text.find(norm_quote) if norm_quote else -1
    if index == -1:
        return norm_quote, HELD_SENTENCE_FALLBACK

    start = max(0, index - WINDOW_CHARS)
    end = min(len(norm_text), index + len(norm_quote) + WINDOW_CHARS)
    window = norm_text[start:end]

    if norm_citation and norm_citation in window:
        return window.replace(norm_citation, PLACEHOLDER), WINDOW_CITATION_MASKED
    return window.replace(norm_quote, PLACEHOLDER), WINDOW_QUOTE_MASKED


def parse_year(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def main() -> int:
    rules = load_rules()
    cases = load_cases()
    links = load_verified_links()
    actions = read_actions()
    known = statutes_with_history(actions)

    gold_rows: list[dict] = []
    skipped_rows: list[dict[str, str]] = []

    def skip(link: dict[str, str], reason: str) -> None:
        skipped_rows.append({"case_id": link["case_id"], "rule_id": link["rule_id"], "reason": reason})

    for link in links:
        source_id = (link.get("source_id") or "").strip().upper()
        section_number = (link.get("section_number") or "").strip()
        if not (source_id and section_number):
            skip(link, "missing-source-or-section")
            continue

        rule = rules.get(link["rule_id"])
        if rule is None:
            skip(link, "rule-not-found")
            continue

        case = cases.get(link["case_id"])
        if case is None:
            skip(link, "case-not-found")
            continue

        text_path = ROOT / case["text_path"]
        if not text_path.exists():
            skip(link, "text-file-missing")
            continue

        quote = rule.get("supporting_quote") or ""
        if not quote.strip():
            skip(link, "no-supporting-quote")
            continue

        citation = rule.get("statute_citation_verbatim") or link.get("citation") or ""
        case_text = text_path.read_text(encoding="utf-8")
        query_text, construction = build_query(case_text, quote, citation)
        if not query_text:
            skip(link, "empty-query")
            continue

        case_year = parse_year(case.get("year"))
        temporal_status, amended_after = grade_link(case_year, source_id, section_number, actions, known)

        gold_rows.append(
            {
                "query_id": f"lsr-{link['rule_id']}",
                "case_id": link["case_id"],
                "source_id": source_id,
                "section_number": section_number,
                "section_id": f"{source_id}:s{section_number}",
                "query_text": query_text,
                "query_construction": construction,
                "case_year": case_year,
                "temporal_status": temporal_status,
                "amended_after_judgment": amended_after,
            }
        )

    OUT_GOLD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_GOLD.open("w", encoding="utf-8") as handle:
        for row in gold_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    with OUT_SKIPPED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "rule_id", "reason"])
        writer.writeheader()
        writer.writerows(skipped_rows)

    print(f"  verified links considered    : {len(links):,}")
    print(f"  gold queries written         : {len(gold_rows):,}")
    print(f"  skipped                      : {len(skipped_rows):,}")
    print(f"  skip reasons                 : {dict(Counter(r['reason'] for r in skipped_rows))}")
    print(f"  query construction           : {dict(Counter(r['query_construction'] for r in gold_rows))}")
    print(f"  temporal status              : {dict(Counter(r['temporal_status'] for r in gold_rows))}")
    print(f"\n  wrote {OUT_GOLD.relative_to(ROOT)}")
    print(f"  wrote {OUT_SKIPPED.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
