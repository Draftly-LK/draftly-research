from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Iterable, TextIO

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "pdfplumber is required. Install it with: pip install pdfplumber"
    ) from exc


SPACE_RE = re.compile(r"\s+")
SECTION_MARKER_RE = re.compile(r"^(\d{1,3}[A-Za-z]?)\.$")
# Some consolidated-Act layouts only give a marginal note to sections that
# open a new topic; sections that continue under the same note are printed
# inline, with the marker glued to the first word of their text ("3.(1)",
# "5.No") rather than as its own token.
INLINE_SECTION_MARKER_RE = re.compile(r"^(\d{1,3})\.(.+)$")
# A reproduced Form or Schedule appended after the last real section. Its own
# numbered fields ("1. Place of Birth") would otherwise be read as further
# section markers.
ORDINALS = "FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH"
# Case-sensitive and searched anywhere in the line (not anchored): a Schedule
# heading is set in caps ("SECOND SCHEDULE", "FORM OF SUMMONS"), often on the
# same line as a bracketed cross-reference ("[Sections 12, SECOND SCHEDULE"),
# while an in-body cross-reference to the same Schedule is always lower/mixed
# case ("substantially in the form set out in the Second Schedule to this
# Law"), so case alone tells heading from reference without a false match.
SCHEDULE_BOUNDARY_RE = re.compile(
    rf"\b(?:(?:{ORDINALS})\s+)?SCHEDULE\b|\bFORM\s+OF\b"
)
# A line that is only ever "Form A" / "Schedules" -- no other prose -- is a
# Schedule caption regardless of case; a body sentence never stands alone
# like this, so the anchor to the whole line is what keeps this one safe to
# match case-insensitively.
FORM_CAPTION_RE = re.compile(r"^(Form\s+[A-Z]+|Schedules?)$", re.IGNORECASE)
# A Part/Chapter cross-heading ("ALTERATION OF LIMITS OF TOWNS AND NUMBER OF
# MEMBERS. ; &C;") divides the Act between sections; it belongs to none of
# them and must not be read as body text of whichever section is still open
# (typically an empty, repealed-in-place section immediately before it).
# Genuine body prose is never set fully in caps, so requiring at least one
# lowercase-eligible letter and none present is a safe, general test.
CROSS_HEADING_RE = re.compile(r"^[^a-z]+$")
CROSS_HEADING_MIN_LETTERS = 4
PROVISION_MARKER_RE = re.compile(r"^\((\d+|[A-Za-z]+)\)\s*(.*)$", re.DOTALL)
TRAILING_PROVISION_MARKER_RE = re.compile(
    r"^(.*(?:;|:))\s+\(([A-Za-z]+)\)\s*$", re.DOTALL
)


