"""Build a canonical tree from a statute harvested off CommonLII.

`harvest_commonlii_statutes.py` assembles one HTML file per Act from CommonLII's
`num_act` database, one `<section>` per statutory section. Nothing parsed those
files, so a harvested Act sat on disk as prose.

CommonLII's markup carries structure only down to the section: a marginal note
and one flat run of text. Everything below that -- subsections, paragraphs,
definitions -- is inferred from the enumerators in the prose, using the same
`classify`/`nest` pair `build_canonical_statutes.py` applies to the LankaLaw
pages, so both sources produce the same shape and can be compared node for node.

What that inference cannot do is invent structure the transcription lost. Where a
subsection is simply absent from the page, this records the gap rather than
smoothing over it: `expected_subsections_missing` lists every subsection number
the Act's own cross-references rely on that no section actually carries.

Nothing here is verified. CommonLII is a priority-3 consolidator under
`data/legal-sources/conveyancing-source-checklist.md`, not the Government
Printer, and the official PDF remains the text authority.

    uv run python scripts/parse_commonlii_statute.py --source-id SRC023 --show
    uv run python scripts/parse_commonlii_statute.py
"""

from __future__ import annotations

import argparse
import collections
import html as html_module
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_canonical_statutes import (  # noqa: E402
    DEFINITION,
    classify,
    cross_references,
    nest,
    quality_flags,
    read_csv,
)

HTML_DIR = REPO_ROOT / "data/legal-sources/library/statutes/HTML"
MANIFEST = REPO_ROOT / "data/legal-sources/manifests/statute-html-commonlii.csv"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
COMMENCEMENT = REPO_ROOT / "data/processed/statute_commencement.csv"
OUT_DIR = REPO_ROOT / "data/processed/canonical-statutes"

BLOCK = re.compile(
    r'<section class="section" id="([^"]+)">\s*'
    r'<h2 class="section-title">(.*?)</h2>\s*'
    r'(?:<p class="marginal-note">(.*?)</p>\s*)?'
    r'<div class="section-text">(.*?)</div>',
    re.S,
)
SOURCE_URL = re.compile(r'<meta name="source-url" content="([^"]+)"')
RETRIEVED_AT = re.compile(r'<meta name="retrieved-at" content="([^"]+)"')
SECTION_NUMBER_PREFIX = re.compile(r"^(\d{1,3}[A-Z]{0,2})\s*\.\s*")
# A run of prose broken at each enumerator that opens a block.
ENUMERATOR_SPLIT = re.compile(
    r"(?=\((?:\d{1,3}[A-Z]?|[a-z]{1,2}|[ivxlc]{1,6})\)\s)"
)
# `(2)` in "subject to the provisions of subsections (2) and (3)" is a citation,
# not the start of subsection (2). Splitting on the bare enumerator invented a
# subsection node for it, and section 5 grew four such phantoms out of
# "subsection (4) or subsection (5) of section 3". Citations are masked before
# the split and restored after, so only enumerators that open a block survive.
# The whole citation run is matched in one go, head included, so that a trailing
# "and (3)" is masked only when it continues a citation. Matching "and (n)" on
# its own would swallow real list items: paragraph (b) of section 3 (1) opens
# "and (b) such transfer is effected ...", and paragraph (f) of 3 (2) likewise.
CITATION = re.compile(
    r"""\b(?:sub-?sections?|sub-?paragraphs?|paragraphs?|sections?|schedules?)
        \s* (?:\d{1,3}[A-Z]{0,2}\s*)?                    # "section 18 (2)"
        \(\s*[0-9a-zA-Z]{1,4}\s*\)
        (?:\s*(?:,|and|or|to)\s*\(\s*[0-9a-zA-Z]{1,4}\s*\))*""",
    re.IGNORECASE | re.VERBOSE,
)
MASK_OPEN, MASK_CLOSE = "\x00", "\x01"


def mask_citations(text: str) -> str:
    """Hide the brackets of a citation so the enumerator split cannot see them."""
    def hide(match: re.Match) -> str:
        return match.group(0).replace("(", MASK_OPEN).replace(")", MASK_CLOSE)

    previous = None
    # Overlapping runs such as "(2) and (3) and (4)" need more than one pass.
    while previous != text:
        previous = text
        text = CITATION.sub(hide, text)
    return text


