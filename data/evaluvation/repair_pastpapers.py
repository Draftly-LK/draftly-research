"""Repair extraction defects in place, against the source text.

Two classes of defect survive validation, and both are mechanical:

  drifted quotes  the extractor transcribed a quote with a character or two
                  changed ("Therafter" for "Thereafter", a space added after
                  "1."). The line it meant is unambiguous, so the quote is
                  replaced with the exact source line rather than re-run.

  missing lines   a source question line no attempt was made to capture. These
                  are NOT repaired here: adding a question needs a decision
                  about which node it belongs to, which is what --report lists
                  so it can be done deliberately.

Repairs are matched by similarity against the page's own lines, and only
applied above a threshold and when the best match is clearly better than the
runner-up. Anything ambiguous is left alone and reported, because a confident
wrong repair is worse than a flagged defect.

Always dry-run first. The default prints the diff and writes nothing.

Usage:
    uv run python data/evaluvation/repair_pastpapers.py --paper 6
    uv run python data/evaluvation/repair_pastpapers.py --paper 6 --apply
    uv run python data/evaluvation/repair_pastpapers.py --all --apply
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from validate_pastpapers import (  # noqa: E402
    RAW_DIR,
    PAPERS_CSV,
    _norm,
    is_unreadable_page,
    load_pages,
    load_paper_row,
    normalize_lead_ins,
    quote_lines_verbatim,
    walk_nodes,
)

# A quote line must be at least this similar to a source line before it is
# treated as the same line with transcription drift.
MIN_SIMILARITY = 0.88
# And it must beat the runner-up by this much, so a line that resembles several
# source lines equally is never silently bound to one of them.
MIN_MARGIN = 0.04


MAX_WINDOW = 25


def _candidates(source_lines: list[str], piece: str) -> list[str]:
    """Source lines, plus every run of consecutive lines, as match candidates.

    A fact pattern spans a dozen source lines and the extractor often emits it
    as one long string. Comparing that against a single source line scores ~0.15
    and looks like a hallucination, when it is really a faithful join of a run
    of lines with one character drifted. Windows make the comparison like-for-
    like; they are capped by the piece's own length so the search stays small.
    """
    out = list(source_lines)
    if len(piece) <= 120:
        return out
    for size in range(2, min(MAX_WINDOW, len(source_lines)) + 1):
        for start in range(len(source_lines) - size + 1):
            window = " ".join(source_lines[start:start + size])
            if len(window) > len(piece) * 1.6:
                break
            out.append(window)
    return out


def best_source_match(line: str, source_lines: list[str]) -> tuple[str | None, float, float]:
    """Closest source line or run of lines, its score, and the gap to the next best."""
    candidates = _candidates(source_lines, line)
    scored = sorted(
        ((difflib.SequenceMatcher(None, line, s).ratio(), s) for s in candidates),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not scored:
        return None, 0.0, 0.0
    top_score, top_line = scored[0]
    # Runner-up must be a materially different string, not the same span with
    # one more word on the end, or the margin test rejects every real match.
    runner_up = next(
        (s for s, text in scored[1:] if difflib.SequenceMatcher(None, top_line, text).ratio() < 0.9),
        0.0,
    )
    return top_line, top_score, top_score - runner_up


def repair_paper(paper_no: int, apply: bool) -> tuple[int, int]:
    raw_path = RAW_DIR / f"paper-{paper_no:02d}.extract.json"
    if not raw_path.is_file():
        print(f"paper {paper_no}: no extraction at {raw_path.name}")
        return 0, 0

    raw = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_path.read_text(encoding="utf-8").strip()))
    normalize_lead_ins(raw)

    row = load_paper_row(paper_no)
    pages = load_pages(int(row["start_page"]), int(row["end_page"]))
    source_lines = [
        _norm(l)
        for page, text in pages.items()
        if not is_unreadable_page(text)
        for l in text.splitlines()
        if _norm(l)
    ]

    fixed = skipped = 0
    for label, node in walk_nodes(raw):
        quote = node.get("quote") or ""
        if not quote or quote_lines_verbatim(quote, pages):
            continue

        repaired_lines, ok = [], True
        for piece in (l for l in quote.splitlines() if _norm(l)):
            piece = _norm(piece)
            if piece in source_lines or any(piece in s for s in source_lines):
                repaired_lines.append(piece)
                continue
            match, score, margin = best_source_match(piece, source_lines)
            if match and score >= MIN_SIMILARITY and margin >= MIN_MARGIN:
                print(f"  {label}")
                print(f"    - {piece[:96]}")
                print(f"    + {match[:96]}   (similarity {score:.3f})")
                repaired_lines.append(match)
            else:
                print(f"  {label}: SKIPPED, best match {score:.3f} margin {margin:.3f}")
                print(f"    ? {piece[:96]}")
                ok = False
                break

        if ok and repaired_lines:
            node["quote"] = "\n".join(repaired_lines)
            fixed += 1
        else:
            skipped += 1

    if apply and fixed:
        raw_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return fixed, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()

    if args.all:
        papers = [int(r["paper_no"]) for r in csv.DictReader(PAPERS_CSV.open(newline="", encoding="utf-8"))]
    elif args.paper:
        papers = [args.paper]
    else:
        parser.error("pass --paper N or --all")

    total_fixed = total_skipped = 0
    for paper_no in papers:
        fixed, skipped = repair_paper(paper_no, args.apply)
        if fixed or skipped:
            print(f"paper {paper_no}: {fixed} repaired, {skipped} left for review\n")
        total_fixed += fixed
        total_skipped += skipped

    print(f"total: {total_fixed} quotes repaired, {total_skipped} left for review")
    if not args.apply:
        print("dry run: nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
