"""Parse the LankaLaw consolidated-statute HTML into sections and chains.

These pages are marked up with semantic classes rather than layout, which makes
them a far better structural source than the two-column PDFs:

    actname               the statute's short name
    ordinancestitle       "Ordinance Nos," / "Act Nos," / "Law Nos," chain heads
    sectioncontent        a section number, on its own
    sectionshorttitle     the marginal-note heading, with inline markers
    morginalnotes         further inline markers (their spelling)
    subsectioncontent     the body text
    subsectionshorttitle  markers attached to a subsection

Serialisation order matters. The marginal note sits in the left column of the
printed page, so it is emitted *before* the section number it belongs to, and
the body follows after. The parser therefore holds a pending heading and
attaches it to the next section number it sees.

An inline marker reads `[ 3,45 of 1982]`, meaning section 3 of Act No. 45 of
1982 changed this provision. That is the same shape the section index already
uses, so the output can be merged with it.

Writes `data/processed/lankalaw-html-sections.json` and
`data/processed/lankalaw-html-chains.csv`. Nothing is verified: LankaLaw is a
private republisher, not the Government Printer.

    uv run python scripts/parse_lankalaw_html.py
    uv run python scripts/parse_lankalaw_html.py --source-id SRC012 --show
"""

from __future__ import annotations

import argparse
import csv
import html as html_module
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = REPO_ROOT / "data/legal-sources/library/statutes/HTML"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
SECTIONS_OUT = REPO_ROOT / "data/processed/lankalaw-html-sections.json"
CHAINS_OUT = REPO_ROOT / "data/processed/lankalaw-html-chains.csv"

CLASSES = (
    "actname|datesup|ordinancestitle|sectioncontent|sectionshorttitle"
    "|morginalnotes|subsectionshorttitle|subsectioncontent"
)
SPAN = re.compile(rf'class="({CLASSES})"[^>]*>(.*?)</font>', re.IGNORECASE | re.DOTALL)
NUMBER_CELL = re.compile(r'<font size="1">\s*(\d{1,3})\s*of\s*(\d{4})\s*</font>', re.IGNORECASE)
CHAIN_HEAD = re.compile(r'class="ordinancestitle"[^>]*>\s*(Ordinance|Act|Law)s?\s*Nos?', re.IGNORECASE)
MARKER = re.compile(r"\[\s*([0-9]{1,3}[A-Z]?)\s*,\s*([^\]]+?)\s*\]")
SECTION_NUMBER = re.compile(r"^\d{1,3}[A-Z]{0,2}$")
FILE_NUMBER_YEAR = re.compile(r"^(\d{1,3})-(1[78]\d{2}|19\d{2}|20\d{2})-")


def text_of(fragment: str) -> str:
    plain = html_module.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", plain.replace(" ", " ")).strip()


def parse_markers(text: str) -> tuple[str, list[dict[str, str]]]:
    """Split trailing `[n, Act of Year]` markers off a heading."""
    markers = []
    for match in MARKER.finditer(text):
        act = re.sub(r"\s+", " ", match.group(2)).strip()
        if not re.search(r"\d{4}", act):
            continue
        markers.append(
            {
                "amending_section": match.group(1),
                "amending_act": act,
                "verbatim": match.group(0),
            }
        )
    return MARKER.sub("", text).strip(" .;,"), markers


def parse_chain(page: str) -> list[tuple[str, int, int]]:
    """(instrument_type, number, year) in printed order."""
    events: list[tuple[int, int, str, object]] = []
    for match in CHAIN_HEAD.finditer(page):
        events.append((match.start(), 0, "type", match.group(1).title()))
    for match in NUMBER_CELL.finditer(page):
        events.append((match.start(), 1, "pair", (int(match.group(1)), int(match.group(2)))))
    events.sort()

    chain, current = [], None
    for _, _, kind, value in events:
        if kind == "type":
            current = value
        elif current:
            chain.append((current, *value))
    return list(dict.fromkeys(chain))


