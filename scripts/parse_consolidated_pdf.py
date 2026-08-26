"""Parse a text-layer consolidated statute PDF into the canonical node model.

Most statutes reach the canonical layer through `build_canonical_statutes.py`,
which reads LankaLaw's HTML and its semantic classes. A few have no HTML edition
at all. The Land (Restrictions on Alienation) Act is one: LankaLaw does not
publish it, and the registry's own PDF is a scan with no text layer, so nothing
could read it until a consolidated PDF with real text appeared.

These PDFs are two-column. The marginal note runs down a narrow left column and
the operative text down a wide right one, and `pdftotext -layout` puts both on
the same line separated by a run of spaces:

    Short title and date 1.(1) This Act may be cited as the Land (Restrictions
    of operation.          No. 38 of 2014.

Reading the whole line would splice the note into the middle of the provision,
which is exactly the damage seen in the older LLM extractions. So each line is
split at the column gap, the two columns are rebuilt separately, and the note is
attached as the section heading rather than mixed into its text.

Output matches `build_canonical_statutes.py`, so both sources land in the same
shape and the same directory. A consolidated PDF carries the same inline
amendment markers the HTML does -- "[2, 21 of 2018]" for section 2 of Act No. 21
of 2018 -- but prints them down the marginal-note column rather than beside the
words they touch, so they are read as marking the section, not the paragraph
they happen to sit against.

    uv run python scripts/parse_consolidated_pdf.py --source-id SRC021
    uv run python scripts/parse_consolidated_pdf.py --source-id SRC021 --show
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_canonical_statutes import (  # noqa: E402
    DEFINITION,
    DEFINITION_VERB,
    parse_definition,
    PROVISO,
    SCHEDULE_REF,
    classify,
    cross_references,
    nest,
    quality_flags,
    split_markers,
    apply_heading_overrides,
)

REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
COMMENCEMENT = REPO_ROOT / "data/processed/statute_commencement.csv"
CHAINS = REPO_ROOT / "data/processed/amendment-chains.csv"
OUT_DIR = REPO_ROOT / "data/processed/canonical-statutes"
OVERRIDES = REPO_ROOT / "data/processed/canonical-overrides.json"

COLUMN_GAP = re.compile(r"\s{3,}")
# The gap between the two columns is not reliably wide. `Short title and date
# 1.(1) This Act may be cited...` separates them with a single space, so a
# whitespace rule alone leaves the note glued to the front of the line and hides
# the section number behind it. Where a line carries a marginal note followed by
# something that looks like the start of a section, split on that instead.
NOTE_THEN_SECTION = re.compile(
    # The note often ends in a full stop, as "Application of law. 2. This Law
    # shall apply...", so the note characters have to allow it. And a section can
    # open with a bare number, its text starting on the following line.
    r"^(?P<note>[A-Z][A-Za-z ,.'()&-]{0,45}?)\s+(?P<body>\d{1,3}[A-Z]{0,2}\.\s*(?:[({A-Z].*)?)$"
)
# A section opens with its number at the start of the body column, as "1." or
# "1.(1)" or "12A.". The trailing dot is what separates it from a stray figure.
SECTION_START = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s*(.*)$", re.DOTALL)
ENUM_START = re.compile(r"^\(\s*\w{1,4}\s*\)")
# A defined term opens a block just as a section number or an enumerator does.
# Without this the whole interpretation list is glued onto the section's text.
DEFINITION_LINE = re.compile(r"^[\"‘“']\s*[^\"’”']{2,60}[\"’”']")
# The long title runs from the opening words to the enacting formula.
# The article is not always printed -- an 1844 Ordinance opens "ORDINANCE TO
# MAKE PROVISION WITH RESPECT TO..." with no "AN" in front of it -- and a
# consolidated reprint of that age carries no enacting formula to stop at
# either, only the amendment chain that follows the title.
LONG_TITLE_PDF = re.compile(
    r"((?:AN?\s+)?(?:ACT|ORDINANCE|LAW)\s+TO.*?)"
    r"(?:BE\s+it\s+enacted|WHEREAS|(?:Ordinance|Act|Law)s?\s+Nos?[.,])",
    re.IGNORECASE | re.DOTALL,
)
# The note column starts hard against the left margin; the body column is
# indented. A short unindented line with no column gap is therefore the tail of a
# marginal note that wrapped, not a line of the provision -- "Exemption from /
# the Land Lease / Tax." puts "Tax." on its own line beside a blank body.
NOTE_TAIL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ,.'()&-]{0,30}$")
# "...unless exempted under section" wrapping onto a line holding just "7."
BARE_NUMBER = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.$")
MARKER_ONLY = re.compile(r"^(?:\[[^\]]+\]\s*)+$")
CHAIN_LINE = re.compile(r"^(?:(Ordinance|Act|Law)s?\s*Nos?[.,]?|\s*\d{1,3}\s+of\s+\d{4}\s*,?)$", re.I)
# Everything between the long title and the enacting formula is the preamble.
# These recitals are the Act's own statement of why it exists, and dropping them
# loses the only place the statute says what it is for.
PREAMBLE = re.compile(
    r"((?:AND\s+)?WHEREAS\b.*?)(?:NOW\s+THEREFORE\b|BE\s+it\s+enacted\b)", re.IGNORECASE | re.DOTALL
)
# Split only where a further recital is joined on. A lookahead for a bare
# "WHEREAS" also fires inside "AND WHEREAS" and leaves "AND" as a recital of
# its own.
RECITAL = re.compile(r"\s+(?=AND\s+WHEREAS\b)", re.IGNORECASE)
ENACTING = re.compile(
    r"((?:NOW\s+THEREFORE\s+)?be\s+it\s+enacted\s+by\s+the\s+Parliament.*?as\s+follows\s*[:\-–—]*)",
    re.IGNORECASE | re.DOTALL,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def page_text(pdf: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def split_at_column(line: str, column: int) -> tuple[str, str] | None:
    """Split an unindented line at the whitespace run nearest a known column.

    The gap between the columns is not always wide. "leasing of lands to law,
    the leasing of a land-" separates them with a single space, so no whitespace
    rule can find the boundary on its own. What can find it is where the body
    column sat on the section line above, since the two lines are in the same
    block and the body is set to the same left edge.
    """
    if column <= 0:
        return None
    # Nearest gap, within a tight tolerance. A greedier rule recovers a few more
    # words of marginal note but pulls words out of the provisions to do it, and
    # the provisions are the part that has to be right. Where that costs a note a
    # word or two, the heading is corrected by hand in canonical-overrides.json
    # rather than by loosening this.
    best = None
    for gap in re.finditer(r"\s+", line):
        distance = abs(gap.end() - column)
        if distance <= 3 and (best is None or distance < best[0]):
            best = (distance, gap.start(), gap.end())
    if best is None or not line[: best[1]].strip():
        return None
    return line[: best[1]].strip(), line[best[2] :].strip()


# A printed proviso opens with a capital "Provided", and it does not always
# reach for "that": "Provided however, where a company referred to in paragraph
# (a),-" is one. Matching case-insensitively instead catches the ordinary
# conditional use -- "a company referred to in section 5(1)(b), provided such
# company has been in active operation" -- which is not a proviso at all.
PROVISO_OPEN = re.compile(r"\bProvided\s*(?:however|always|further|nevertheless)?\s*(?:,|that\b)")


def retype_roman_runs(stream: list[dict]) -> list[dict]:
    """Decide whether "(i)" continues the alphabet or opens a roman sub-list.

    Both happen in this Act. Section 3(1) runs (a) to (i), where "(i)" is the
    ninth paragraph; section 2(2)(b) is followed by "(i)" and "(ii)", where they
    are sub-paragraphs of (b). The letter alone cannot tell them apart -- what
    can is the one before it. Only "(h)" is followed by a paragraph "(i)"; after
    anything else a roman run is starting, one level down.
    """
    previous = ""
    for node in stream:
        label = str(node.get("number") or "")
        if node["type"] not in ("paragraph", "subparagraph"):
            if node["type"] in ("section", "subsection"):
                previous = ""
            continue
        if label == "i" and previous != "h":
            node["type"] = "subparagraph"
        previous = label
    return stream


def lift_provisos(nodes: list[dict]) -> list[dict]:
    """Cut each proviso out of the provision it is printed inside.

    Left in place it is just more of the parent's text, so nothing downstream can
    tell the qualification from the rule it qualifies -- which for a statute is
    the difference between what the provision says and what it does.
    """
    for node in nodes:
        node["children"] = lift_provisos(node.get("children", []))
        body = node.get("text") or ""
        found = PROVISO_OPEN.search(body)
        node.pop("is_proviso", None)
        if not found:
            continue
        if found.start() == 0:
            node["is_proviso"] = True
            continue
        node["text"] = body[: found.start()].strip()
        node["children"].insert(
            0,
            {
                "type": "proviso",
                "is_proviso": True,
                "raw_text": body[found.start():].strip(),
                "text": body[found.start():].strip(),
                "qualifies": node.get("number") or node.get("term") or "",
                "amendment_events": [],
                "cross_references": [],
            },
        )
    return [n for n in nodes if n.get("text") or n.get("children") or n.get("term")]


def repair_references(nodes: list[dict]) -> None:
    """Give a clipped enactment name back its opening bracket.

    Sri Lankan short titles carry a bracketed qualifier -- Land (Restrictions on
    Alienation) Act -- and a name matched from the capital letter after "the"
    starts inside the bracket, leaving "Restrictions on Alienation) Act". That is
    not a title anyone can look up, and it will not match the registry.
    """
    for node in nodes:
        haystack = f"{node.get('raw_text', '')} {node.get('text', '')}"
        for reference in node.get("cross_references", []):
            name = reference.get("target_document", "")
            if not name or name.count("(") >= name.count(")"):
                continue
            whole = re.search(r"((?:\w+\s+){0,3}\w+\s*\(\s*" + re.escape(name) + ")", haystack)
            if whole:
                reference["target_document_raw"] = name
                reference["target_document"] = re.sub(r"\s+", " ", whole.group(1)).strip()
        repair_references(node.get("children", []))


def resolve_operations(nodes: list[dict], instructions: dict) -> None:
    """Say what each inline amendment marker actually did.

    "[2, 21 of 2018]" records that section 2 of Act No. 21 of 2018 touched this
    provision, and nothing more -- every event in the corpus reads `operation:
    unknown` for want of anyone having read the amending Act. Those Acts are now
    parsed, and they state their own operations and targets, so the marker and
    the instruction can be joined on (Act number, year, section).
    """
    for node in nodes:
        for event in node.get("amendment_events", []):
            key = (event.get("amending_act_no"), event.get("amending_year"),
                   str(event.get("amending_section", "")))
            found = instructions.get(key)
            if not found:
                continue
            event["operation"] = found["operation"]
            event["operation_source"] = found["source"]
            if found.get("operations"):
                event["operations"] = found["operations"]
            if found.get("target_label"):
                event["target_label"] = found["target_label"]
        resolve_operations(node.get("children", []), instructions)


def amending_instructions() -> dict:
    """Index every amending Act's own instructions by (number, year, section)."""
    index: dict = {}
    finalized = REPO_ROOT / "data/legal-sources/library/finalized"
    searched = list(finalized.glob("*/*.json")) + list(
        (REPO_ROOT / "data/processed/canonical-amendments").glob("*.json")
    )
    for path in searched:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if document.get("instrument_role") != "amending":
            continue
        citation = document.get("citation", {})
        for instruction in document.get("amendment_instructions", []):
            key = (citation.get("number"), citation.get("year"), str(instruction.get("in_section")))
            # An accepted tree wins over a regenerated one; whichever is seen
            # first stays, and finalized/ is searched first.
            index.setdefault(
                key,
                {
                    "operation": instruction.get("operation", "unknown"),
                    "operations": instruction.get("operations", []),
                    "target_label": instruction.get("target_label", ""),
                    "source": f"{path.parent.name}/{path.name}",
                },
            )
    return index