def clean_text(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip()


def join_wrapped_lines(lines: Iterable[str]) -> str:
    """Join visual lines without damaging printed hyphenated compounds."""
    output = ""
    for raw_line in lines:
        line = clean_text(raw_line)
        if not line:
            continue
        if not output:
            output = line
        elif output.endswith("-"):
            # re- + division -> re-division
            output += line
        else:
            output += " " + line
    return clean_text(output)


@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float


@dataclass
class Line:
    page: int
    top: float
    words: list[Word]


@dataclass
class BodyBlock:
    raw_text: str
    indent: float


@dataclass
class WorkingSection:
    number: str
    page_start: int
    heading_lines: list[str] = field(default_factory=list)
    body_blocks: list[BodyBlock] = field(default_factory=list)
    pages_seen: set[int] = field(default_factory=set)


def cluster_words_into_lines(
    page_number: int,
    raw_words: list[dict[str, Any]],
    line_tolerance: float,
) -> list[Line]:
    """Cluster pdfplumber words by baseline/top position."""
    words = [
        Word(
            text=str(item["text"]),
            x0=float(item["x0"]),
            x1=float(item["x1"]),
            top=float(item["top"]),
        )
        for item in raw_words
        if clean_text(str(item.get("text", "")))
    ]
    words.sort(key=lambda word: (word.top, word.x0))

    clusters: list[list[Word]] = []
    cluster_tops: list[float] = []
    for word in words:
        if not clusters or abs(word.top - cluster_tops[-1]) > line_tolerance:
            clusters.append([word])
            cluster_tops.append(word.top)
        else:
            clusters[-1].append(word)
            cluster_tops[-1] = median(item.top for item in clusters[-1])

    lines = []
    for cluster, top in zip(clusters, cluster_tops):
        cluster.sort(key=lambda word: word.x0)
        lines.append(Line(page=page_number, top=top, words=cluster))
    return lines


# Words that mark the following number as *not* a section marker: a
# cross-reference ("section 41") or a Rupee amount in a fee table ("Rs. 750"
# but does not exceed Rs. 1,500").
SECTION_REFERENCE_WORDS = (
    "section", "sections", "subsection", "subsections",
    "chapter", "chapters", "article", "articles", "rs",
)


def find_section_marker(
    line: Line, marker_min_x: float, last_word_of_previous_line: str = ""
) -> tuple[int, str, str | None] | None:
    """Return (word index, section number, glued leftover text) if this line
    opens a section -- either an isolated marker token ("2.") anywhere past
    `marker_min_x`, or, when a topic continues under a still-open marginal
    note, a marker glued straight onto its first word ("3.(1)", "5.No").
    """
    for index, word in enumerate(line.words):
        match = SECTION_MARKER_RE.match(word.text)
        # A standalone "237." ending a sentence is as often a cross-reference
        # ("under section 237.") as it is a real marker. A genuine section
        # opens a paragraph, so it is never preceded by the word "section" --
        # including where the reference wraps, leaving the number alone at
        # the start of the next line ("... of section" / "27.") -- while a
        # cross-reference always is. Legitimate numbering gaps (a run of
        # sections consolidated away entirely, not just left as an empty
        # stub) are common enough in these Acts that gating on sequence
        # instead would reject real markers as often as fake ones.
        # A list of cross-references ("sections 36 and 45") only has the
        # reference word before its first number; later ones in the list are
        # preceded by "and" or a comma. Skip over those to find it too.
        referenced = False
        for back in range(index - 1, max(index - 6, -1), -1):
            token = line.words[back].text.strip("[](),.:;").lower()
            if token == "and" or token == "" or token.isdigit() or (
                token[:-1].isdigit() and token.endswith((".", "a", "b", "c"))
            ):
                continue
            referenced = token in SECTION_REFERENCE_WORDS
            break
        else:
            token = last_word_of_previous_line.strip("[](),.:;").lower()
            referenced = token in SECTION_REFERENCE_WORDS
        if match and word.x0 >= marker_min_x and not referenced:
            return index, match.group(1), None
        glued = INLINE_SECTION_MARKER_RE.match(word.text)
        if glued and not referenced:
            return index, glued.group(1), glued.group(2)
    return None


def heading_text_from_line(
    line: Line,
    *,
    body_x: float,
    margin_line_max_x: float,
    stop_index: int | None = None,
) -> str:
    """Extract a marginal heading fragment from a line."""
    words = line.words if stop_index is None else line.words[:stop_index]
    if not words or words[0].x0 > margin_line_max_x:
        return ""
    margin_words = [word.text for word in words if word.x0 < body_x]
    return clean_text(" ".join(margin_words))


def body_text_from_line(
    line: Line,
    *,
    body_x: float,
    full_width_body_min_x: float,
) -> BodyBlock | None:
    """Extract only provision text, excluding the marginal heading column."""
    if not line.words:
        return None

    # Most body lines begin at body_x. A few continuation paragraphs are
    # centred and begin around x=130, with no marginal text on that line.
    if line.words[0].x0 >= full_width_body_min_x:
        body_words = line.words
    else:
        first_body_index = next(
            (i for i, word in enumerate(line.words) if word.x0 >= body_x),
            None,
        )
        if first_body_index is None:
            return None
        body_words = line.words[first_body_index:]

    text = clean_text(" ".join(word.text for word in body_words))
    return BodyBlock(text, body_words[0].x0) if text else None


def _new_provision(number: str, body: str) -> dict[str, Any]:
    return {
        "number": number,
        "_blocks": [body] if body else [],
        "paragraphs": [],
        "subparagraphs": [],
    }


def _finish_provision(node: dict[str, Any]) -> None:
    blocks = node.pop("_blocks", [])
    node["raw_text"] = "\n".join(blocks).strip()
    node["normalized_text"] = clean_text(" ".join(blocks))
    node["text"] = node["normalized_text"]
    for key in ("paragraphs", "subparagraphs"):
        for child in node.get(key, []):
            _finish_provision(child)
        if not node.get(key):
            node.pop(key, None)


def _indent_levels(blocks: list[BodyBlock], tolerance: float = 2.0) -> list[float]:
    marker_indents = sorted(
        block.indent
        for block in blocks
        if PROVISION_MARKER_RE.match(block.raw_text)
    )
    levels: list[float] = []
    for indent in marker_indents:
        if not levels or abs(indent - levels[-1]) > tolerance:
            levels.append(indent)
        else:
            levels[-1] = (levels[-1] + indent) / 2
    return levels


def parse_hierarchy(blocks: list[BodyBlock]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reconstruct nested provisions from marker indentation."""
    expanded_blocks: list[BodyBlock] = []
    for block in blocks:
        trailing = TRAILING_PROVISION_MARKER_RE.match(block.raw_text)
        if trailing:
            text, marker = trailing.groups()
            expanded_blocks.extend(
                (BodyBlock(text, block.indent), BodyBlock(f"({marker})", block.indent))
            )
        else:
            expanded_blocks.append(block)

    levels = _indent_levels(expanded_blocks)
    subsections: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []
    current_subsection: dict[str, Any] | None = None
    current_paragraph: dict[str, Any] | None = None
    current_subparagraph: dict[str, Any] | None = None
    subsection_level = 0
    paragraph_level = 0

    for block in expanded_blocks:
        match = PROVISION_MARKER_RE.match(block.raw_text)
        if not match:
            target = current_subparagraph or current_paragraph or current_subsection
            if target is not None:
                target["_blocks"].append(block.raw_text)
            continue

        level = min(
            range(1, len(levels) + 1),
            key=lambda index: abs(block.indent - levels[index - 1]),
            default=1,
        )
        number, body = match.groups()
        if number.isdigit():
            expected_number = 1 if not subsections else int(subsections[-1]["number"]) + 1
            if int(number) != expected_number:
                # PDF line wrapping can leave a parenthesized numeric cross-
                # reference at the start of a continuation line. Preserve it
                # in the active provision instead of creating a duplicate.
                target = current_subparagraph or current_paragraph or current_subsection
                if target is not None:
                    target["_blocks"].append(block.raw_text)
                continue
            current_subsection = _new_provision(number, body)
            subsections.append(current_subsection)
            subsection_level = level
            current_paragraph = None
            current_subparagraph = None
            continue

        if current_paragraph is not None and level > paragraph_level:
            current_subparagraph = _new_provision(number, body)
            current_paragraph["subparagraphs"].append(current_subparagraph)
            continue

        current_paragraph = _new_provision(number, body)
        paragraph_level = level
        current_subparagraph = None
        if current_subsection is not None and level > subsection_level:
            current_subsection["paragraphs"].append(current_paragraph)
        else:
            paragraphs.append(current_paragraph)

    for node in [*subsections, *paragraphs]:
        _finish_provision(node)
    return subsections, paragraphs


def finalize_section(section: WorkingSection) -> dict[str, Any]:
    heading = join_wrapped_lines(section.heading_lines).rstrip(".")
    raw_text = "\n".join(block.raw_text for block in section.body_blocks).strip()
    normalized_text = join_wrapped_lines(
        block.raw_text for block in section.body_blocks
    )
    subsections, paragraphs = parse_hierarchy(section.body_blocks)
    pages = sorted(section.pages_seen or {section.page_start})
    return {
        "section_number": section.number,
        "heading": heading or None,
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
    body_x: float = 165.0,
    marker_min_x: float = 150.0,
    margin_line_max_x: float = 110.0,
    full_width_body_min_x: float = 110.0,
    line_tolerance: float = 2.0,
    top_margin: float = 45.0,
    bottom_margin: float = 40.0,
) -> list[dict[str, Any]]:
    """Extract sections using word coordinates from a PDF text layer."""
    all_lines: list[Line] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                use_text_flow=False,
                keep_blank_chars=False,
            )
            page_lines = cluster_words_into_lines(
                page_number, raw_words, line_tolerance=line_tolerance
            )
            all_lines.extend(
                line
                for line in page_lines
                if line.top >= top_margin
                and line.top <= float(page.height) - bottom_margin
            )

    sections: list[dict[str, Any]] = []
    current: WorkingSection | None = None
    last_word = ""

    for line in all_lines:
        # Appended Forms/Schedules are reproduced legal instruments, not
        # sections -- they carry their own numbered fields ("1. Place of
        # Birth", "2. Lay Name") that read exactly like section markers, so
        # scanning past this boundary turns every field into a false split.
        line_text_probe = clean_text(" ".join(w.text for w in line.words))
        if SCHEDULE_BOUNDARY_RE.search(line_text_probe) or FORM_CAPTION_RE.match(
            line_text_probe
        ):
            break

        letters = [c for c in line_text_probe if c.isalpha()]
        is_cross_heading = len(letters) >= CROSS_HEADING_MIN_LETTERS and (
            CROSS_HEADING_RE.match(line_text_probe)
        )
        if is_cross_heading:
            if line.words:
                last_word = line.words[-1].text
            continue

        marker = find_section_marker(
            line, marker_min_x=marker_min_x, last_word_of_previous_line=last_word
        )
        if line.words:
            last_word = line.words[-1].text
        if marker and current is not None:
            marker_index, number, glued = marker
            # A leading digit can be lost off a marker when it merges into
            # the word before it in the PDF's text stream ("streams1
            # 05.Every" for ".. streams. 105.Every", or "in6" for ".. in
            # 62D."). Only repaired when the short number is literally a
            # suffix of the section that must come next -- either the next
            # base number, or a further letter on the section still open --
            # never for a number that merely looks close, so a genuine gap
            # is never masked.
            base_match = re.match(r"(\d+)([A-Za-z]*)", number)
            trunc_base, trunc_suffix = base_match.group(1), base_match.group(2)
            current_base = int(re.match(r"\d+", current.number).group())
            repaired = False
            for candidate_base in (current_base, current_base + 1):
                candidate = str(candidate_base)
                if candidate.endswith(trunc_base) and len(trunc_base) < len(candidate):
                    number = candidate + trunc_suffix
                    repaired = True
                    break
            # A section number never goes backwards. A bare "2." deep inside,
            # say, section 327 is a subsection the source set without
            # parentheses (an Interpretation clause's second numbered limb,
            # typeset as "2." instead of "(2)"), not a new section -- so it
            # is left for the ordinary body/heading handling below to attach
            # to the section still open, rather than started as section 2.
            if not repaired and int(base_match.group(1)) < current_base:
                marker = None
            else:
                marker = (marker_index, number, glued)

        if marker:
            marker_index, number, glued = marker
            if current is not None:
                sections.append(finalize_section(current))

            current = WorkingSection(number=number, page_start=line.page)
            current.pages_seen.add(line.page)

            heading_fragment = heading_text_from_line(
                line,
                body_x=body_x,
                margin_line_max_x=margin_line_max_x,
                stop_index=marker_index,
            )
            if heading_fragment:
                current.heading_lines.append(heading_fragment)

            rest_words = line.words[marker_index + 1 :]
            if glued is not None:
                text = clean_text(
                    " ".join([glued] + [word.text for word in rest_words])
                )
                indent = rest_words[0].x0 if rest_words else body_x
            else:
                text = clean_text(" ".join(word.text for word in rest_words))
                indent = rest_words[0].x0 if rest_words else body_x
            if text:
                current.body_blocks.append(BodyBlock(text, indent))
            continue

        if current is None:
            continue

        current.pages_seen.add(line.page)

        heading_fragment = heading_text_from_line(
            line,
            body_x=body_x,
            margin_line_max_x=margin_line_max_x,
        )
        if heading_fragment:
            current.heading_lines.append(heading_fragment)

        body_fragment = body_text_from_line(
            line,
            body_x=body_x,
            full_width_body_min_x=full_width_body_min_x,
        )
        if body_fragment:
            current.body_blocks.append(body_fragment)

    if current is not None:
        sections.append(finalize_section(current))

    return sections


def numeric_part(section_number: str) -> int:
    match = re.match(r"\d+", section_number)
    if not match:
        raise ValueError(f"Invalid section number: {section_number!r}")
    return int(match.group())


def validate_sections(sections: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if not sections:
        return [
            "No sections found. The PDF may be scanned or the column thresholds may need adjustment."
        ]

    numbers = [numeric_part(section["section_number"]) for section in sections]
    full_numbers = [section["section_number"] for section in sections]
    duplicates = sorted(
        {n for n in full_numbers if full_numbers.count(n) > 1},
        key=numeric_part,
    )
    if duplicates:
        warnings.append(f"Duplicate section numbers: {duplicates}")

    expected = set(range(min(numbers), max(numbers) + 1))
    missing = sorted(expected - set(numbers))
    if missing:
        warnings.append(f"Missing numeric section numbers: {missing}")

    if numbers != sorted(numbers):
        warnings.append("Section numbers are not in ascending order.")

    empty_headings = [
        section["section_number"] for section in sections if not section["heading"]
    ]
    if empty_headings:
        warnings.append(f"Sections with empty headings: {empty_headings}")

    empty_text = [
        section["section_number"] for section in sections if not section["text"]
    ]
    if empty_text:
        warnings.append(f"Sections with empty text: {empty_text}")

    return warnings


def build_document(args: argparse.Namespace, sections: list[dict[str, Any]]) -> dict[str, Any]:
    raw_text = "\n\n".join(section["raw_text"] for section in sections)
    normalized_text = "\n\n".join(section["normalized_text"] for section in sections)
    return {
        "source_id": args.source_id,
        "official_title": args.official_title,
        "act_number": args.act_number,
        "year": args.year,
        "source_url": args.source_url,
        "retrieved_at": args.retrieved_at,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "verification_status": args.verification_status,
        "source_errors": [],
        "content_hash": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "sections": sections,
    }


def write_json(document: dict[str, Any], stream: TextIO) -> None:
    json.dump(document, stream, ensure_ascii=False, indent=2)
    stream.write("\n")


def write_jsonl(sections: list[dict[str, Any]], stream: TextIO) -> None:
    for section in sections:
        stream.write(json.dumps(section, ensure_ascii=False) + "\n")


def write_csv(sections: list[dict[str, Any]], stream: TextIO) -> None:
    fields = ["section_number", "heading", "text", "page_start", "page_end"]
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(sections)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract sections from two-column legislation PDFs."
    )
    parser.add_argument("input", type=Path, help="Input PDF with a text layer")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path; stdout when omitted"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "jsonl", "csv"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--body-x", type=float, default=165.0)
    parser.add_argument("--marker-min-x", type=float, default=150.0)
    parser.add_argument("--margin-line-max-x", type=float, default=110.0)
    parser.add_argument("--full-width-body-min-x", type=float, default=110.0)
    parser.add_argument("--line-tolerance", type=float, default=2.0)
    parser.add_argument("--top-margin", type=float, default=45.0)
    parser.add_argument("--bottom-margin", type=float, default=40.0)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 when validation warnings are found",
    )
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
    sections = extract_sections(
        args.input,
        body_x=args.body_x,
        marker_min_x=args.marker_min_x,
        margin_line_max_x=args.margin_line_max_x,
        full_width_body_min_x=args.full_width_body_min_x,
        line_tolerance=args.line_tolerance,
        top_margin=args.top_margin,
        bottom_margin=args.bottom_margin,
    )
    warnings = validate_sections(sections)
    document = build_document(args, sections)

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