def unmask(text: str) -> str:
    return text.replace(MASK_OPEN, "(").replace(MASK_CLOSE, ")")
# "section 21 (2)" / "subsection (4) or subsection (5) of section 4"
SUBSECTION_REF = re.compile(r"\bsections?\s+(\d{1,3}[A-Z]{0,2})\s*\(\s*(\d{1,3}[A-Z]?)\s*\)")
# A definition opens with a quoted term followed by its defining verb. Splitting
# on the quote alone breaks inside a definition, because the closing quote of one
# term and the opening quote of the next look identical to a bare quote pattern:
# `" partition action" means an action under the Partition Act; "` matched, and
# cost the corpus that definition.
DEFINITION_START = re.compile(
    r'(?=["“]\s*[^"”]{2,60}?\s*["”]\s*,?\s*'
    r"(?:means|includes|shall\b|has the same meaning|with reference))",
    re.IGNORECASE,
)


def text_of(fragment: str) -> str:
    plain = html_module.unescape(re.sub(r"<[^>]+>", " ", fragment or ""))
    return re.sub(r"\s+", " ", plain.replace("\xa0", " ")).strip()


def raw_of(fragment: str) -> str:
    plain = html_module.unescape(re.sub(r"<[^>]+>", "", fragment or ""))
    return re.sub(r"[ \t]+", " ", plain.replace("\xa0", " ")).strip()


def split_definitions(body: str, self_title: str) -> list[dict]:
    """One node per defined term, for an interpretation section."""
    parts = DEFINITION_START.split(body)
    nodes = []
    for part in parts:
        part = part.strip(" -;")
        if not part:
            continue
        match = DEFINITION.match(part)
        if not match:
            continue
        term = re.sub(r"\s+", " ", match.group(1)).strip()
        text = match.group(2).strip().rstrip(";").strip()
        if not term or not text:
            continue
        nodes.append(
            {
                "type": "definition",
                "term": term,
                "raw_text": part,
                "text": text,
                "amendment_events": [],
                "cross_references": cross_references(text, self_title),
            }
        )
    return nodes


# "subsection (4) or subsection (5) of section 3" names 3(4) AND 3(5). The
# shared extractor keeps only the subsection nearest the section number, so
# section 5 recorded 3(5) and 4(4) and dropped 3(4) and 4(3).
SUBSECTION_RUN = re.compile(
    r"\bsub-?sections?\s*\(\s*(\w{1,4})\s*\)"
    r"((?:\s*(?:,|or|and)\s*sub-?sections?\s*\(\s*\w{1,4}\s*\))*)"
    r"\s+of\s+section\s+(\d{1,3}[A-Z]{0,2})",
    re.IGNORECASE,
)
RUN_MEMBER = re.compile(r"\(\s*(\w{1,4})\s*\)")


def expand_subsection_runs(text: str, self_title: str, existing: list[dict]) -> list[dict]:
    """Every subsection named in a run, not just the one next to the section."""
    seen = {(r.get("target_section"), r.get("target_subsection")) for r in existing}
    extra = []
    for match in SUBSECTION_RUN.finditer(text):
        section = match.group(3)
        members = [match.group(1)] + RUN_MEMBER.findall(match.group(2) or "")
        for member in members:
            key = (section, member)
            if key in seen:
                continue
            seen.add(key)
            extra.append(
                {
                    "kind": "internal",
                    "target_document": self_title,
                    "target_section": section,
                    "target_subsection": member,
                    "verbatim": match.group(0),
                }
            )
    return extra


def fix_roman_run(blocks: list[dict]) -> None:
    """`(i)` opening a roman run is a subparagraph, not paragraph nine.

    `classify` resolves the (i) ambiguity in favour of a paragraph, which is
    right for a lettered list reaching i but wrong when (ii) follows: section 8
    came out with (i) as a sibling of (b) and (ii)-(iii) nested inside (i).
    """
    for index, block in enumerate(blocks):
        if block["type"] != "paragraph" or block.get("number", "").lower() != "i":
            continue
        following = blocks[index + 1] if index + 1 < len(blocks) else None
        if following and str(following.get("number", "")).lower() == "ii":
            block["type"] = "subparagraph"
            block["number_style"] = "roman"
            block["type_note"] = (
                "Typed subparagraph because the next block is (ii); a lone (i) after a lettered "
                "run would be paragraph nine."
            )