def split_columns(text: str) -> list[tuple[str, str]]:
    """(marginal note, body) per line, using the column gap as the boundary."""
    rows: list[tuple[str, str]] = []
    body_column = 0

    def record(note: str, body: str, line: str) -> None:
        nonlocal body_column
        # Where a provision opens is where the body column starts, and it holds
        # until the next one. Recording zero matters as much as recording twenty:
        # this Act stops printing marginal notes partway through and runs full
        # width, and a body column left over from the two-column pages is what
        # makes a wrapped line there look like a note beside a provision.
        if body and (
            SECTION_START.match(body) or ENUM_START.match(body) or DEFINITION_LINE.match(body)
        ):
            found = line.find(body[:8])
            if found >= 0:
                body_column = found
        rows.append((note, body))

    def mid_sentence() -> bool:
        """Did the last line of body text stop in the middle of a sentence?

        Past the last marginal note this PDF runs full width at indent 0, and a
        wrapped line there looks exactly like a note-plus-body line. Splitting it
        loses words: "...transferred to a dual citizen of Sri" wraps onto "Lanka
        within the meaning of the Citizenship Act;", and cutting that at the body
        column throws "Lanka within the" into a note that belongs to nothing.

        A marginal note never continues a sentence, so an unfinished one is proof
        the next line is more of the provision.
        """
        for _note, body in reversed(rows):
            if body:
                return body.rstrip()[-1:] not in ".;:-–—"
            if _note:
                return False
        return False

    for line in text.splitlines():
        if not line.strip():
            rows.append(("", ""))
            continue
        indent = len(line) - len(line.lstrip())
        carried = NOTE_THEN_SECTION.match(line.strip())
        if carried and indent < 24:
            record(carried.group("note").strip(), carried.group("body").strip(), line)
            continue
        fields = COLUMN_GAP.split(line.strip())
        if len(fields) >= 2 and indent < 24:
            # Note on the left, provision on the right.
            record(fields[0].strip(), " ".join(f.strip() for f in fields[1:]), line)
            continue
        # Past the last marginal note the body runs full width, so an unindented
        # line that opens a provision in its own right is body, not a note.
        # A marker alone on an unindented line is in the note column.
        if indent <= 2 and MARKER_ONLY.match(line.strip()):
            rows.append((line.strip(), ""))
            continue
        opens_provision = bool(
            DEFINITION_LINE.match(line.strip())
            or ENUM_START.match(line.strip())
            or SECTION_START.match(line.strip())
        )
        if indent <= 2 and not opens_provision:
            # Two spaces is still a gap; fall back to the column only when the
            # note and the body run together on a single space.
            spaced = (re.split(r"\s{2,}", line.strip(), maxsplit=1) + [""])[:2]
            narrow = spaced if spaced[1].strip() else (split_at_column(line, body_column) or ("", ""))
            if narrow[1].strip():
                record(narrow[0].strip(), narrow[1].strip(), line)
                continue
            # Only where a note column actually exists. Full width, a short line
            # is the last line of a provision -- "the Companies Act." closing the
            # definition of "subsidiary" -- not a marginal note that wrapped.
            if body_column > 0 and NOTE_TAIL.match(line.strip()):
                rows.append((line.strip(), ""))
                continue
        record("", line.strip(), line)
    return rows


