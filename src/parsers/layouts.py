"""One parser per layout category, plus a generic fallback for uncertain files.

All four layouts share the extraction core in ``base.py``; what differs is the
paragraph-boundary tuning. NLR hybrids (see uncertain-layouts.csv) mix
paragraph-led and <br>-led sections in one file, so both NLR parsers honour
both boundary kinds and differ only in how aggressively <br> runs split.
"""

from __future__ import annotations

from pathlib import Path

from base import ParsedJudgment, parse_judgment


def parse_paragraph_nlr(path: Path, file: str) -> ParsedJudgment:
    """Paragraph-led NLR: <p> per paragraph, double <br> only in front matter."""
    return parse_judgment(path, file, min_br_run=2)


def parse_dense_br_nlr(path: Path, file: str) -> ParsedJudgment:
    """<br>-led NLR: page-sized <p> blocks split by double-<br> runs."""
    return parse_judgment(path, file, min_br_run=2)


def parse_structured_slr(path: Path, file: str) -> ParsedJudgment:
    """Early SLR: clean <p> structure with semantic markers (Held, etc.)."""
    return parse_judgment(path, file, min_br_run=2)


def parse_late_slr_font(path: Path, file: str) -> ParsedJudgment:
    """2005+ SLR: <font>-wrapped <p> blocks whose paragraphs are separated by
    double <br> runs; single <br>s are caption line breaks and collapse."""
    return parse_judgment(path, file, min_br_run=2)


def parse_uncertain(path: Path, file: str) -> ParsedJudgment:
    """Fallback for low-confidence files: the shared hybrid-safe splitter."""
    return parse_judgment(path, file, min_br_run=2)


PARSERS = {
    "paragraph_nlr": parse_paragraph_nlr,
    "dense_br_nlr": parse_dense_br_nlr,
    "structured_slr": parse_structured_slr,
    "late_slr_font": parse_late_slr_font,
    "uncertain": parse_uncertain,
}
