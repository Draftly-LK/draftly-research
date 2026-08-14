"""Shared HTML extraction for CommonLII LKSC judgment pages.

Every page follows the same frame: a ``<h2>`` case heading, judgment content,
then a footer that starts at the first following ``<hr>``. The judgment body
mixes two paragraph conventions, sometimes in the same file: one ``<p>`` per
paragraph, and page-sized ``<p>`` blocks whose paragraphs are separated by
runs of two or more ``<br>`` tags. Manual inspection of the low-confidence
files (see data/commonlii/layout-eda/uncertain-layouts.csv) showed hybrids of
both conventions, so the core splitter always honours both boundaries and the
per-layout parsers tune post-processing instead.

Output is a list of evidence blocks rather than bare strings: each block
carries its index, the printed report page it sits on, the source tag, the
reason it was split, and bold/italic flags, so downstream consumers can show
exactly where a holding or citation came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

# Paragraphs that are only a printed page number, e.g. "330" or "1 7 8".
PAGE_NUMBER_PATTERN = re.compile(r"^\d[\d\s]{0,6}$")
# Conversion placeholder for report pages absent from the CommonLII source.
PAGE_MISSED_PATTERN = re.compile(r"^page\s+missed\b", re.I)

BLOCK_TAGS = {"p", "div", "center", "table", "blockquote", "ul", "ol", "pre"}
BOLD_TAGS = {"b", "strong"}
ITALIC_TAGS = {"i", "em"}


@dataclass
class Block:
    """One judgment paragraph with evidence of where it came from."""

    block_index: int
    text: str
    report_page: int | None
    source_tag: str
    split_reason: str  # "p_boundary" | "double_br" | "top_level_text"
    was_bold: bool
    was_italic: bool

    def to_dict(self) -> dict:
        return {
            "block_index": self.block_index,
            "text": self.text,
            "report_page": self.report_page,
            "source_tag": self.source_tag,
            "split_reason": self.split_reason,
            "was_bold": self.was_bold,
            "was_italic": self.was_italic,
        }


@dataclass
class ParsedJudgment:
    file: str
    page_title: str
    blocks: list[Block] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)
    missing_page_locations: list[dict] = field(default_factory=list)

    @property
    def paragraphs(self) -> list[str]:
        return [block.text for block in self.blocks]

    @property
    def has_page_missed(self) -> bool:
        return bool(self.missing_page_locations)

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)


def load_soup(path: Path) -> BeautifulSoup:
    html = path.read_text(encoding="utf-8", errors="replace")
    # lxml tolerates the archive's stray </font> and </span> closers.
    return BeautifulSoup(html, "lxml")


def judgment_blocks(soup: BeautifulSoup) -> list[Tag | NavigableString]:
    """Top-level nodes between the case heading and the footer rule."""
    heading = soup.find("h2")
    if heading is None:
        raise ValueError("no <h2> case heading")

    blocks: list[Tag | NavigableString] = []
    for node in heading.next_siblings:
        if isinstance(node, Tag) and node.name == "hr":
            break
        blocks.append(node)
    return blocks


# Digitized print carries Unicode punctuation variants; fold them to ASCII so
# downstream regexes see one hyphen and one apostrophe.
_PUNCT_FOLD = str.maketrans({
    "\xa0": " ",
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
})


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_PUNCT_FOLD)).strip()


def _has_ancestor(node: NavigableString, names: set[str], stop: Tag) -> bool:
    for parent in node.parents:
        if parent is stop:
            return False
        if parent.name in names:
            return True
    return False


@dataclass
class _Segment:
    text: str
    split_reason: str
    bold_chars: int
    italic_chars: int
    total_chars: int

    @property
    def was_bold(self) -> bool:
        return self.total_chars > 0 and self.bold_chars / self.total_chars >= 0.6

    @property
    def was_italic(self) -> bool:
        return self.total_chars > 0 and self.italic_chars / self.total_chars >= 0.6


def split_on_br_runs(tag: Tag, min_br_run: int = 2) -> list[_Segment]:
    """Split one block tag into segments at runs of ``min_br_run`` <br> tags.

    Shorter runs read as soft line breaks and collapse into spaces. Each
    segment tracks how much of its text sat inside bold/italic markup.
    """
    segments: list[_Segment] = []
    parts: list[str] = []
    bold_chars = italic_chars = total_chars = 0
    br_run = 0
    saw_split = False

    def flush(reason: str) -> None:
        nonlocal bold_chars, italic_chars, total_chars
        text = normalise("".join(parts))
        if text:
            segments.append(
                _Segment(text, reason, bold_chars, italic_chars, total_chars)
            )
        parts.clear()
        bold_chars = italic_chars = total_chars = 0

    for node in tag.descendants:
        if isinstance(node, Comment):
            continue
        if isinstance(node, NavigableString):
            raw = str(node)
            visible = len(normalise(raw))
            if visible:
                br_run = 0
                total_chars += visible
                if _has_ancestor(node, BOLD_TAGS, tag):
                    bold_chars += visible
                if _has_ancestor(node, ITALIC_TAGS, tag):
                    italic_chars += visible
            parts.append(raw)
        elif node.name == "br":
            br_run += 1
            if br_run >= min_br_run:
                flush("double_br")
                saw_split = True
                br_run = 0
            else:
                parts.append(" ")
    flush("double_br" if saw_split else "p_boundary")
    return segments


def extract_blocks(
    soup: BeautifulSoup, min_br_run: int = 2
) -> tuple[list[Block], list[int], list[dict]]:
    """Return (blocks, printed page numbers, missing-page locations)."""
    staged: list[tuple[_Segment, str]] = []  # (segment, source_tag)

    for node in judgment_blocks(soup):
        if isinstance(node, Comment):
            continue
        if isinstance(node, NavigableString):
            text = normalise(str(node))
            if text:
                staged.append(
                    (_Segment(text, "top_level_text", 0, 0, len(text)), "text")
                )
            continue
        if node.name not in BLOCK_TAGS:
            # Inline strays (<b>, <font>, ...) hoisted to top level by the
            # tag-soup source; keep their text as part of the flow.
            for segment in split_on_br_runs(node, min_br_run=min_br_run):
                staged.append((segment, node.name))
            continue
        for segment in split_on_br_runs(node, min_br_run=min_br_run):
            staged.append((segment, node.name))

    blocks: list[Block] = []
    page_numbers: list[int] = []
    missing: list[dict] = []
    current_page: int | None = None
    pending_missed: dict | None = None

    for segment, source_tag in staged:
        if PAGE_NUMBER_PATTERN.match(segment.text):
            current_page = int(segment.text.replace(" ", ""))
            page_numbers.append(current_page)
            if pending_missed is not None:
                pending_missed["before_report_page"] = current_page
                missing.append(pending_missed)
                pending_missed = None
            continue
        if PAGE_MISSED_PATTERN.match(segment.text):
            pending_missed = {
                "after_report_page": current_page,
                "before_report_page": None,
                "block_index": len(blocks),
            }
            continue
        blocks.append(
            Block(
                block_index=len(blocks),
                text=segment.text,
                report_page=current_page,
                source_tag=source_tag,
                split_reason=segment.split_reason,
                was_bold=segment.was_bold,
                was_italic=segment.was_italic,
            )
        )
    if pending_missed is not None:
        missing.append(pending_missed)
    return blocks, page_numbers, missing


def parse_judgment(path: Path, file: str, min_br_run: int = 2) -> ParsedJudgment:
    soup = load_soup(path)
    heading = soup.find("h2")
    title = normalise(heading.get_text(" ")) if heading else ""
    blocks, page_numbers, missing = extract_blocks(soup, min_br_run=min_br_run)
    return ParsedJudgment(
        file=file,
        page_title=title,
        blocks=blocks,
        page_numbers=page_numbers,
        missing_page_locations=missing,
    )