def parse_section_body(body: str, self_title: str) -> tuple[str, list[dict]]:
    """(opening text, child blocks) for one section's flat run of prose."""
    pieces = [unmask(p).strip()
              for p in ENUMERATOR_SPLIT.split(mask_citations(body)) if p.strip()]
    if not pieces:
        return body, []
    # A section whose only enumerated block is "(1)" still has a subsection; it
    # would otherwise keep the label inside the section's own text.
    if len(pieces) == 1 and classify(pieces[0])[0] == "text":
        return body, []

    opening, blocks = "", []
    for index, piece in enumerate(pieces):
        kind, label, remainder = classify(piece)
        if kind == "text":
            if index == 0:
                opening = piece
            else:
                blocks.append(
                    {
                        "type": "text",
                        "number": "",
                        "raw_text": piece,
                        "text": piece,
                        "amendment_events": [],
                        "cross_references": cross_references(piece, self_title),
                    }
                )
            continue
        blocks.append(
            {
                "type": kind,
                "number": label,
                "raw_text": piece,
                "text": remainder,
                "amendment_events": [],
                "cross_references": cross_references(remainder, self_title),
            }
        )
    fix_roman_run(blocks)
    for block in blocks:
        block["cross_references"] += expand_subsection_runs(
            block.get("text", ""), self_title, block["cross_references"]
        )
    return opening, nest(blocks)


# A provision that stops on a connective or an unclosed clause did not finish.
# CommonLII drops text mid-sentence in places, and a parse that says nothing
# about it reads as "complete".
# Only an unpunctuated stop on a word that cannot end a provision. A list item
# closing on ";" or "," or "and" is ordinary drafting; flagging those buried the
# two real cases in forty-five false ones.
# Only an unpunctuated stop on a word that cannot end a provision. A list item
# closing on ";" or "," or "and" is ordinary drafting; flagging those buried the
# one real case in forty-five false ones. The lookbehind drops ", and" / "; or",
# which close a limb rather than break off mid-clause.
UNFINISHED = re.compile(
    r"(?<![,;:])\s(?:of|to|the|a|an|by|for|in|into|upon|under|which|that|with|"
    r"as|at|from|is|are|be|been|shall|may|such|any|and|or|not)$",
    re.IGNORECASE,
)


def truncated_provisions(sections: list[dict]) -> list[dict]:
    """Provisions whose text stops mid-sentence in the source."""
    found = []

    def walk(nodes: list[dict], path: str) -> None:
        for node in nodes:
            label = node.get("number") or node.get("term") or ""
            here = f"{path}({label})" if path and label else (path or label)
            text = (node.get("text") or "").strip()
            if text and UNFINISHED.search(text):
                found.append(
                    {
                        "at": here,
                        "ends_with": text[-70:],
                        "note": "the source stops here; no full stop and no following text",
                    }
                )
            walk(node.get("children", []), here)

    walk(sections, "")
    return found


def missing_subsections(sections: list[dict]) -> list[dict]:
    """Subsections the Act's own cross-references need but no section carries."""
    held: dict[str, set[str]] = collections.defaultdict(set)
    for node in sections:
        for child in node.get("children", []):
            if child["type"] == "subsection":
                held[node["number"]].add(str(child["number"]))

    numbers = {n["number"] for n in sections}
    wanted: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for node in sections:
        blob = json.dumps(node, ensure_ascii=False)
        for target, subsection in SUBSECTION_REF.findall(blob):
            if target in numbers:
                wanted[(target, subsection)].add(node["number"])

    gaps = []
    for (target, subsection), citers in sorted(wanted.items()):
        if subsection in held.get(target, set()):
            continue
        # A section with no subsections at all is not evidence of a gap unless
        # something cites one.
        gaps.append(
            {
                "section": target,
                "subsection": subsection,
                "cited_by": sorted(citers),
                "note": f"section {target} ({subsection}) is cited but this edition does not carry it",
            }
        )
    return gaps


