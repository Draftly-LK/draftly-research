"""Extract sections from legislation PDFs whose marginal notes are *stacked*.

Why a second extractor
----------------------
`extractor.py` assumes the two-column layout of the Apartment Ownership Law
PDF: on any given line, the marginal note and the provision text sit side by
side, so a vertical cut at `--body-x` separates them. Word x0 positions there
show a clean gap -- nothing between x=160 and x=170, and 295 body words land
exactly on 170.

The Registration of Title Act PDF is laid out differently. Its marginal notes
occupy their own lines, *interleaved* between the body lines they sit beside:

    x0= 72.7 | Beneficiaries may request
    x0=205.8 | 17. The beneficiaries may apply to the Commissioner of Title
    x0= 72.7 | appointment of new
    x0=205.8 | Settlement to appoint another co-owner as the Manager of the co-
    x0= 72.7 | Manager.
    x0=205.8 | owned land parcel, on the following grounds :

and the body column's left edge moves with the width of the note beside it --
147, 149, 157, 176, 206, 221, 259, 272 all occur. A marginal note can therefore
end further right (x1 up to 205) than a body line begins (x0 from 147), so no
vertical cut can split them. Running `extractor.py` over this PDF recovers 52
of 74 sections, misorders them, and bleeds headings across section boundaries.

What separates the columns here is not x0 but *line role*, worked out in
`classify_margin_runs`: lines flush with the margin arrive in runs, and a run is
body text if it is full width or wraps from a line that was. Width alone cannot
decide it -- section 10's note reaches x1=246 while section 75's body lines come
back as short as x1=214.

Heading assembly follows from the interleaving. A note's first fragment sits
just above its section's opening line and the rest run alongside, so fragments
are buffered and flushed to the section that the next body line belongs to.

Everything below the line level -- subsection/paragraph nesting, validation,
serialisation -- is imported from `extractor.py` rather than reimplemented.
Beyond that shared schema this adds `part_title` per section, from the all-caps
cross-headings, and a document-level `long_title`.

Checked against CommonLII's independent table of provisions for this Act
(`lk/legis/num_act/rota21o1998290`): 75 of 75 sections, and all 74 headings
that appear in both agree.

    python extractor_stacked.py registration-of-title-act-21-1998.pdf \
        -o ../parsed/registration-of-title-act-21-1998.json \
        --source-id SRC011 --official-title "Registration of Title Act" \
        --act-number 21 --year 1998
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "pdfplumber is required. Install it with: pip install pdfplumber"
    ) from exc

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extractor import (  # noqa: E402  (path set above)
    BodyBlock,
    Line,
    build_document,
    clean_text,
    cluster_words_into_lines,
    join_wrapped_lines,
    parse_hierarchy,
    validate_sections,
    write_csv,
    write_json,
    write_jsonl,
)

SECTION_MARKER_RE = re.compile(r"^(\d{1,3})([A-Za-z]?)\.$")
MARKER_PREFIX_RE = re.compile(r"^\d{1,3}[A-Za-z]?\.?$")
# A lone marker is only a section start if the preceding line finished a
# sentence or list item. See read_section_marker.
SENTENCE_END_RE = re.compile(r"[.;:]\s*$")
MARKER_MAX_TOKENS = 3
MARKER_MAX_GAP = 8.0
# Cross-headings ("STRATA TITLES", "TRANSMISSION OF TITLE") divide the Act
# between sections. They carry no lowercase letters.
CROSS_HEADING_RE = re.compile(r"^[^a-z]+$")
CROSS_HEADING_MIN_LETTERS = 4
# The long title is set in the same all-caps style as the cross-headings but is
# document metadata, not a division of the Act.
LONG_TITLE_RE = re.compile(r"^(AN ACT|AN ORDINANCE|A LAW)\b")


@dataclass
class StackedSection:
    number: str
    page_start: int
    part_title: str | None = None
    heading_fragments: list[str] = field(default_factory=list)
    body_blocks: list[BodyBlock] = field(default_factory=list)
    pages_seen: set[int] = field(default_factory=set)


def is_cross_heading(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    return (len(letters) >= CROSS_HEADING_MIN_LETTERS
            and bool(CROSS_HEADING_RE.match(text)))


def is_margin_flush(line: Line, *, margin_x: float,
                    margin_tolerance: float) -> bool:
    return abs(line.words[0].x0 - margin_x) <= margin_tolerance


def classify_margin_runs(lines: list[Line], *, margin_x: float,
                         margin_tolerance: float,
                         full_width_min_x1: float) -> set[int]:
    """Return the indices of lines that are marginal notes.

    Starting at the margin is not enough on its own: the "Provided that ..."
    provisos and the whole of section 75 (Interpretation) are set full width
    from the same left edge. Nor is a width cut enough in the other direction --
    section 10's note runs out to x1=246 while section 75's continuation lines
    come back as short as x1=214, so the two overlap and no threshold separates
    them.

    What does separate them is how these lines arrive: in runs, broken by the
    body-column lines they sit beside. Within a run, a line is body text if it
    is full width, or if it continues a body line that had not finished its
    sentence. Anything else is a note.

    That last test is what splits a run like section 59's proviso, where a note
    follows the paragraph immediately with no body-column line between them:

        of a registered owner ... or interest therein     x1=539  body
        for valuable consideration ... to such fraud.     x1=418  body, wraps
        Person suffering                                  x1=151  note

    Judging the run as a whole would swallow "Person suffering" into the
    proviso and lose the section 60 heading with it. Judging each line only by
    width would break the wrapped line above it.

    Finally, a note column never overlaps the body column beside it. Section 75
    (Interpretation) is set full width, so `"owner" means-` sits at the margin
    and looks like a note until you see that the line under it begins at
    x0=147.6, to the *left* of where that "note" ends. Candidates failing this
    are body text.
    """
    notes: set[int] = set()
    run: list[int] = []

    def next_body_x0(after: int) -> float | None:
        for i in range(after + 1, len(lines)):
            if lines[i].words and not is_margin_flush(
                    lines[i], margin_x=margin_x,
                    margin_tolerance=margin_tolerance):
                return lines[i].words[0].x0
        return None

    def flush() -> None:
        candidates: list[int] = []
        previous_was_body = False
        previous_text = ""
        for i in run:
            line = lines[i]
            text = " ".join(word.text for word in line.words)
            if line.words[-1].x1 >= full_width_min_x1:
                is_body = True
            elif previous_was_body and not SENTENCE_END_RE.search(previous_text):
                is_body = True          # wrapped tail of the paragraph above
            else:
                is_body = False
            if not is_body:
                candidates.append(i)
            previous_was_body, previous_text = is_body, text

        if candidates:
            body_x0 = next_body_x0(run[-1])
            widest = max(lines[i].words[-1].x1 for i in candidates)
            if body_x0 is None or body_x0 > widest:
                notes.update(candidates)
        run.clear()

    for index, line in enumerate(lines):
        if line.words and is_margin_flush(line, margin_x=margin_x,
                                          margin_tolerance=margin_tolerance):
            run.append(index)
        else:
            flush()
    flush()

    # An indented note. Section 75's "Interpretation." sits at x0=143.9 rather
    # than at the margin, so no margin test finds it, but it still clears the
    # body column that opens directly beneath it.
    for index, line in enumerate(lines):
        if index == 0 or index in notes or not line.words:
            continue
        if not looks_like_marker(line):
            continue
        above = lines[index - 1]
        if not above.words or index - 1 in notes:
            continue
        marker_x0 = line.words[0].x0
        if above.words[0].x0 < marker_x0 and above.words[-1].x1 < marker_x0:
            notes.add(index - 1)
    return notes


def looks_like_marker(line: Line) -> bool:
    """Shape test only -- does this line open with a section number?"""
    joined = ""
    for index, word in enumerate(line.words[:MARKER_MAX_TOKENS]):
        if index and word.x0 - line.words[index - 1].x1 > MARKER_MAX_GAP:
            return False
        joined += word.text
        if SECTION_MARKER_RE.match(joined):
            return True
        if not MARKER_PREFIX_RE.match(joined):
            return False
    return False


def read_section_marker(line: Line, previous: BodyBlock | None,
                        ) -> tuple[str, int] | None:
    """Return (section number, words consumed) when this body line opens one.

    Two artefacts of this PDF's text layer are handled here.

    The marker is not reliably one token. `5 7.`, `6 4.` and `6 6.` split the
    digits apart, and `26 .` and `56 .` split the period off. So leading tokens
    are joined while they still look like a marker and the gaps between them
    stay tight. Reading only the first token records section 57 as section 7 and
    loses 26 and 56 entirely.

    A marker alone on its line is ambiguous: it is equally the shape of a
    cross-reference that wrapped. Section 58 ends `... made under section` with
    `59.` carried to the next line, which would otherwise open a second, empty
    section 59 immediately before the real one. Two signals separate them, and a
    lone marker needs either:

    - the preceding line closed a sentence or list item; or
    - the marker is outdented from the preceding line. Section numbers sit at
      the left edge of the body column while the text they interrupt is
      indented under a subsection.

    The wrapped `59.` fails both -- it sits at exactly the x0 of the line it
    continues. Section 64 needs the indent test on its own, because the PDF
    omits the full stop that should close section 63.
    """
    words = line.words
    joined = ""
    for index, word in enumerate(words[:MARKER_MAX_TOKENS]):
        if index and word.x0 - words[index - 1].x1 > MARKER_MAX_GAP:
            break
        joined += word.text
        match = SECTION_MARKER_RE.match(joined)
        if match:
            consumed = index + 1
            if consumed == len(words) and previous is not None:
                outdented = words[0].x0 < previous.indent - 1.0
                closed = bool(SENTENCE_END_RE.search(previous.raw_text))
                if not (outdented or closed):
                    return None
            return match.group(1) + match.group(2), consumed
        if not MARKER_PREFIX_RE.match(joined):
            break
    return None


def finalize_section(section: StackedSection) -> dict[str, Any]:
    heading = join_wrapped_lines(section.heading_fragments).rstrip(".")
    raw_text = "\n".join(block.raw_text for block in section.body_blocks).strip()
    normalized_text = join_wrapped_lines(
        block.raw_text for block in section.body_blocks
    )
    subsections, paragraphs = parse_hierarchy(section.body_blocks)
    pages = sorted(section.pages_seen or {section.page_start})
    return {
        "section_number": section.number,
        "heading": heading or None,
        "part_title": section.part_title,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "text": normalized_text,
        "subsections": subsections,
        "paragraphs": paragraphs,
        "page_start": min(pages),
        "page_end": max(pages),
    }


def extract_sections(
    pdf_path: Path,
    *,
    margin_x: float = 72.7,
    margin_tolerance: float = 3.0,
    full_width_min_x1: float = 450.0,
    line_tolerance: float = 2.0,
    top_margin: float = 45.0,
    bottom_margin: float = 40.0,
) -> tuple[list[dict[str, Any]], str | None]:
    lines: list[Line] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(
                x_tolerance=2, y_tolerance=3,
                use_text_flow=False, keep_blank_chars=False,
            )
            lines.extend(
                line
                for line in cluster_words_into_lines(
                    page_number, words, line_tolerance)
                if top_margin <= line.top <= float(page.height) - bottom_margin
            )

    note_indices = classify_margin_runs(
        lines, margin_x=margin_x, margin_tolerance=margin_tolerance,
        full_width_min_x1=full_width_min_x1)

    sections: list[dict[str, Any]] = []
    current: StackedSection | None = None
    pending_notes: list[str] = []
    part_title: str | None = None
    long_title: str | None = None
    after_heading = False
    in_long_title = False

    for index, line in enumerate(lines):
        if not line.words:
            continue

        if index in note_indices:
            pending_notes.append(clean_text(
                " ".join(word.text for word in line.words)))
            continue

        line_text = clean_text(" ".join(word.text for word in line.words))
        if is_cross_heading(line_text):
            # Consecutive all-caps lines are one heading. The long title is set
            # the same way, so it is routed to document metadata instead of
            # becoming section 1's part -- PRELIMINARY is printed after section
            # 1 in this Act, so section 1 would otherwise inherit the long title.
            if in_long_title or (current is None
                                 and LONG_TITLE_RE.match(line_text)):
                long_title = (f"{long_title} {line_text}" if in_long_title
                              else line_text)
                in_long_title = True
            else:
                part_title = (f"{part_title} {line_text}" if after_heading
                              else line_text)
            after_heading = True
            continue
        in_long_title = False

        previous = (current.body_blocks[-1]
                    if current and current.body_blocks else None)
        # A cross-heading is a hard break, so a marker directly below one is
        # unambiguously a section start rather than a wrapped cross-reference.
        marker = read_section_marker(line, None if after_heading else previous)
        after_heading = False
        if marker:
            number, consumed = marker
            if current is not None:
                sections.append(finalize_section(current))
            current = StackedSection(number=number, page_start=line.page,
                                     part_title=part_title)
            current.heading_fragments.extend(pending_notes)
            pending_notes.clear()
            current.pages_seen.add(line.page)
            rest = line.words[consumed:]
            text = clean_text(" ".join(word.text for word in rest))
            if text:
                current.body_blocks.append(BodyBlock(text, rest[0].x0))
            continue

        if current is None:
            # Preamble and long title precede section 1; the notes buffered
            # there belong to no section and are dropped rather than
            # misattributed to section 1.
            pending_notes.clear()
            continue

        # A note fragment sitting alongside body text belongs to the section
        # that body text is in.
        current.heading_fragments.extend(pending_notes)
        pending_notes.clear()
        current.pages_seen.add(line.page)
        if line_text:
            current.body_blocks.append(BodyBlock(line_text, line.words[0].x0))

    if current is not None:
        current.heading_fragments.extend(pending_notes)
        sections.append(finalize_section(current))

    return sections, long_title


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract sections from legislation PDFs with stacked "
                    "marginal notes.")
    parser.add_argument("input", type=Path, help="Input PDF with a text layer")
    parser.add_argument("-o", "--output", type=Path,
                        help="Output path; stdout when omitted")
    parser.add_argument("-f", "--format", choices=("json", "jsonl", "csv"),
                        default="json", help="Output format (default: json)")
    parser.add_argument("--margin-x", type=float, default=72.7,
                        help="Left edge of the marginal-note column")
    parser.add_argument("--margin-tolerance", type=float, default=3.0)
    parser.add_argument("--full-width-min-x1", type=float, default=450.0,
                        help="A margin-flush run reaching beyond this is body "
                             "text, not a note")
    parser.add_argument("--line-tolerance", type=float, default=2.0)
    parser.add_argument("--top-margin", type=float, default=45.0)
    parser.add_argument("--bottom-margin", type=float, default=40.0)
    parser.add_argument("--strict", action="store_true",
                        help="Exit 2 when validation warnings are found")
    parser.add_argument("--source-id")
    parser.add_argument("--official-title")
    parser.add_argument("--act-number")
    parser.add_argument("--year", type=int)
    parser.add_argument("--source-url")
    parser.add_argument("--retrieved-at")
    parser.add_argument("--verification-status", default="unverified")
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    sections, long_title = extract_sections(
        args.input,
        margin_x=args.margin_x,
        margin_tolerance=args.margin_tolerance,
        full_width_min_x1=args.full_width_min_x1,
        line_tolerance=args.line_tolerance,
        top_margin=args.top_margin,
        bottom_margin=args.bottom_margin,
    )
    warnings = validate_sections(sections)
    document = build_document(args, sections)
    document["long_title"] = long_title

    stream: TextIO
    should_close = False
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        stream = args.output.open("w", encoding="utf-8", newline="")
        should_close = True
    else:
        stream = sys.stdout

    try:
        if args.format == "json":
            write_json(document, stream)
        elif args.format == "jsonl":
            write_jsonl(sections, stream)
        else:
            write_csv(sections, stream)
    finally:
        if should_close:
            stream.close()

    destination = f" to {args.output}" if args.output else ""
    print(f"Extracted {len(sections)} sections{destination}", file=sys.stderr)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    return 2 if warnings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
