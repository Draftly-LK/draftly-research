"""Stage 1 of case-law -> statute linking: audit the EXISTING resolution.

The extractor already populated statute_section for 697 rules, but only 166 of
those also carry a verbatim citation -- meaning 531 were resolved with NO
citation text to back them. Before building anything on top of that, we must
know HOW those 531 were produced and whether they are trustworthy.

The rules.csv has the columns that answer this: section_status, match_type,
confidence, method, statute_citation_grounded, status. This script reads them
(read-only) and reports:

  1. coverage: cited / resolved / both / gap / no-citation-resolved;
  2. the 531 no-citation resolutions broken down by method / match_type /
     section_status / confidence -- so we can see if they were matched, inferred,
     or guessed;
  3. confidence distribution for grounded vs ungrounded resolutions;
  4. the gap (cited-but-unresolved) split into: cites an Act we HAVE vs an Act
     NOT in the catalogue (winnable vs coverage-gap);
  5. flags for the two systematic bugs seen in the sample -- multi-section
     citations collapsed to one, and section numbers that don't appear in the
     citation text (possible OCR/parse errors).

Nothing is modified.

Usage:
    python scripts/case-law-statute-linking/01_audit_existing_resolution.py
    python 01_audit_existing_resolution.py --rules path/to/rules.csv
    # optional: point at the folder of Lahiru's statute JSONs to compute the
    # HAVE-vs-MISSING split precisely:
    python 01_audit_existing_resolution.py --statutes data/legal-sources/statutes
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "scripts" / "case-law-information-extraction" / "output" / "rules.csv"

# known columns in rules.csv (from the audit output)
C_CITE = "statute_citation_verbatim"
C_GROUNDED = "statute_citation_grounded"
C_SECTION = "statute_section"
C_SEC_STATUS = "section_status"
C_MATCH = "match_type"
C_CONF = "confidence"
C_METHOD = "method"
C_STATUS = "status"
C_CASE = "case_id"
C_YEAR = "year"

# section token inside a resolved id, e.g. SRC030-s247 -> ('SRC030','247')
RESOLVED_RE = re.compile(r"(SRC\d+)\D+s?(\d+)", re.I)
# all section numbers mentioned in a citation string, e.g. "ss. 283, 284 and 285"
SECNUM_RE = re.compile(r"\b(\d{1,4})\b")


def load_statute_ids(folder: Path | None) -> set[str]:
    """Return the set of source_ids Lahiru has parsed, if the folder is given."""
    ids: set[str] = set()
    if not folder or not folder.exists():
        return ids
    for p in folder.rglob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            sid = d.get("source_id")
            if sid:
                ids.add(sid)
        except Exception:
            continue
    return ids


def section_of(resolved: str) -> tuple[str, str] | None:
    m = RESOLVED_RE.search(resolved or "")
    return (m.group(1).upper(), m.group(2)) if m else None


def run(rules: str | None = None, statutes: str | None = None) -> int:
    path = Path(rules) if rules else DEFAULT_RULES
    if not path.exists():
        raise SystemExit(f"rules file not found: {path}")
    df = pd.read_csv(path, dtype=str).fillna("")
    total = len(df)

    have_ids = load_statute_ids(Path(statutes) if statutes else None)

    has_cite = df[C_CITE].str.strip() != "" if C_CITE in df else pd.Series([False] * total)
    has_sec = df[C_SECTION].str.strip() != "" if C_SECTION in df else pd.Series([False] * total)

    print(f"rules file: {path}")
    print(f"total rules: {total}")
    if have_ids:
        print(f"statute catalogue: {len(have_ids)} source_ids loaded from {statutes}")
    else:
        print("statute catalogue: not provided (HAVE-vs-MISSING split will be skipped)")

    # ---- 1. coverage ----
    both = has_cite & has_sec
    gap = has_cite & ~has_sec           # cited but unresolved
    nocite = ~has_cite & has_sec        # resolved with no citation text
    print(f"\n--- coverage ---")
    print(f"  cited (verbatim):        {int(has_cite.sum())}")
    print(f"  resolved to a section:   {int(has_sec.sum())}")
    print(f"  both:                    {int(both.sum())}")
    print(f"  cited but UNRESOLVED:    {int(gap.sum())}   <- winnable gap")
    print(f"  resolved but NO citation:{int(nocite.sum())}   <- trust unknown")

    # ---- 2. break down the no-citation resolutions ----
    print(f"\n--- the {int(nocite.sum())} no-citation resolutions, by column ---")
    nc = df[nocite]
    for col in (C_METHOD, C_MATCH, C_SEC_STATUS, C_STATUS, C_GROUNDED):
        if col in df:
            print(f"\n  {col}:")
            for val, n in Counter(nc[col]).most_common(10):
                shown = val if val else "(blank)"
                print(f"    {shown:<32} {n:>4}")

    # ---- 3. confidence distribution grounded vs ungrounded ----
    if C_CONF in df:
        print(f"\n--- confidence: grounded (both) vs ungrounded (no-citation) ---")
        def conf_stats(mask, label):
            vals = pd.to_numeric(df.loc[mask, C_CONF], errors="coerce").dropna()
            if len(vals):
                print(f"  {label:<26} n={len(vals):>4}  "
                      f"min={vals.min():.2f} med={vals.median():.2f} "
                      f"mean={vals.mean():.2f} max={vals.max():.2f}")
            else:
                print(f"  {label:<26} (no numeric confidence values)")
        conf_stats(both, "grounded (cited+resolved)")
        conf_stats(nocite, "ungrounded (no citation)")

    # ---- 4. split the gap: Act we HAVE vs Act MISSING ----
    if have_ids:
        print(f"\n--- the {int(gap.sum())} unresolved-but-cited, by catalogue coverage ---")
        # heuristic: can't know source_id without resolving; instead report how
        # many resolved rows point at ids we DON'T have (dangling), and how many
        # distinct resolved ids are outside the catalogue.
        resolved_ids = set()
        for r in df.loc[has_sec, C_SECTION]:
            s = section_of(r)
            if s:
                resolved_ids.add(s[0])
        dangling = sorted(resolved_ids - have_ids)
        print(f"  resolved source_ids present in catalogue: "
              f"{len(resolved_ids & have_ids)}/{len(resolved_ids)}")
        if dangling:
            print(f"  resolved to source_ids NOT in catalogue (dangling links): {dangling}")

    # ---- 5. systematic-bug flags ----
    print(f"\n--- systematic-bug flags (on the {int(both.sum())} grounded rows) ---")
    multi_sec = 0
    mismatch = 0
    examples_multi, examples_mismatch = [], []
    for r in df[both].itertuples(index=False):
        cite = getattr(r, C_CITE)
        resolved = getattr(r, C_SECTION)
        s = section_of(resolved)
        if not s:
            continue
        resolved_num = s[1]
        nums_in_cite = SECNUM_RE.findall(cite)
        # multi-section citation: more than one distinct section-like number,
        # but only one resolved
        distinct = [n for n in dict.fromkeys(nums_in_cite)]
        if len(distinct) > 1 and resolved_num in distinct:
            multi_sec += 1
            if len(examples_multi) < 5:
                examples_multi.append((cite[:70], resolved))
        # mismatch: the resolved section number does NOT appear in the citation
        if resolved_num not in nums_in_cite:
            mismatch += 1
            if len(examples_mismatch) < 8:
                examples_mismatch.append((cite[:70], resolved))
    print(f"  multi-section citations collapsed to one section: {multi_sec}")
    for c, rv in examples_multi:
        print(f"      cite={c!r} -> {rv}")
    print(f"  resolved section NOT found in citation text (possible error): {mismatch}")
    for c, rv in examples_mismatch:
        print(f"      cite={c!r} -> {rv}")

    print(f"\ndone. Nothing was modified.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rules", default=None, help="path to rules.csv")
    ap.add_argument("--statutes", default=None,
                    help="folder of Lahiru's statute JSONs (optional, enables "
                         "HAVE-vs-MISSING catalogue split)")
    raise SystemExit(run(**vars(ap.parse_args())))