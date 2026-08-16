from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, TextIO


SPACE_RE = re.compile(r"\s+")
SECTION_START_RE = re.compile(r"^(\d+[A-Za-z]?)\.\s*(.*)$", re.DOTALL)
PART_RE = re.compile(r"^PART\s+([IVXLCDM]+)\s*$", re.IGNORECASE)
SUBSECTION_RE = re.compile(r"^\((\d+)\)\s*(.*)$", re.DOTALL)
PROVISION_MARKER_RE = re.compile(r"^\((\d+|[A-Za-z]+)\)\s*(.*)$", re.DOTALL)
TRAILING_PROVISION_MARKER_RE = re.compile(
    r"^(.*(?:;|:))\s+\(([A-Za-z]+)\)\s*$", re.DOTALL
)

KNOWN_SOURCE_ERRORS = [
    ("section_heading", "2", "National Development Authority", "Heading appears to omit 'Housing'."),
    ("section_text", "5", "other wise", "Suspicious split word in the source text."),
    ("section_text", "8", "may. with", "Suspicious punctuation in the source text."),
    ("section_text", "17", "deter mined", "Suspicious split word in the source text."),
    ("section_text", "18", "Chair man", "Suspicious split word in the source text."),
    ("section_text", "27", "sub section", "Suspicious split word in the source text."),
    ("section_text", "38", "foe served", "Suspicious wording in the source text."),
    ("section_text", "58", "sub section", "Suspicious split word in the source text."),
    ("section_text", "72", "not excluding one year", "Potentially legally significant source wording; verify against the Gazette."),
    ("part_title", "VII", "by the General", "Part title appears to end abruptly in the source."),
]


def clean_text(value: str) -> str:
    """Collapse layout whitespace while preserving the words and punctuation."""
    return SPACE_RE.sub(" ", value).strip(" |\t\r\n")


def restore_html(source: str) -> str:
    """Restore HTML tags escaped by a Markdown paste/export."""
    # Do not remove all backslashes: the legislative text may contain genuine
    # backslashes. Only undo escaping used around HTML syntax and quotes.
    return (
        source.replace(r"\<", "<")
        .replace(r"\>", ">")
        .replace(r'\"', '"')
        .replace(r"\'", "'")
    )


@dataclass
class Event:
    kind: str
    text: str
    raw_text: str
    td_width: str | None = None
    depth: int = 0


class LegislationHTMLParser(HTMLParser):
    """Convert relevant HTML elements into an ordered stream of text events."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[Event] = []
        self._td_width_stack: list[str | None] = []
        self._captures: list[dict[str, Any]] = []

    @property
    def current_td_width(self) -> str | None:
        return self._td_width_stack[-1] if self._td_width_stack else None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = {name.lower(): value for name, value in attrs}

        # A historical page may put nested tables/divs inside the div that
        # starts with the section number. Emit the parent's direct text (such
        # as "2.") before entering the child so source order is preserved.
        if tag in {"div", "center"} and self._captures:
            self._flush_capture(self._captures[-1])

        if tag == "td":
            width = attributes.get("width")
            self._td_width_stack.append(width.lower() if width else None)

        if tag in {"div", "center"}:
            self._captures.append(
                {
                    "tag": tag,
                    "parts": [],
                    "td_width": self.current_td_width,
                    "depth": sum(
                        1 for width in self._td_width_stack if width_number(width) == 340
                    ),
                }
            )

        if tag == "br":
            for capture in self._captures:
                capture["parts"].append(" ")

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # Self-closing <td ... /> cells occur in this source. They should not
        # remain on the ancestor stack.
        if tag.lower() == "td":
            return
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        # Markdown table separators can occur between nested HTML tags. They
        # are layout noise, not legislative content.
        if re.fullmatch(r"[\s|]*", data):
            return
        if self._captures:
            # Add text only to the innermost element. Adding it to every open
            # parent would duplicate nested subsection text.
            self._captures[-1]["parts"].append(data)

    def _flush_capture(self, capture: dict[str, Any]) -> None:
        raw_text = "".join(capture["parts"]).strip()
        text = clean_text(raw_text)
        capture["parts"].clear()
        if text:
            self.events.append(
                Event(
                    capture["tag"],
                    text,
                    raw_text,
                    capture.get("td_width"),
                    capture.get("depth", 0),
                )
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in {"div", "center"}:
            # Find the nearest still-open matching capture. This makes the
            # parser tolerant of imperfect historical HTML.
            index = next(
                (
                    i
                    for i in range(len(self._captures) - 1, -1, -1)
                    if self._captures[i]["tag"] == tag
                ),
                None,
            )
            if index is not None:
                capture = self._captures.pop(index)
                self._flush_capture(capture)

        if tag == "td" and self._td_width_stack:
            self._td_width_stack.pop()


def width_number(width: str | None) -> int | None:
    if not width:
        return None
    match = re.search(r"\d+", width)
    return int(match.group()) if match else None


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


def parse_hierarchy(blocks: list[tuple[str, int]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reconstruct subsection, paragraph and subparagraph nesting."""
    expanded_blocks: list[tuple[str, int]] = []
    for block, level in blocks:
        trailing = TRAILING_PROVISION_MARKER_RE.match(clean_text(block))
        if trailing:
            text, marker = trailing.groups()
            expanded_blocks.extend(((text, level), (f"({marker})", level)))
        else:
            expanded_blocks.append((block, level))

    subsections: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []
    current_subsection: dict[str, Any] | None = None
    current_paragraph: dict[str, Any] | None = None
    current_subparagraph: dict[str, Any] | None = None
    subsection_level = 0
    paragraph_level = 0

    for block, level in expanded_blocks:
        match = PROVISION_MARKER_RE.match(clean_text(block))
        if not match:
            target = current_subparagraph or current_paragraph or current_subsection
            if target is not None:
                target["_blocks"].append(block)
            continue

        number, body = match.groups()
        if number.isdigit():
            expected_number = 1 if not subsections else int(subsections[-1]["number"]) + 1
            if int(number) != expected_number:
                # A wrapped line can begin with a parenthesized numeric cross-
                # reference (for example, "(1) and the certificates...").
                # Do not turn that reference into a duplicate subsection.
                target = current_subparagraph or current_paragraph or current_subsection
                if target is not None:
                    target["_blocks"].append(block)
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