def merge_note_runs(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Collapse each run of consecutive note-column lines onto its first row.

    A marginal note wraps over as many lines as it needs, and the lines it wraps
    onto are the ones carrying the paragraphs of the section it names. Left as
    they are, "Exemption from / the application of / the provisions of /
    section 2." would give section 3 the first line and hand the rest to (a).
    """
    # The amendment chain sits in the note column too. Drop it before the runs
    # are joined, or it becomes the first section's heading.
    merged = [("" if CHAIN_LINE.match(note) else note, body) for note, body in rows]
    start = None
    for index, (note, body) in enumerate(merged + [("", "")]):
        # Some pages double-space the note column, so a single blank row inside a
        # run is part of the run, not the end of it. A row carrying body text
        # without a note always ends it.
        if (
            start is not None
            and not note
            and not body
            and index + 1 < len(merged)
            and merged[index + 1][0]
            # A section number on the far side of the gap means the note there
            # belongs to that section, not to this run.
            and not SECTION_START.match(merged[index + 1][1])
        ):
            continue
        if note and start is None:
            start = index
        elif not note and start is not None:
            joined = " ".join(merged[i][0] for i in range(start, index))
            merged[start] = (joined, merged[start][1])
            for i in range(start + 1, index):
                merged[i] = ("", merged[i][1])
            start = None
    return merged


def blocks_from(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Group the body column into (pending note, block) runs."""
    rows = merge_note_runs(rows)
    blocks, note_parts, body_parts = [], [], []

    def flush():
        body = re.sub(r"\s+", " ", " ".join(body_parts)).strip()
        note = re.sub(r"\s+", " ", " ".join(note_parts)).strip(" .")
        if body:
            blocks.append((note, body))
        note_parts.clear()
        body_parts.clear()

    real = {
        SECTION_START.match(body).group(1)
        for _note, body in rows
        if SECTION_START.match(body) and SECTION_START.match(body).group(2).strip()
    }
    for note, body in rows:
        # "7." alone, where section 7 proper appears elsewhere with text, is the
        # end of a sentence in the section above it, not the start of a new one.
        bare = BARE_NUMBER.match(body)
        if bare and bare.group(1) in real:
            body_parts.append(body)
            continue
        # An enumerator only opens a provision where the one before it closed. A
        # line can also *begin* with a bracketed letter because a cross-reference
        # wrapped across it -- "...of a company referred to in paragraph" /
        # "(a) reaches or exceeds fifty per cent..." -- and treating that as a new
        # paragraph (a) tears the sentence in half and invents a provision.
        opens_list = bool(
            body_parts
            and (
                re.search(r"(?:[;:.\-–—]|\b(?:or|and))$", body_parts[-1].rstrip())
                # "(2)" can sit alone on its line with "(a)" beneath it. Nothing
                # has been said yet, so the next enumerator is the first thing
                # inside it rather than a continuation of it.
                or re.fullmatch(r"\(\s*\w{1,4}\s*\)", body_parts[-1].strip())
            )
        )
        starts_block = bool(
            SECTION_START.match(body)
            or DEFINITION_LINE.match(body)
            or (ENUM_START.match(body) and (opens_list or not body_parts))
        )
        if starts_block and body_parts:
            flush()
        if note and not CHAIN_LINE.match(note):
            note_parts.append(note)
        if body:
            body_parts.append(body)
    flush()
    return blocks


SCHEDULE_BOUNDARY = re.compile(r"\n[ \t]*Schedules?[ \t]*\n")


def parse(pdf: Path, title: str) -> list[dict]:
    text = page_text(pdf)
    # A Schedule prints its own numbered items (a form's "1. Place of Birth",
    # "2. Lay Name in Full", ...), which SECTION_START cannot tell apart from a
    # real section restarting at 1. Nothing here extracts schedule content into
    # structure yet, so stop before it rather than filing form fields as bogus
    # sections 1-N with no heading (Buddhist Temporalities Ordinance section 44
    # was followed by three such runs before this cut).
    boundary = SCHEDULE_BOUNDARY.search(text)
    if boundary:
        text = text[: boundary.start()]
    stream: list[dict] = []
    current_note = ""

    pending_events: list[dict] = []
    for note, body in blocks_from(split_columns(text)):
        note, note_events = split_markers(note)
        body, body_events = split_markers(body)
        events = body_events + pending_events
        pending_events = []
        if note:
            current_note = note
        section = SECTION_START.match(body)
        # A bare "7." is usually a real section whose text begins on the next
        # line. It is an artefact only when that number is already open, which is
        # what the duplicate section 7 in the Land Restrictions PDF looks like.
        if section and not section.group(2).strip():
            if any(n["type"] == "section" and n["number"] == section.group(1) for n in stream):
                continue
        if section and not body[:1].isalpha():
            number, remainder = section.group(1), section.group(2).strip()
            stream.append(
                {
                    "type": "section",
                    "number": number,
                    "heading": current_note,
                    "raw_text": body,
                    "text": "" if ENUM_START.match(remainder) else remainder,
                    "amendment_events": events + note_events,
                    "cross_references": cross_references(remainder, title),
                }
            )
            note_events = []
            current_note = ""
            if ENUM_START.match(remainder):
                # The section node has taken these; the subsection below is a
                # different node and must not claim them a second time.
                events = []
                body = remainder
            else:
                continue

        if note_events:
            # The note column is printed against the section as a whole. Where
            # this block is not itself a section, the marker still belongs to the
            # section it sits inside.
            section_above = next((n for n in reversed(stream) if n["type"] == "section"), None)
            if section_above is None:
                pending_events.extend(note_events)
            else:
                section_above.setdefault("amendment_events", []).extend(note_events)
        if not stream:
            continue
        defined = parse_definition(body)
        if defined:
            term, qualifier, definition_text = defined
            stream.append(
                {
                    "type": "definition",
                    "term": term,
                    "qualifier": qualifier,
                    "raw_text": body,
                    "text": definition_text,
                    "amendment_events": events,
                    "cross_references": cross_references(definition_text, title),
                }
            )
            continue
        kind, label, remainder = classify(body)
        if kind == "text" and stream and stream[-1]["type"] != "section":
            stream[-1]["text"] = (stream[-1]["text"] + " " + remainder).strip()
            stream[-1].setdefault("amendment_events", []).extend(events)
            continue
        node = {
            "type": kind,
            "number": label,
            "raw_text": body,
            "text": remainder,
            "amendment_events": events,
            "cross_references": cross_references(remainder, title),
        }
        stream.append(node)

    return lift_provisos(nest(retype_roman_runs(stream)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--show", action="store_true")
    parser.add_argument(
        "--edition",
        default="consolidated",
        help="which text this PDF is. The same statute can be held twice, as "
             "enacted and as consolidated, and they must not overwrite each other.",
    )
    args = parser.parse_args()

    registry = {r["source_id"]: r for r in read_csv(REGISTRY)}
    row = registry[args.source_id]
    pdf = REPO_ROOT / row["local_pdf_path"]
    if not pdf.exists():
        print(f"{pdf} is missing", file=sys.stderr)
        return 1

    body = parse(pdf, row["official_title"])
    if not body:
        print("no sections found; this PDF probably has no text layer", file=sys.stderr)
        return 1

    chain = [
        r
        for r in (read_csv(CHAINS) if CHAINS.exists() else [])
        if r["source_id"] == args.source_id and r["role"] == "amending"
    ]
    commencement = {r["source_id"]: r["commencement"] for r in read_csv(COMMENCEMENT)}
    full_text = page_text(pdf)
    title_match = LONG_TITLE_PDF.search(re.sub(r"\s+", " ", full_text))
    long_title = re.sub(r"\s+", " ", title_match.group(1)).strip(" .") + "." if title_match else ""
    flat = re.sub(r"\s+", " ", full_text)
    preamble_match = PREAMBLE.search(flat)
    recitals = []
    if preamble_match:
        recitals = [
            {"type": "recital", "order": order, "text": piece.strip(" :")}
            for order, piece in enumerate(
                (p.strip() for p in RECITAL.split(preamble_match.group(1)) if p.strip()), start=1
            )
        ]
    enacting = ENACTING.search(flat)

    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    override = overrides.get(args.source_id, {})
    # A marginal note the columns could not be separated cleanly enough to
    # recover is corrected here, by hand, against the print. The damaged reading
    # is kept as heading_raw so the correction is visible rather than assumed.
    apply_heading_overrides(body, override.get("section_headings", {}))
    repair_references(body)
    resolve_operations(body, amending_instructions())

    document = {
        "source_id": args.source_id,
        "title": row["official_title"],
        "long_title": override.get("long_title", long_title),
        "long_title_raw": long_title if override.get("long_title") else "",
        "citation": {
            "type": chain[0]["instrument_type"] if chain else "",
            "number": int(row["act_or_ordinance_no"]),
            "year": int(row["year"]),
        },
        "commencement": commencement.get(args.source_id, ""),
        "preamble": recitals,
        "enacting_formula": re.sub(r"\s+", " ", enacting.group(1)).strip() if enacting else "",
        "language": "en",
        "edition": {
            "publisher": override.get("publisher", "unattributed"),
            "kind": args.edition,
            "local_path": pdf.relative_to(REPO_ROOT).as_posix(),
            "caveat": "parsed from a two-column PDF",
        },
        "amendments": [
            {
                "type": r["instrument_type"],
                "number": int(r["instrument_no"]),
                "year": int(r["instrument_year"]),
            }
            for r in chain
        ],
        "verification_status": override.get("verification_status", "unverified"),
        "quality_flags": quality_flags(full_text) + override.get("quality_notes", []),
        "editorial_notes": override.get("editorial_notes", []),
        "checked_against": override.get("checked_against", ""),
        "schedules_referenced": sorted({m.group(1) for m in SCHEDULE_REF.finditer(full_text)}),
        "schedules": [],
        "body": body,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.edition == "consolidated" else f"-{args.edition}"
    target = (
        OUT_DIR
        / f"{args.source_id}-{document['citation']['number']}-{document['citation']['year']}{suffix}.json"
    )
    target.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    sections = [n for n in body if n["type"] == "section"]
    print(f"wrote {target.relative_to(REPO_ROOT)}")
    print(f"  {len(sections)} sections, {len(document['amendments'])} amendments in the chain")
    if args.show:
        def show(nodes, indent=0):
            for node in nodes:
                label = node.get("term") or node.get("number") or ""
                print("  " * indent + f"{node['type']:12} {label:16} {node.get('text', '')[:46]}")
                show(node.get("children", []), indent + 1)
        show(body[:6])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
