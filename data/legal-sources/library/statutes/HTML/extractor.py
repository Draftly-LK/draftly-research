from __future__ import annotations

import argparse
import csv
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
    td_width: str | None = None


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
        text = clean_text("".join(capture["parts"]))
        capture["parts"].clear()
        if text:
            self.events.append(
                Event(capture["tag"], text, capture.get("td_width"))
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


def parse_subsections(blocks: list[str]) -> list[dict[str, str]]:
    """Build top-level subsection records from block boundaries."""
    subsections: list[dict[str, str]] = []
    current: dict[str, Any] | None = None

    for block in blocks:
        match = SUBSECTION_RE.match(block)
        if match:
            if current:
                current["text"] = clean_text(" ".join(current.pop("blocks")))
                subsections.append(current)
            current = {
                "number": match.group(1),
                "blocks": [match.group(2)] if match.group(2) else [],
            }
        elif current:
            current["blocks"].append(block)

    if current:
        current["text"] = clean_text(" ".join(current.pop("blocks")))
        subsections.append(current)

    return subsections


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
        current["text"] = clean_text(" ".join(blocks))
        current["subsections"] = parse_subsections(blocks)
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
            }
            pending_heading = None
            continue

        if current is not None:
            # 340 px cells contain subsections, paragraphs and subparagraphs.
            # A 420 px continuation is also accepted for simple sections.
            if width in {340, 420}:
                current["_blocks"].append(text)

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


def write_json(sections: list[dict[str, Any]], stream: TextIO) -> None:
    json.dump(sections, stream, ensure_ascii=False, indent=2)
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
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    source = args.input.read_text(encoding="utf-8")
    sections = extract_sections(source)
    warnings = validate_sections(sections)

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
            write_json(sections, stream)
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