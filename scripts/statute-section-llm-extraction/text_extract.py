"""Phase 1: correctly-ordered linear text per statute PDF.

Plain pdfplumber `extract_text()` is already in reading order for
single-column pages regardless of where marginal notes sit -- the
mirrored-layout Stamp Duty Act only breaks a *coordinate* margin/body split,
not linear reading order, so it needs nothing special here.

Genuine two-physical-column pages (the two Matrimonial Rights Ordinances)
need a column-aware pass: `page.extract_text()` reads strictly top-to-bottom
across the whole page width, which interleaves the two columns' unrelated
content line by line. This module instead groups each page's lines into a
left half and a right half by x-position, and emits all of the left half
top-to-bottom, then all of the right half top-to-bottom -- matching how a
person actually reads the page.

Only macro reading order matters here, not margin-vs-body role: a line's
words are joined in left-to-right (x0) order regardless of whether some of
them are a marginal note and others are body text, since the LLM downstream
parses structure from continuous prose, not from column position.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pdfplumber

import config

sys.path.insert(0, str(config.SANDBOX))
from extractor import Line, clean_text, cluster_words_into_lines  # noqa: E402

sys.path.insert(0, str(config.ROOT / "scripts"))
import convert_to_text as _docai  # noqa: E402

# Mirrors convert_to_text.py's MIN_DOCUMENT_CHARS: below this, a PDF's own
# text layer is too thin to be real body text (a scanned image PDF commonly
# still carries a handful of stray characters -- a page-number stamp, an
# OCR'd cover sheet -- so the bar is "basically nothing", not "zero").
MIN_TEXT_LAYER_CHARS = 200


def _non_ws_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def extract_plain_text(pdf_path: Path) -> str:
    """Reading-order text for single-column (or margin-mirrored) PDFs."""
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


_MARGIN_AVG_WORDS = 4.5  # a margin phrase is short; body wraps to fill the column
_MIN_BUCKET_LINES = 4    # ignore buckets too sparse to trust their average
_MIN_MARGIN_SHARE = 0.07  # a real margin column covers more than a stray indent


def _sample_pages(pages: list, sample_pages: int) -> list:
    """Spread the sample across the document rather than taking the first N,
    which skews toward a cover page and Table of Sections -- both have
    line-length statistics nothing like the real body (short, dot-leadered
    entries), which otherwise gets misread as a marginal note column.
    """
    n = len(pages)
    if n <= sample_pages:
        return list(pages)
    # skip the first 5% (front matter) and last 2% (schedules/index)
    start, end = int(n * 0.05), int(n * 0.98)
    span = max(end - start, 1)
    step = max(span // sample_pages, 1)
    return [pages[i] for i in range(start, end, step)][:sample_pages]


def _line_buckets(pages: list, sample_pages: int) -> tuple[dict[int, list[int]], float]:
    from collections import defaultdict

    buckets: dict[int, list[int]] = defaultdict(list)
    widths: list[float] = []
    for page in _sample_pages(pages, sample_pages):
        lines = _page_lines(page)
        widths.append(float(page.width))
        for line in lines:
            if not line.words:
                continue
            bucket = round(line.words[0].x0 / 10) * 10
            buckets[bucket].append(len(line.words))
    width = sum(widths) / len(widths) if widths else 0.0
    return buckets, width


def _find_margin_split(
    pages: list, sample_pages: int = 15
) -> tuple[float, str] | None:
    """Return (x threshold, side) where `side` is "left" or "right" -- the
    side of the threshold that is the marginal note -- or None if the
    document doesn't show one at all (a clean single-column Act).

    Classifies each x0 bucket by average words-per-line rather than by which
    side of the page it's on: a margin phrase is short (a handful of words)
    regardless of whether the margin sits on the left (the common case) or
    the right (Stamp Duty Special Provisions Act, this Act -- both mirrored).
    A body column wraps to fill its width, so its buckets average markedly
    more words per line. The margin is whichever edge (left or right) starts
    with a run of short-average buckets that then switches to long-average
    ones -- not just the single narrowest bucket, since a margin column's
    own line starts vary a little from wrapping.
    """
    buckets, width = _line_buckets(pages, sample_pages)
    if not buckets or width <= 0:
        return None
    trusted = {
        x: sum(counts) / len(counts)
        for x, counts in buckets.items()
        if len(counts) >= _MIN_BUCKET_LINES
    }
    total_lines = sum(len(buckets[x]) for x in trusted)
    xs = sorted(trusted)
    if len(xs) < 2 or total_lines == 0:
        return None

    def is_margin(x: int) -> bool:
        return trusted[x] <= _MARGIN_AVG_WORDS

    def cluster_share(edge_xs: list[int]) -> float:
        return sum(len(buckets[x]) for x in edge_xs) / total_lines

    # A genuine margin note recurs on most sections, not just an occasional
    # deep-indent list marker ("(a)", "(i)") that happens to open a wrapped
    # line -- so the low-average-words run at an edge must cover a real
    # share of all sampled lines, not just be sparse-but-present.

    # Left-margin case: a run of margin-like buckets from the left edge,
    # ending where body-like buckets begin.
    if is_margin(xs[0]):
        for i, x in enumerate(xs):
            if not is_margin(x):
                if i and cluster_share(xs[:i]) >= _MIN_MARGIN_SHARE:
                    return (xs[i - 1] + x) / 2, "left"
                break
    # Right-margin (mirrored) case: same, scanning from the right edge.
    if is_margin(xs[-1]):
        for i, x in enumerate(reversed(xs)):
            if not is_margin(x):
                prev = xs[len(xs) - i]
                if cluster_share(xs[len(xs) - i :]) >= _MIN_MARGIN_SHARE:
                    return (x + prev) / 2, "right"
                break
    return None


_ROW_GAP_MIN = 15.0  # a visual break between columns, not routine word spacing


def _drop_margin_from_line(line: Line, split: float, side: str) -> Line:
    """Trim a line to its body portion only, using a per-line gap rather than
    a single global cutoff.

    A body sentence's natural wrap length varies row to row, so a fixed x0
    threshold cuts into real body words on some rows ("...cited as the
    Revocation of[374.9] Short[395.85] title.[416.85]" -- a global cutoff
    placed between the margin and body *clusters* can still land inside
    body's own row-to-row range and drop "of"). What's actually reliable is
    that wherever the margin genuinely starts on THIS row, there is a real
    visual gap between it and the body word before it -- word spacing within
    a column runs a few points; the gap into a separate column runs much
    wider. So each line is scanned for that gap near the document's
    approximate margin start (`split`, used only as *where to start
    looking*, not as a strict boundary), and only trimmed if a genuine gap
    is found there. A row with no such gap is body through to its end and is
    kept whole, rather than risk cutting it on a threshold that doesn't
    apply to this particular row.
    """
    words = line.words
    if not words:
        return line
    if side == "left":
        # margin words come first; find the gap that ends the margin and
        # starts the body, searching from a little before the approximate
        # split so a slightly early body start is still caught.
        for i in range(1, len(words)):
            if words[i].x0 >= split - 40 and words[i].x0 - words[i - 1].x1 >= _ROW_GAP_MIN:
                return Line(page=line.page, top=line.top, words=words[i:])
        # No gap found: either this row is body-only (started past the
        # margin already, nothing to trim) or margin-only (never reached
        # body). The two are told apart by whether the row ever got close.
        if words[-1].x0 < split - 40:
            return Line(page=line.page, top=line.top, words=[])
        return line
    # margin words trail; scan for the gap that starts it, searching from
    # a little before the approximate split so a slightly early margin start
    # is still caught.
    for i in range(1, len(words)):
        if words[i].x0 >= split - 40 and words[i].x0 - words[i - 1].x1 >= _ROW_GAP_MIN:
            return Line(page=line.page, top=line.top, words=words[:i])
    if words[0].x0 >= split - 40:
        return Line(page=line.page, top=line.top, words=[])
    return line


def extract_body_only_text(pdf_path: Path) -> str:
    """Reading-order text for a margin-note document, with the marginal
    notes dropped entirely rather than left interleaved into body sentences.

    A margin note commonly interrupts a body sentence mid-line in the raw
    PDF text stream ("...cited as the Revocation of Short title. Irrevocable
    Deeds of Gift..."), which an LLM asked to quote it verbatim will
    "helpfully" smooth over -- exactly the paraphrase risk the anchor design
    exists to catch, so nearly every anchor fails validation against text
    that still contains the interruption. Dropping the margin words leaves
    plain, grammatically complete body prose with nothing to smooth over.
    """
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        found = _find_margin_split(pdf.pages)
        if found is None:
            return extract_plain_text(pdf_path)
        split, side = found
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_words = page.extract_words(
                x_tolerance=2, y_tolerance=3, use_text_flow=False,
                keep_blank_chars=False,
            )
            for line in cluster_words_into_lines(page_number, raw_words, 2.0):
                trimmed = _drop_margin_from_line(line, split, side)
                text = clean_text(" ".join(word.text for word in trimmed.words))
                if text:
                    parts.append(text)
    return "\n".join(parts)


def _page_lines(page, line_tolerance: float = 2.0) -> list[Line]:
    words = page.extract_words(
        x_tolerance=2, y_tolerance=3, use_text_flow=False, keep_blank_chars=False
    )
    return cluster_words_into_lines(1, words, line_tolerance)


def _find_column_split(
    pages: list, sample_pages: int = 15
) -> float | None:
    """Return an x threshold separating two physical columns, or None if the
    sampled pages don't show a clear gap (not a two-column document).

    The widest gap in first-word x0 isn't necessarily the real column
    boundary: a margin-note document commonly has margin/body pairs on
    *both* sides ("margin1 body1 margin2 body2"), and the gap between body1
    and margin2 is often narrower than a sparse, wide gap between margin2
    and an outlier cluster (page numbers, rare full-width lines) further
    right. So this scores each candidate gap by how evenly it splits the
    sampled lines' total count, not just by raw width -- the real column
    boundary divides the page's content roughly in half; an accidental gap
    between minor clusters doesn't.
    """
    from collections import Counter

    counts: Counter[int] = Counter()
    widths: list[float] = []
    for page in _sample_pages(pages, sample_pages):
        lines = _page_lines(page)
        counts.update(round(line.words[0].x0) for line in lines if line.words)
        widths.append(float(page.width))
    if not counts or not widths:
        return None
    width = sum(widths) / len(widths)
    lo, hi = width * 0.1, width * 0.9
    xs = sorted(x for x in counts if lo <= x <= hi)
    if len(xs) < 2:
        return None
    total = sum(counts[x] for x in xs)
    if total == 0:
        return None

    best_score, best_mid = 0.0, None
    cumulative = counts[xs[0]]
    prev = xs[0]
    for x in xs[1:]:
        gap = x - prev
        if gap >= 15:
            balance = 1 - abs(cumulative / total - 0.5) * 2  # 1.0 = even split
            score = balance * min(gap, 80)
            if score > best_score:
                best_score, best_mid = score, (prev + x) / 2
        cumulative += counts[x]
        prev = x
    return best_mid


def extract_two_column_text(pdf_path: Path) -> str:
    """Reading-order text for a genuinely two-physical-column PDF.

    A single visual row can hold unrelated text from both columns at once
    (pdfplumber's line clustering groups purely by vertical position, and two
    columns with different line-heights frequently land at the same `top`),
    so words are split into a left set and a right set *before* clustering,
    not after -- each side is then independently reclustered into its own
    lines, which is what keeps a shared row from merging two columns' text.
    """
    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        split = _find_column_split(pdf.pages)
        if split is None:
            raise ValueError(
                f"{pdf_path.name}: no clear two-column split found; use "
                "extract_plain_text instead"
            )
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_words = page.extract_words(
                x_tolerance=2, y_tolerance=3, use_text_flow=False,
                keep_blank_chars=False,
            )
            left_words = [w for w in raw_words if w["x0"] < split]
            right_words = [w for w in raw_words if w["x0"] >= split]
            left_lines = cluster_words_into_lines(page_number, left_words, 2.0)
            right_lines = cluster_words_into_lines(page_number, right_words, 2.0)
            for line in (*left_lines, *right_lines):
                text = clean_text(" ".join(word.text for word in line.words))
                if text:
                    parts.append(text)
    return "\n".join(parts)


def extract_text_with_ocr_fallback(
    pdf_path: Path, *, two_column: bool = False, source_id: str | None = None,
) -> tuple[str, bool, list[int]]:
    """Try the pdfplumber text layer first; only reach for Document AI OCR
    if that comes back empty or negligible (a genuinely scanned PDF).

    Returns (source_text, used_ocr, low_confidence_pages) -- low_confidence_pages
    are 1-indexed pages where Document AI's own reported confidence fell below
    CONFIDENCE_THRESHOLD (scripts/convert_to_text.py's
    document_ai_confidence_threshold()), surfaced so a document built from
    them can be flagged for review rather than treated as clean.
    """
    text = extract_two_column_text(pdf_path) if two_column else extract_plain_text(pdf_path)
    if _non_ws_chars(text) >= MIN_TEXT_LAYER_CHARS:
        return text, False, []

    import pypdfium2 as pdfium

    sid = source_id or pdf_path.stem
    pdf = pdfium.PdfDocument(pdf_path)
    pages_text: list[str] = []
    low_confidence_pages: list[int] = []
    try:
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            bitmap = page.render(scale=150 / 72.0)
            image = bitmap.to_pil()
            # force_document_ai=True: this PDF has no usable text layer at
            # all, so there's no local-OCR result to weigh against -- go
            # straight to Document AI for every page, reusing the same
            # cache/ledger/confidence-threshold logic convert_to_text.py's
            # own OCR fallback uses rather than duplicating it here.
            page_text, used_cloud, warning, confidence = _docai.maybe_document_ai(
                image, sid, page_index + 1, "", 0.0, True,
                _docai.MAX_DOCUMENT_AI_PAGES, force_document_ai=True,
            )
            if not used_cloud:
                raise RuntimeError(
                    f"{pdf_path.name} page {page_index + 1}: Document AI OCR "
                    f"did not run ({warning or 'no text layer and no cloud result'})"
                )
            if warning:
                low_confidence_pages.append(page_index + 1)
            pages_text.append(page_text)
            del image, bitmap, page
            _docai.print_progress_bar(
                page_index + 1, len(pdf), label=f"{sid} OCR",
            )
    finally:
        pdf.close()
    return "\n".join(pages_text), True, low_confidence_pages