def parse(page: str, self_title: str) -> tuple[list[dict], str, list[dict]]:
    """(body, long title, quality flags from the raw text)."""
    long_title, sections = "", []
    for block_id, _, note, body_html in BLOCK.findall(page):
        body = text_of(body_html)
        if block_id == "longtitle":
            long_title = body
            continue

        number_match = SECTION_NUMBER_PREFIX.match(body)
        number = number_match.group(1) if number_match else block_id.lstrip("s")
        rest = body[number_match.end():] if number_match else body

        node = {
            "type": "section",
            "number": number,
            "heading": text_of(note),
            "raw_text": raw_of(body_html),
            "text": "",
            "amendment_events": [],
            "cross_references": [],
        }
        if re.search(r"\bunless the context otherwise requires\b", rest, re.IGNORECASE):
            lead, _, tail = rest.partition("-")
            node["text"] = lead.strip()
            node["cross_references"] = cross_references(lead, self_title)
            children = split_definitions(tail, self_title)
            if children:
                node["children"] = children
        else:
            opening, children = parse_section_body(rest, self_title)
            node["text"] = opening
            node["cross_references"] = cross_references(opening or rest, self_title)
            node["cross_references"] += expand_subsection_runs(
                opening or rest, self_title, node["cross_references"]
            )
            if children:
                node["children"] = children
        sections.append(node)
    return sections, long_title, quality_flags(text_of(page))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    rows = read_csv(MANIFEST) if MANIFEST.exists() else []
    registry = {r["source_id"]: r for r in read_csv(REGISTRY)}
    commencement = {r["source_id"]: r["commencement"] for r in read_csv(COMMENCEMENT)}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for row in rows:
        source_id = row["source_id"]
        if args.source_id and source_id != args.source_id:
            continue
        recorded = row.get("local_html_path") or row.get("local_path") or ""
        file = REPO_ROOT / recorded if recorded else HTML_DIR / f"{source_id}.html"
        if not file.exists():
            print(f"  {source_id}: {file} is not on disk")
            continue

        registry_row = registry.get(source_id, {})
        title = registry_row.get("official_title") or row.get("title", source_id)
        page = file.read_text(encoding="utf-8", errors="replace")
        body, long_title, flags = parse(page, title)
        if not body:
            print(f"  {source_id}: no sections found in {file.name}")
            continue

        number = int(registry_row.get("act_or_ordinance_no") or 0)
        year = int(registry_row.get("year") or 0)
        source_url = SOURCE_URL.search(page)
        retrieved = RETRIEVED_AT.search(page)
        document = {
            "source_id": source_id,
            "title": title,
            "long_title": long_title,
            "long_title_raw": long_title,
            "long_title_correction_status": "none_needed",
            "citation": {"type": registry_row.get("source_type_label") or "Act",
                         "number": number, "year": year},
            "date_stated_in_source": "",
            "commencement": commencement.get(source_id) or None,
            "commencement_source": "statute_commencement.csv" if commencement.get(source_id) else "",
            "language": "en",
            "edition": {
                "publisher": "commonlii",
                "kind": "as enacted (Numbered Acts database)",
                "source_url": source_url.group(1) if source_url else "",
                "retrieved_at": retrieved.group(1) if retrieved else "",
                "local_path": file.relative_to(REPO_ROOT).as_posix(),
                "caveat": "priority-3 consolidator, not the Government Printer",
            },
            "amendments": [],
            "verification_status": "unverified",
            "content_completeness": "",
            "amendment_history_status": "not_recorded_by_this_source",
            "editorial_notes": [],
            "omitted_provisions": [],
            "overrides_applied": {},
            "quality_flags": flags,
            "expected_subsections_missing": missing_subsections(body),
            "truncated_in_source": truncated_provisions(body),
            "source_location": {},
            "alternate_edition_variants": [],
            "schedules_referenced": [],
            "schedules": [],
            "body": body,
        }

        target = OUT_DIR / f"{source_id}-{number}-{year}.json"
        target.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

        counts = collections.Counter()

        def walk(nodes):
            for node in nodes:
                counts[node["type"]] += 1
                walk(node.get("children", []))

        walk(body)
        print(f"  {source_id}: {dict(counts)} -> {target.relative_to(REPO_ROOT)}")
        if document["expected_subsections_missing"]:
            for gap in document["expected_subsections_missing"]:
                print(f"      missing: {gap['note']} (cited by {', '.join(gap['cited_by'])})")
        if args.show:
            for node in body[:30]:
                kids = len(node.get("children", []))
                print(f"    s.{node['number']:<4} {node['heading'][:52]:54} children={kids}")

    print(f"\nwrote {written} document(s) to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