def parse_sections(page: str) -> list[dict]:
    """Sections in printed order, each with its heading, markers and body."""
    sections: list[dict] = []
    pending_heading, pending_markers = "", []

    for class_name, fragment in SPAN.findall(page):
        value = text_of(fragment)
        if not value:
            continue
        name = class_name.lower()

        if name == "datesup":
            # Section 1's heading is printed alongside the commencement date.
            tail = value.split("]")[-1].strip()
            if tail:
                pending_heading, pending_markers = parse_markers(tail)
        elif name in {"sectionshorttitle", "morginalnotes"}:
            heading, markers = parse_markers(value)
            if name == "sectionshorttitle":
                pending_heading = heading or pending_heading
            pending_markers.extend(markers)
        elif name == "subsectionshorttitle":
            _, markers = parse_markers(value)
            if sections:
                sections[-1]["amendment_markers"].extend(markers)
        elif name == "sectioncontent" and SECTION_NUMBER.match(value):
            sections.append(
                {
                    "section": value,
                    "heading": pending_heading,
                    "heading_source": "lankalaw-html",
                    "present_in": ["lankalaw-html"],
                    "amendment_markers": pending_markers,
                    "text": "",
                }
            )
            pending_heading, pending_markers = "", []
        elif name == "subsectioncontent" and sections:
            sections[-1]["text"] = (sections[-1]["text"] + " " + value).strip()

    for section in sections:
        seen, unique = set(), []
        for marker in section["amendment_markers"]:
            key = (marker["amending_section"], marker["amending_act"])
            if key not in seen:
                seen.add(key)
                unique.append(marker)
        section["amendment_markers"] = unique
    return sections


def registry_by_number_year() -> dict[tuple[int, int], dict[str, str]]:
    with REGISTRY.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    mapping = {}
    for row in rows:
        number, year = row["act_or_ordinance_no"], row["year"]
        if number.isdigit() and year.isdigit() and year != "0":
            mapping[(int(number), int(year))] = row
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", help="only this statute")
    parser.add_argument("--show", action="store_true", help="print what was parsed")
    args = parser.parse_args()

    lookup = registry_by_number_year()
    sections_out: dict[str, list[dict]] = {}
    chain_rows: list[dict] = []
    skipped: list[str] = []

    for file in sorted(HTML_DIR.glob("*.html")):
        match = FILE_NUMBER_YEAR.match(file.stem)
        if not match:
            skipped.append(f"{file.name}: filename carries no Act number and year")
            continue
        key = (int(match.group(1)), int(match.group(2)))
        row = lookup.get(key)
        if not row:
            skipped.append(f"{file.name}: No. {key[0]} of {key[1]} is not in the registry")
            continue
        if args.source_id and row["source_id"] != args.source_id:
            continue

        page = file.read_text(encoding="utf-8", errors="replace")
        sections = parse_sections(page)
        chain = parse_chain(page)
        if not sections:
            skipped.append(f"{file.name}: no sections found")
            continue

        sections_out[row["source_id"]] = sections
        for order, (kind, number, year) in enumerate(chain):
            chain_rows.append(
                {
                    "source_id": row["source_id"],
                    "statute": row["official_title"],
                    "instrument_type": kind,
                    "instrument_no": number,
                    "instrument_year": year,
                    "role": "principal" if (number, year) == key else "amending",
                    "chain_order": order,
                    "status": "unverified",
                }
            )

        if args.show:
            print(f"=== {row['source_id']} {row['official_title']} ===")
            print(f"  chain: {', '.join(f'{k} {n} of {y}' for k, n, y in chain)}")
            print(f"  sections: {len(sections)}")
            for section in sections[:8]:
                marks = " ".join(m["verbatim"] for m in section["amendment_markers"])
                print(f"    s.{section['section']:<4} {section['heading'][:52]:54} {marks}")

    if args.source_id:
        return 0

    SECTIONS_OUT.write_text(
        json.dumps(sections_out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with CHAINS_OUT.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Amendment chains read from the LankaLaw consolidated HTML pages.\n"
            "# Same shape as amendment-chains.csv, from a different source.\n"
            "# Generated by scripts/parse_lankalaw_html.py. status=unverified.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(chain_rows[0]))
        writer.writeheader()
        writer.writerows(chain_rows)

    total_sections = sum(len(v) for v in sections_out.values())
    with_markers = sum(
        1 for v in sections_out.values() for s in v if s["amendment_markers"]
    )
    print(f"parsed {len(sections_out)} statutes, {total_sections} sections")
    print(f"  {with_markers} sections carry an amendment marker")
    print(f"  {sum(1 for r in chain_rows if r['role'] == 'amending')} amending instruments in chains")
    print(f"wrote {SECTIONS_OUT.relative_to(REPO_ROOT)}")
    print(f"wrote {CHAINS_OUT.relative_to(REPO_ROOT)}")
    if skipped:
        print(f"{len(skipped)} skipped:")
        for line in skipped:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