def extract_sections(source: str) -> list[dict[str, Any]]:
    parser = LegislationHTMLParser()
    parser.feed(restore_html(source))
    parser.close()

    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_heading: str | None = None
    pending_part_title = False
    current_part_number: str | None = None
    current_part_title: str | None = None

    def finish_current() -> None:
        nonlocal current
        if current is None:
            return
        blocks = current.pop("_blocks")
        raw_blocks = current.pop("_raw_blocks")
        hierarchy_blocks = current.pop("_hierarchy_blocks")
        current["raw_text"] = "\n".join(raw_blocks).strip()
        current["normalized_text"] = clean_text(" ".join(blocks))
        current["text"] = current["normalized_text"]
        subsections, paragraphs = parse_hierarchy(hierarchy_blocks)
        current["subsections"] = subsections
        current["paragraphs"] = paragraphs
        sections.append(current)
        current = None

    for event in parser.events:
        text = event.text

        if event.kind == "center":
            part_match = PART_RE.match(text)
            if part_match:
                current_part_number = part_match.group(1).upper()
                current_part_title = None
                pending_part_title = True
            elif pending_part_title:
                current_part_title = text
                pending_part_title = False
            continue

        width = width_number(event.td_width)

        # Marginal notes/headings are consistently stored in the 80 px cell.
        if width == 80:
            pending_heading = text
            continue

        # A true section begins in the main 420 px body cell. Requiring both
        # conditions prevents "section 6" cross-references and numbered lists
        # from being treated as new sections.
        section_match = SECTION_START_RE.match(text) if width == 420 else None
        if section_match:
            finish_current()
            number, first_text = section_match.groups()
            current = {
                "section_number": number,
                "heading": pending_heading,
                "part_number": current_part_number,
                "part_title": current_part_title,
                "_blocks": [first_text] if first_text else [],
                "_raw_blocks": [first_text] if first_text else [],
                "_hierarchy_blocks": [],
            }
            pending_heading = None
            continue

        if current is not None:
            # 340 px cells contain subsections, paragraphs and subparagraphs.
            # A 420 px continuation is also accepted for simple sections.
            if width in {340, 420}:
                current["_blocks"].append(text)
                current["_raw_blocks"].append(event.raw_text)
                current["_hierarchy_blocks"].append((event.raw_text, event.depth))

    finish_current()
    return sections


def validate_sections(sections: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if not sections:
        return ["No sections were extracted."]

    numeric_numbers = []
    for section in sections:
        match = re.match(r"\d+", section["section_number"])
        if match:
            numeric_numbers.append(int(match.group()))

    duplicates = sorted({n for n in numeric_numbers if numeric_numbers.count(n) > 1})
    if duplicates:
        warnings.append(f"Duplicate numeric section numbers: {duplicates}")

    if numeric_numbers:
        expected = set(range(min(numeric_numbers), max(numeric_numbers) + 1))
        missing = sorted(expected - set(numeric_numbers))
        if missing:
            warnings.append(f"Missing numeric section numbers: {missing}")

    empty = [s["section_number"] for s in sections if not s["text"]]
    if empty:
        warnings.append(f"Sections with empty text: {empty}")

    return warnings


def source_errors_for(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_number = {section["section_number"]: section for section in sections}
    errors: list[dict[str, str]] = []
    for kind, location, observed, note in KNOWN_SOURCE_ERRORS:
        if kind == "part_title":
            haystack = " ".join(
                section.get("part_title") or ""
                for section in sections
                if section.get("part_number") == location
            )
            label = f"part {location} title"
        else:
            section = by_number.get(location, {})
            field = "heading" if kind == "section_heading" else "raw_text"
            haystack = str(section.get(field) or "")
            label = f"section {location} {'heading' if field == 'heading' else 'text'}"
        if observed in haystack:
            errors.append(
                {
                    "location": label,
                    "observed_text": observed,
                    "note": note,
                    "verification_status": "needs_authoritative_source_check",
                }
            )
    return errors


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
        "source_errors": source_errors_for(sections),
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
    fieldnames = ["section_number", "heading", "part_number", "part_title", "text"]
    writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(sections)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract structured sections from escaped legislation HTML."
    )
    parser.add_argument("input", type=Path, help="Input Markdown or HTML file")
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 if validation warnings are found",
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
    source = args.input.read_text(encoding="utf-8")
    sections = extract_sections(source)
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

    print(
        f"Extracted {len(sections)} sections"
        + (f" to {args.output}" if args.output else ""),
        file=sys.stderr,
    )
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    return 2 if warnings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
