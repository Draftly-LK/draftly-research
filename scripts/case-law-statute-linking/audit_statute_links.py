"""Audit the EXISTING statute resolution in rules.csv before building any linker.

Something already populated a statute_section field for ~697 rules. Before we
build anything on top of that, we need to know: how was it done, and is it
trustworthy? This script does NOT change anything -- it reads rules.csv and
reports:

  1. total rules, how many carry a statute_citation_verbatim, how many already
     resolve to a statute_section, and the overlap between the two;
  2. the gap: cited-but-unresolved, and resolved-but-no-citation (suspicious);
  3. the most-cited statutes/sections (your 'top-N' targets);
  4. a side-by-side sample of citation-text vs resolved-section, so a human can
     eyeball whether the existing resolution is actually correct;
  5. which citation FORMAT each sampled row uses (the 3 patterns you found),
     so we know the extractor's job up front.

Usage:
    python scripts/audit_statute_links.py
    python scripts/audit_statute_links.py --rules path/to/rules.csv --sample 30
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = ROOT / "scripts" / "case-law-information-extraction" / "output" / "rules.csv"

# candidate column names -- the script auto-detects whichever exist
CITATION_COLS = ["statute_citation_verbatim", "citation_verbatim", "statute_citation"]
SECTION_COLS = ["statute_section", "resolved_section", "section_id", "statute_section_id"]
STATUTE_ID_COLS = ["statute_source_id", "source_id", "statute_id"]
RULE_TEXT_COLS = ["rule_text", "rule", "ratio", "text", "holding"]
CASE_COLS = ["case_id", "case", "case_name"]


def pick(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


# the 3 citation formats found in the data
PATTERNS = {
    "section-of-Act": re.compile(r"\bsections?\b.{0,6}\bof the\b", re.I),
    "Code-comma-s": re.compile(r",\s*s\.?\s*\d", re.I),
    "Ordinance-No-of-year": re.compile(r"Ordinance\s+No\.?\s*\d+\s+of\s+\d{4}", re.I),
}


def classify_format(text: str) -> str:
    if not text:
        return "empty"
    if PATTERNS["Ordinance-No-of-year"].search(text):
        return "Ordinance-No-of-year"
    if PATTERNS["section-of-Act"].search(text):
        return "section-of-Act"
    if PATTERNS["Code-comma-s"].search(text):
        return "Code-comma-s"
    if len(text) > 200:
        return "inline-fulltext (long)"
    return "other"


def run(rules: str | None = None, sample: int = 20) -> int:
    path = Path(rules) if rules else DEFAULT_RULES
    if not path.exists():
        raise SystemExit(f"rules file not found: {path}\n"
                         f"pass the real path with --rules")

    df = pd.read_csv(path, dtype=str).fillna("")
    total = len(df)

    cite_col = pick(df, CITATION_COLS)
    sec_col = pick(df, SECTION_COLS)
    sid_col = pick(df, STATUTE_ID_COLS)
    rule_col = pick(df, RULE_TEXT_COLS)
    case_col = pick(df, CASE_COLS)

    print(f"rules file: {path}")
    print(f"total rules: {total}")
    print(f"\ndetected columns:")
    print(f"  citation : {cite_col}")
    print(f"  section  : {sec_col}")
    print(f"  statute  : {sid_col}")
    print(f"  rule text: {rule_col}")
    print(f"  case     : {case_col}")
    print(f"\nall columns present: {list(df.columns)}")

    if not cite_col and not sec_col:
        print("\n[!] Couldn't find citation or section columns by name. "
              "Check the column list above and re-run with the right names "
              "hardcoded, or tell me the names.")
        return 1

    has_cite = df[cite_col].str.strip() != "" if cite_col else pd.Series([False] * total)
    has_sec = df[sec_col].str.strip() != "" if sec_col else pd.Series([False] * total)

    n_cite = int(has_cite.sum())
    n_sec = int(has_sec.sum())
    both = int((has_cite & has_sec).sum())
    cite_no_sec = int((has_cite & ~has_sec).sum())   # the GAP to close
    sec_no_cite = int((~has_cite & has_sec).sum())   # suspicious: resolved with no citation text

    print(f"\n--- coverage ---")
    print(f"  carry a citation (verbatim): {n_cite} ({n_cite/total:.1%})")
    print(f"  already resolved to a section: {n_sec} ({n_sec/total:.1%})")
    print(f"  BOTH cited and resolved:       {both}")
    print(f"  cited but NOT resolved (gap):  {cite_no_sec}  <- v1 target to close")
    print(f"  resolved but NO citation text: {sec_no_cite}  <- check how these were resolved")

    # most-cited statutes / sections (top-N targets)
    if sid_col:
        print(f"\n--- most-cited statutes ({sid_col}) ---")
        top = Counter(df.loc[has_sec, sid_col]).most_common(12)
        for sid, n in top:
            print(f"  {sid:<12} {n:>4}")
    if sec_col:
        print(f"\n--- most-cited sections ({sec_col}) ---")
        top = Counter(df.loc[has_sec, sec_col]).most_common(15)
        for sec, n in top:
            print(f"  {sec:<24} {n:>4}")

    # citation format breakdown
    if cite_col:
        print(f"\n--- citation FORMAT breakdown (of the {n_cite} cited) ---")
        fmts = Counter(classify_format(t) for t in df.loc[has_cite, cite_col])
        for fmt, n in fmts.most_common():
            print(f"  {fmt:<26} {n:>4} ({n/n_cite:.0%})")

    # side-by-side sample: citation text vs resolved section vs rule snippet
    print(f"\n--- SAMPLE: citation vs resolved section (eyeball these) ---")
    sample_df = df[has_cite & has_sec].head(200)
    step = max(1, len(sample_df) // sample)
    picked = sample_df.iloc[::step].head(sample)
    for i, r in enumerate(picked.itertuples(index=False), 1):
        cite = getattr(r, cite_col)[:90] if cite_col else ""
        sec = getattr(r, sec_col) if sec_col else ""
        sid = getattr(r, sid_col) if sid_col else ""
        case = getattr(r, case_col) if case_col else ""
        print(f"\n[{i}] {case}")
        print(f"    cited:    {cite!r}")
        print(f"    resolved: {sid}  {sec}")

    # also show a few cited-but-unresolved, so we see what the gap looks like
    if cite_no_sec:
        print(f"\n--- SAMPLE: cited but UNRESOLVED (the gap to close) ---")
        gap = df[has_cite & ~has_sec].head(60)
        for i, r in enumerate(gap.iloc[::max(1, len(gap)//10)].head(10).itertuples(index=False), 1):
            cite = getattr(r, cite_col)[:90]
            fmt = classify_format(getattr(r, cite_col))
            print(f"  [{i}] ({fmt}) {cite!r}")

    print(f"\ndone. Nothing was modified.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rules", default=None, help="path to rules.csv")
    ap.add_argument("--sample", type=int, default=20, help="side-by-side rows to print")
    raise SystemExit(run(**vars(ap.parse_args())))