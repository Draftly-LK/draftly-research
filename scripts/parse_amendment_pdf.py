"""Parse a Government Printer amending Act into the canonical amendment shape.

`build_canonical_amendments.py` reads LankaLaw's HTML. For the Land
(Restrictions on Alienation) amendments that source turned out to be truncated:
both pages stop partway and show a subscription banner, so Act No. 3 of 2017 lost
its section 3 and Act No. 21 of 2018 lost its sections 3 and 4 -- including the
one that moves section 5A's operative date from January 8, 2017 to January 1,
2016. A tree built from those pages is not wrong so much as short, which is worse,
because nothing in it says anything is missing.

The Government Printer PDF is the authority anyway, so this reads that instead.
Its layout is the mirror of the consolidated volumes: the marginal note runs down
the *right* column and the provision down the left.

       1. This Act may be cited as the Land (Restrictions on    Short title and
    Alienation) (Amendment) Act, No. 3 of 2017 and shall be     date of
    deemed to have come into operation with effect from         operation.

A provision the Act inserts is printed as a quoted extract, and inside those
quotes the principal Act's own layout resumes -- note on the left again:

    "Land Lease 5A. Notwithstanding anything to the contrary
    Tax not to be in any of the provisions of this Act, the
    levied with   provisions relating to the Land Lease Tax shall

That left-hand note is the inserted section's heading. Reading it as body text
loses the heading and corrupts the provision, so the two regimes are split apart.

References inside an amending section resolve against the principal enactment,
not against this Act: "in subsection (1)" in a section that amends section 3 of
the principal Act means principal 3(1), and reading it as 1(1) of the amending
Act points at its own short title.

    uv run python scripts/parse_amendment_pdf.py --number 3 --year 2017 \
        --pdf <path> --amends SRC021
    uv run python scripts/parse_amendment_pdf.py --number 21 --year 2018 \
        --ocr-text <path> --amends SRC021
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

OUT_DIR = REPO_ROOT / "data/processed/canonical-amendments"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
OVERRIDES = REPO_ROOT / "data/processed/amendment-overrides.json"

SECTION = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s*(.*)$", re.DOTALL)
ENUM = re.compile(r"^\(\s*([A-Za-z]{1,4}|\d{1,3})\s*\)\s*(.*)$", re.DOTALL)
LONG_TITLE = re.compile(r"(AN?\s+ACT\s+TO\s+AMEND\b.*?)(?:BE\s+it\s+enacted)", re.I | re.S)
ENACTMENT_WORD = re.compile(r"\s+(Act|Ordinance|Law)$")
CERTIFIED = re.compile(r"\[\s*Certified\s+on\s+([^\]]+?)\s*\]", re.I)
# "L. D.-O. 49/2021", where the dash is a hyphen in one Act and an en or em dash
# in the next, depending on who set the page.
LD_NUMBER = re.compile(r"^L\.?\s*D\.?\s*[-–—.]{0,3}\s*O\.?\s*(\d+/\d{4})", re.I | re.M)

# The lead-in of an amending section names what it operates on. It does not
# always say "amended": a section replaced outright reads "is hereby repealed
# and the following section is substituted therefor", and a section deleted
# reads "is hereby repealed" and stops. Matching only "amended" leaves those
# with no target and no instruction at all, which reads as an Act that changes
# nothing.
LEAD_TARGET = re.compile(
    r"[Ss]ection\s+(?P<section>\d{1,3}[A-Z]{0,2})\s+of\s+(?P<what>the\s+.*?)"
    r"\s+is\s+hereby\s+(?P<verb>amended|repealed)",
    re.S,
)
REPEAL_AND_SUBSTITUTE = re.compile(
    r"repealed\s+and\s+the\s+following\s+\w+\s+is\s+substituted", re.S | re.I
)
LEAD_SUBSECTION = re.compile(r"is\s+hereby\s+amended[^.]*?in\s+subsection\s*\(\s*(\w{1,3})\s*\)", re.S)
INSERT_AFTER = re.compile(
    r"inserted\s+immediately\s+after\s+section\s+(?P<after>\d{1,3}[A-Z]{0,2})\s+of\s+"
    r"(?P<what>the\s+.*?)\s+and\s+shall\s+have\s+effect\s+as\s+section\s+(?P<as>\d{1,3}[A-Z]{0,2})",
    re.S,
)

# What one enumerated limb of an amending section does. Order matters: a repeal
# paired with a substitution is one operation, not two.
LIMB_OPERATIONS = (
    ("repeal_and_substitute", re.compile(r"repeal\s+of\b.*?\bsubstitution", re.S | re.I)),
    ("insert", re.compile(r"\baddition\s+of\s+the\s+following\b|\binsertion\b", re.S | re.I)),
    # "substitution" on its own, not "substitution for": OCR runs the following
    # words together often enough ("substitution forghe words") that requiring
    # the preposition drops real limbs.
    ("substitute", re.compile(r"\bsubstitut(?:ion|ed?)\b", re.S | re.I)),
    ("repeal", re.compile(r"\brepeal(ed)?\b", re.S | re.I)),
    ("amend", re.compile(r"\bamend(ed|ment)?\b", re.S | re.I)),
)
LIMB_PARAGRAPH = re.compile(r"paragraph\s*\(\s*(\w{1,3})\s*\)", re.I)
NEW_PARAGRAPH = re.compile(r'following\s+new\s+paragraph[^"“]*["“]\s*\(\s*(\w{1,3})\s*\)', re.I | re.S)
MARGINAL_NOTE_LIMB = re.compile(r"in\s+the\s+marginal\s+note", re.I)
# "for the words and figures "January 8, 2017." of the words and figures "January 1, 2016.""
# The commas are not decoration and they are not always in the same places:
# "...on the same, and", of the words, "buildings erected..." puts one after the
# closing quote and another after "words", and a pattern that allows neither
# reads the whole substitution as no substitution at all.
SUBSTITUTION_PAIR = re.compile(
    r"substitution\s+for\s+the\s+words(?:\s+and\s+figures)?\s*,?\s+"
    r"[\"“](?P<from>[^\"”]+)[\"”]\s*,?\s+of\s+the\s+words(?:\s+and\s+figures)?\s*,?\s+"
    r"[\"“](?P<to>[^\"”]+)[\"”]",
    re.S | re.I,
)
# A reference to the principal Act's own provisions, written out in full.
PRINCIPAL_REF = re.compile(
    r"paragraph\s*\(\s*(?P<para>\w{1,3})\s*\)\s+of\s+subsection\s*\(\s*(?P<sub>\w{1,3})\s*\)"
    r"\s+of\s+section\s+(?P<section>\d{1,3}[A-Z]{0,2})",
    re.I,
)
PAGE_FURNITURE = re.compile(
    # OCR spaces a running head out unevenly -- "Land    (Restrictions   on
    # Alienution)" -- so the words in it have to be matched with flexible gaps
    # too, or the head survives into the provision it was printed above.
    r"^\s*[\"“]?(?:\d+\s*)?(?:Land\s+\(Restrictions|Act, No\.|PRINTED|TO BE|Price|Postage|"
    # The tail of a running head that OCR broke over two lines. Anchored to the
    # end of the line: a provision citing the amending Act by name wraps onto a
    # line opening the same way and must not be thrown out with it.
    r"\(Amendment\)\s+Act,\s*No\.\s*\d{1,3}\s*of\s*\d{4}\s*$|"
    # Laid back out from OCR, a word gap can be several spaces wide, so the
    # imprint lines have to be matched with flexible whitespace or they survive
    # into the tree as a section 118.
    r"Annual\s+subscription|English\s+Acts|GOVERNMENT\s+PRINTING|DEPARTMENT\s+OF|"
    r"December\s+each\s+year|"
    # "2--PL 010272--2,961" in an ASCII reading, "2—PL 010272—2,961" once the
    # page is read with its real em dashes.
    r"\d+[-—]{1,2}PL|This Act can be|T$)",
    re.I,
)
# The running head repeats the Act's own citation on every page, sometimes with
# the page number on the left and sometimes on the right. Left in, it reaches
# the column splitter as a full-width line and can swallow the marginal note
# printed beside it.
RUNNING_HEADER = re.compile(
    r"^\s*(?:\d{1,3}\s+)?[A-Z][A-Za-z()'’ -]{2,60}Act,\s*No\.\s*\d{1,3}\s+of\s+\d{4}\s*\d{0,3}\s*$"
)


def page_text(pdf: Path) -> str:
    # `-enc UTF-8` is redundant under poppler, which already defaults to it, and
    # is asked for anyway because it is not redundant under every pdftotext. An
    # Xpdf build earlier on PATH answers in its own locale encoding, and the
    # curly quotes an Act is printed with come back as U+FFFD -- which silently
    # breaks the quote matching that finds inserted provisions.
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout


def note_column(lines: list[str]) -> int:
    """Where the right-hand note column starts, from the section lines.

    A section line carries both columns, so the wide gap on it marks the edge.
    Taking the median over every such line rather than the first keeps one
    ragged line from moving the boundary.
    """
    edges = []
    for line in lines:
        if not SECTION.match(line.strip()):
            continue
        # The widest gap on the line, not the first one past a threshold. On a
        # page laid back out from OCR the body itself carries runs of three or
        # four spaces, so "first wide gap" lands in the middle of the provision
        # and drags half of it into the heading. The column break is the widest.
        gaps = [g for g in re.finditer(r"\s{3,}", line) if g.end() > 40 and g.start() > 0]
        if gaps:
            widest = max(len(g.group(0)) for g in gaps)
            edges.append(max(g.end() for g in gaps if len(g.group(0)) == widest))
    if edges:
        return sorted(edges)[len(edges) // 2]
    # A reconstructed OCR page has no wide gap to find -- the words are laid out
    # on a character grid, so the note can start one space after the provision.
    # What is still true is that the note column is a column: the same left edge,
    # line after line. Take the rightmost edge that repeats often enough to be a
    # column rather than a coincidence.
    starts: dict[int, int] = {}
    for line in lines:
        for word in re.finditer(r"\S+", line):
            if word.start() > 55:
                starts[word.start()] = starts.get(word.start(), 0) + 1
    repeated = [column for column, count in starts.items() if count >= 3]
    return min(repeated) if repeated else 0


def note_side(lines: list[str]) -> str:
    """Which margin this page runs its notes down.

    The marginal note sits in the *outer* margin, so it swaps sides from one
    page to the next. On a page whose notes are on the right the section number
    opens the line; on a left-note page the note comes first and the number is
    pushed well in. Assuming one side for the whole Act loses every section on
    half the pages -- which is how sections 3 and 4 of the 2018 Act went missing.
    """
    right = left = 0
    for line in lines:
        stripped = line.strip()
        if SECTION.match(stripped):
            right += 1
            continue
        found = re.search(r"(?<![\d.])\b(\d{1,3}[A-Z]{0,2})\.\s+[A-Z(]", line)
        if found and found.start() > 8 and line[: found.start()].strip():
            left += 1
    return "left" if left > right else "right"


def split_left_notes(lines: list[str]) -> list[tuple[str, str]]:
    """(body, note) per line for a page whose notes run down the left margin."""
    edges = []
    for line in lines:
        found = re.search(r"(?<![\d.])\b\d{1,3}[A-Z]{0,2}\.\s+[A-Z(]", line)
        if found and found.start() > 8:
            edges.append(found.start())
    edge = sorted(edges)[len(edges) // 2] if edges else 0
    rows = []
    for line in lines:
        if not line.strip():
            rows.append(("", ""))
            continue
        indent = len(line) - len(line.lstrip())
        # A line that begins in the body column has no note on it, whatever
        # whitespace it happens to contain. Without this, "as follows:-" set
        # under the provision is cut at its own word gap and "as" is filed as
        # part of the marginal note above it.
        if edge and indent >= edge - 4:
            rows.append((line.strip(), ""))
            continue
        if edge and len(line.rstrip()) > edge:
            # The column break is a run of spaces; the note's own word gaps are
            # single spaces. Taking the last gap of any width before the edge
            # cuts "section 9 of the   by the substitution" after "by" and files
            # that word as note text. Prefer a real run, and fall back to a
            # single space only where the line carries no run at all.
            def before_edge(pattern: str) -> list[re.Match[str]]:
                return [
                    g
                    for g in re.finditer(pattern, line)
                    if g.start() < edge + 2 and line[: g.start()].strip()
                ]

            runs = before_edge(r"\s{2,}") or before_edge(r"\s+")
            if runs:
                best = runs[-1]
                rows.append((line[best.end():].strip(), line[: best.start()].strip()))
                continue
        if edge and indent < edge - 6 and not SECTION.match(line.strip()):
            rows.append(("", line.strip()))
            continue
        rows.append((line.strip(), ""))
    return rows


def split_right_notes(lines: list[str], column: int) -> list[tuple[str, str]]:
    """(body, note) per line, cutting at the note column.

    A note that runs longer than the provision it annotates wraps onto lines of
    its own, out in the note column with nothing to their left. There is no gap
    to cut those at, so they fall through to being read as body -- which is how
    "Replacement of / section 2 of / Chapter 60" loses two of its three lines
    and the ones it loses turn up in the middle of the section's text.
    """
    rows = []
    for line in lines:
        if not line.strip():
            rows.append(("", ""))
            continue
        # Nothing to the left of the column: this is the note above, wrapping.
        if column and len(line) - len(line.lstrip()) >= column - 2:
            rows.append(("", line.strip()))
            continue
        if column and len(line) > column - 4:
            gap = None
            for candidate in re.finditer(r"\s{2,}", line):
                if candidate.end() >= column - 2:
                    gap = candidate
                    break
            if gap and line[gap.end():].strip() and line[: gap.start()].strip():
                rows.append((line[: gap.start()].strip(), line[gap.end():].strip()))
                continue
        rows.append((line.strip(), ""))
    return rows


def join_runs(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Attach each run of note lines to the body block it starts against."""
    blocks: list[tuple[str, str]] = []
    body_parts: list[str] = []
    note_parts: list[str] = []

    def flush():
        body = re.sub(r"\s+", " ", " ".join(body_parts)).strip()
        note = re.sub(r"\s+", " ", " ".join(note_parts)).strip()
        if body:
            blocks.append((body, note))
        body_parts.clear()
        note_parts.clear()

    for body, note in rows:
        if body and SECTION.match(body) and body_parts:
            flush()
        if body:
            body_parts.append(body)
        if note:
            note_parts.append(note)
    flush()
    return blocks


def parse_inserted_block(raw_lines: list[str]) -> dict | None:
    """Read a quoted inserted provision, whose note is on the LEFT again."""
    text = "\n".join(raw_lines)
    opener = re.search(r'["“](?P<note>[^"”]*?)\s*(?P<num>\d{1,3}[A-Z]{0,2})\.\s', text)
    if not opener:
        return None
    number = opener.group("num")
    # Which printed line the number sits on. It is not always the first line of
    # the block: the quote can open two or three lines earlier, on the opening
    # words of the inserted section's own marginal note, and reading the body
    # column off the quote line then finds no number and no column at all.
    start = next(
        (i for i, line in enumerate(raw_lines) if re.search(rf"(?<![\d.]){number}\.\s", line)),
        0,
    )
    # The note wraps down the left column of the following lines; the provision
    # body sits to its right. The columns are not a clean rectangle -- the note
    # runs a word or two past the body's left edge on some lines and stops well
    # short of it on others -- so cut at a word boundary near that edge rather
    # than at the edge itself, which slices "Tax not to be" into "Tax not to b".
    body_edge = raw_lines[start].find(f"{number}.") if raw_lines else 0
    note_parts = [opener.group("note").strip().lstrip('"“')]
    body_parts = [text[opener.end():].split("\n")[0].strip()]
    for line in raw_lines[start + 1:]:
        if not line.strip():
            body_parts.append("")
            continue
        if body_edge <= 0:
            body_parts.append(line.strip())
            continue
        # A line that ends before the body column is all note.
        if len(line.rstrip()) <= body_edge:
            note_parts.append(line.strip())
            continue
        # A line that begins at the body column has no note beside it. Where the
        # inserted section's note is only three lines long the rest of the
        # provision runs on alone, and cutting those lines at a word gap files
        # the first word of each into the margin: "has reached the age" becomes
        # a note reading "has" and a provision starting "reached".
        if len(line) - len(line.lstrip()) >= body_edge - 4:
            body_parts.append(line.strip())
            continue
        # The last gap before the body's left edge, not the nearest one: the note
        # is set flush left and runs as far right as its words take it, a word or
        # two past that edge on a long line. Nearest-gap cuts "Tax not to be"
        # after "to"; last-gap keeps the whole note and starts the body at "in".
        # A run of spaces is the column break where there is one; a single space
        # is only the break where the note runs right up against the provision.
        def before_body(pattern: str) -> list[re.Match[str]]:
            return [
                g
                for g in re.finditer(pattern, line)
                if g.start() < body_edge + 2 and line[: g.start()].strip()
            ]

        runs = before_body(r"\s{2,}") or before_body(r"\s+")
        if not runs:
            body_parts.append(line.strip())
            continue
        best = runs[-1]
        note_parts.append(line[: best.start()].strip())
        body_parts.append(line[best.end():].strip())
    heading = re.sub(r"\s+", " ", " ".join(p for p in note_parts if p)).strip()
    body = re.sub(r"[ \t]+", " ", "\n".join(body_parts))
    return {"number": number, "heading": heading, "body": body}


def nest_enumerated(body: str, title: str) -> tuple[str, list[dict]]:
    """Split a provision's trailing enumerated limbs off its opening text."""
    from build_canonical_statutes import cross_references

    pieces = re.split(r"\n(?=\(\s*[A-Za-z0-9]{1,4}\s*\))", body)
    lead = re.sub(r"\s+", " ", pieces[0]).strip()
    children, closing = [], []
    for piece in pieces[1:]:
        # Prose set off by a blank line after a limb is not part of that limb: it
        # closes the whole provision. "(c) to a foreign company," then "under and
        # indenture of lease executed on or after January 8, 2017..." governs
        # (a), (b) and (c) alike, and folding it into (c) makes it say the
        # opposite of what it does.
        parts = re.split(r"\n\s*\n", piece)
        flat = re.sub(r"\s+", " ", parts[0]).strip()
        tail = re.sub(r"\s+", " ", " ".join(parts[1:])).strip()
        if tail:
            closing.append(tail)
        match = ENUM.match(flat)
        if not match:
            closing.insert(0, flat)
            continue
        limb_text = match.group(2).strip()
        children.append(
            {
                "type": "paragraph",
                "number": match.group(1),
                "raw_text": flat,
                "text": limb_text,
                "amendment_events": [],
                "cross_references": cross_references(limb_text, title),
            }
        )
    return lead, children + (
        [
            {
                "type": "closing_text",
                "raw_text": " ".join(closing),
                "text": " ".join(closing),
                "amendment_events": [],
                "cross_references": cross_references(" ".join(closing), title),
            }
        ]
        if closing
        else []
    )


def limb_instructions(section_text: str, limbs: list[dict]) -> tuple[dict, list[dict]]:
    """What an amending section operates on, and what each of its limbs does.

    The lead-in fixes the target once -- "Section 3 of the ... Act ... is hereby
    amended in subsection (1)" -- and every limb below it is relative to that.
    Read limb by limb in isolation, "in paragraph (h) of that subsection" has no
    subsection to point at and "that subsection" resolves to nothing.
    """
    context: dict = {}
    lead = LEAD_TARGET.search(section_text)
    inserted = INSERT_AFTER.search(section_text)
    if lead:
        context["target_section"] = lead.group("section")
        context["named_target"] = re.sub(r"\s+", " ", lead.group("what")).strip()
    elif inserted:
        context["target_section"] = inserted.group("as")
        context["after_section"] = inserted.group("after")
        context["named_target"] = re.sub(r"\s+", " ", inserted.group("what")).strip()
    subsection = LEAD_SUBSECTION.search(section_text)
    if subsection:
        context["target_subsection"] = subsection.group(1)

    operations: list[dict] = []
    for limb in limbs:
        body = limb.get("text", "")
        operation = next((name for name, rx in LIMB_OPERATIONS if rx.search(body)), "")
        if not operation:
            continue
        entry: dict = {"limb": limb.get("number", ""), "operation": operation}
        target = dict(context)
        # A limb that adds a paragraph names the new one inside the quoted text;
        # one that changes an existing paragraph names it in the instruction.
        added = NEW_PARAGRAPH.search(body)
        existing = LIMB_PARAGRAPH.search(body)
        if operation == "insert" and added:
            target["target_paragraph"] = added.group(1)
            if existing:
                target["inserted_after_paragraph"] = existing.group(1)
        elif existing:
            target["target_paragraph"] = existing.group(1)
        if MARGINAL_NOTE_LIMB.search(body):
            target["target_component"] = "marginal note"
        pair = SUBSTITUTION_PAIR.search(body)
        if pair:
            entry["substitutes"] = {
                "from": pair.group("from").strip(),
                "to": pair.group("to").strip(),
            }
        entry["target"] = target
        entry["target_label"] = format_target(target)
        operations.append(entry)
    return context, operations


def whole_section_operation(section_text: str, context: dict) -> str:
    """What an amending section with no enumerated limbs does."""
    if context.get("after_section"):
        return "insert"
    lead = LEAD_TARGET.search(section_text)
    if lead and lead.group("verb").lower() == "repealed":
        return "repeal_and_substitute" if REPEAL_AND_SUBSTITUTE.search(section_text) else "repeal"
    return "amend"


def format_target(target: dict) -> str:
    """`3(1)(b)`, so a reader does not have to reassemble the parts."""
    label = target.get("target_section", "")
    if not label:
        return ""
    if target.get("target_subsection"):
        label += f"({target['target_subsection']})"
    if target.get("target_paragraph"):
        label += f"({target['target_paragraph']})"
    if target.get("target_component"):
        label += f" [{target['target_component']}]"
    return label


INSERT_OPEN = re.compile(r'["“][^"”]{0,60}?\b\d{1,3}[A-Z]{0,2}\.\s')
INSERT_CLOSE = re.compile(r'["”]\s*\.?\s*["”]?\s*\.?\s*$')


def carve_inserted(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Lift the quoted inserted provisions out of the page before it is split.

    They have to come out first. Inside the quotes the columns swap sides, so
    running the right-hand note rule over them would cut the inserted section's
    own heading in half.
    """
    kept: list[str] = []
    carved: list[list[str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        # The quote and the number of the inserted section are not always on one
        # line. Where the inserted section carries a marginal note the quote
        # opens on the first line of that note, which then wraps for two or three
        # lines before the number appears -- so look at a short window, and carve
        # only where the quote itself is on this line.
        window = INSERT_OPEN.search("\n".join(lines[index:index + 4]))
        if window and window.start() < len(line):
            block = [line]
            index += 1
            while index < len(lines) and not INSERT_CLOSE.search(lines[index - 1].rstrip()):
                block.append(lines[index])
                index += 1
            carved.append(block)
            kept.append("")
            continue
        kept.append(line)
        index += 1
    return kept, carved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--number", type=int, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--ocr-text", type=Path)
    parser.add_argument("--amends", required=True, help="source_id of the principal statute")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    from build_canonical_statutes import cross_references, read_csv

    if args.pdf:
        source = args.pdf.resolve()
        text = page_text(source)
        markup, caveat = "text layer", "read from the Government Printer PDF"
    elif args.ocr_text:
        source = args.ocr_text.resolve()
        text = source.read_text(encoding="utf-8")
        markup = "OCR of a scan"
        caveat = (
            "the Government Printer PDF is a scan with no text layer, so this "
            "tree is parsed from an OCR reading and carries OCR errors"
        )
    else:
        print("give --pdf or --ocr-text", file=sys.stderr)
        return 1

    registry = {r["source_id"]: r for r in read_csv(REGISTRY)}
    principal = registry[args.amends]
    principal_title = principal["official_title"]

    flat = re.sub(r"\s+", " ", text)
    long_title_match = LONG_TITLE.search(flat)
    long_title = re.sub(r"\s+", " ", long_title_match.group(1)).strip() if long_title_match else ""
    certified = CERTIFIED.search(flat)
    ld_number = LD_NUMBER.search(text)

    # Keep the page breaks: which margin the notes run down depends on them.
    # Split on newlines only. `str.splitlines()` treats a form feed as a line
    # break in its own right and drops it, so every page boundary in the
    # pdftotext stream disappears and the whole Act is read as a single page --
    # one margin for all of it, and every section printed on a page that uses
    # the other margin is lost without a word.
    pages: list[list[str]] = [[]]
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("===== PAGE") or "\f" in line:
            pages.append([])
            line = line.replace("\f", "")
        if line.startswith("#") or line.startswith("===== PAGE"):
            continue
        if PAGE_FURNITURE.match(line) or RUNNING_HEADER.match(line):
            continue
        pages[-1].append(line)

    # Carve across the whole Act, not page by page: the 2018 insertion opens on
    # page 2 and closes on page 3, and carving per page leaves its tail behind to
    # be read as loose text.
    marker = "<<<PAGE-BREAK>>>"
    flat_lines: list[str] = []
    for page in pages:
        flat_lines.append(marker)
        flat_lines.extend(page)
    flat_lines, carved = carve_inserted(flat_lines)
    pages, current = [], []
    for line in flat_lines:
        if line == marker:
            pages.append(current)
            current = []
        else:
            current.append(line)
    pages.append(current)

    started = False
    rows: list[tuple[str, str]] = []
    for page in pages:
        if not started:
            for position, line in enumerate(page):
                if re.search(r"BE\s+it\s+enacted", line, re.I):
                    page = page[position + 1:]
                    started = True
                    break
            else:
                continue
        if note_side(page) == "left":
            rows.extend(split_left_notes(page))
        else:
            rows.extend(split_right_notes(page, note_column(page)))
        rows.append(("", ""))
    blocks = join_runs(rows)

    body: list[dict] = []
    instructions: list[dict] = []
    quality: list[str] = []
    for block_body, note in blocks:
        match = SECTION.match(block_body)
        if not match:
            continue
        number, remainder = match.group(1), match.group(2).strip()
        # A limb opens only where the one before it closed. Splitting on every
        # "(x)" tears the sentence apart at its own cross-references: "by the
        # repeal of paragraph (b) of that subsection" becomes a limb (a) reading
        # "by the repeal of paragraph" and a phantom limb (b).
        marked = re.sub(r'(?<=[;:"”)\-])\s+(\([a-z]\)\s)', r"\n\1", remainder)
        # The first limb can follow the lead-in's last word rather than any
        # punctuation: "is hereby amended (a) by the substitution ...".
        marked = re.sub(r"(?<=\bamended)\s+(\([a-z]\)\s)", r"\n\1", marked)
        lead, limbs = nest_enumerated(marked, principal_title)
        node = {
            "type": "section",
            "number": number,
            "heading": re.sub(r"\s+", " ", note).strip(),
            "raw_text": block_body,
            "text": lead,
            "amendment_events": [],
            "cross_references": [],
            "children": limbs,
        }
        context, operations = limb_instructions(remainder, limbs)
        if operations or context.get("target_section"):
            if operations:
                headline = operations[0]["operation"] if len(operations) == 1 else "multiple"
            else:
                # No enumerated limbs: the whole section is one instruction, and
                # the lead-in says which. "shall have effect as section 5A" is an
                # insertion even though no limb below it says so, and "is hereby
                # repealed" is a repeal, not the amendment this used to record.
                headline = whole_section_operation(remainder, context)
            node["amendment_instruction"] = {
                "operation": headline,
                "operations": operations,
                "targets_principal_enactment": bool(context.get("named_target")),
                "target_enactment": principal_title,
                **{k: v for k, v in context.items() if k != "named_target"},
            }
            # A section that substitutes words without enumerating limbs states
            # the pair in its own sentence, so it is read off the section rather
            # than off a limb that is not there.
            pair = SUBSTITUTION_PAIR.search(remainder) if not operations else None
            if pair:
                node["amendment_instruction"]["substitutes"] = {
                    "from": pair.group("from").strip(),
                    "to": pair.group("to").strip(),
                }
            instructions.append({"in_section": number, **node["amendment_instruction"]})
        body.append(node)

    # Attach each carved insertion to the section that introduced it.
    for block in carved:
        provision = parse_inserted_block(block)
        if not provision:
            continue
        lead, children = nest_enumerated(provision["body"], principal_title)
        target = next(
            (
                n
                for n in body
                if n.get("amendment_instruction", {}).get("target_section") == provision["number"]
            ),
            body[-1] if body else None,
        )
        if target is None:
            continue
        target.setdefault("inserted_provisions", []).append(
            {
                "type": "inserted_provision",
                "inserted_into": principal_title,
                "provision": {
                    "type": "section",
                    "number": provision["number"],
                    "heading": provision["heading"],
                    "raw_text": re.sub(r"\s+", " ", provision["body"]).strip(),
                    "text": lead,
                    "amendment_events": [],
                    "cross_references": cross_references(lead, principal_title),
                    "children": children,
                },
            }
        )

    if not body:
        print("no sections found", file=sys.stderr)
        return 1
    if args.ocr_text:
        quality.append("parsed from OCR; wording needs checking against the scan")

    document = {
        "instrument_id": f"{args.number}-{args.year}",
        # An amending Act is cited by the principal enactment's name without the
        # word for what it is: the Act amending the Wills Ordinance is the Wills
        # (Amendment) Act, not the Wills Ordinance (Amendment) Act.
        "title": f"{ENACTMENT_WORD.sub('', principal_title)} (Amendment) Act",
        "long_title": long_title,
        "citation": {"type": "Act", "number": args.number, "year": args.year},
        "instrument_role": "amending",
        "amends": {
            "source_id": args.amends,
            "title": principal_title,
            "number": int(principal["act_or_ordinance_no"]),
            "year": int(principal["year"]),
        },
        "certified_on": certified.group(1).strip() if certified else "",
        "legal_draftsman_number": ld_number.group(1) if ld_number else "",
        "language": "en",
        "edition": {
            "publisher": "Government Printer, Sri Lanka",
            "kind": "as_enacted",
            "markup": markup,
            "local_path": source.relative_to(REPO_ROOT).as_posix(),
            "caveat": caveat,
        },
        "amendment_instructions": instructions,
        "verification_status": "unverified",
        "editorial_notes": [],
        "quality_flags": quality,
        "body": body,
    }

    # Hand-checked notes last, so a person's reading is never overwritten by a
    # re-run. The parser records what the Act says; the override says what is
    # wrong with what it says.
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    for key, value in overrides.get(document["instrument_id"], {}).items():
        if key.startswith("_"):
            continue
        if isinstance(value, list):
            document.setdefault(key, []).extend(value)
        else:
            document[key] = value

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target_path = OUT_DIR / f"{args.number}-{args.year}.json"
    target_path.write_text(
        json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {target_path.relative_to(REPO_ROOT)}")
    print(f"  {len(body)} sections, {len(instructions)} amending instructions")
    if args.show:
        for node in body:
            print(f"  s.{node['number']:<4} {node['heading'][:60]}")
            for operation in node.get("amendment_instruction", {}).get("operations", []):
                print(f"      {operation['operation']:22} -> {operation['target_label']}")
            for inserted in node.get("inserted_provisions", []):
                print(f"      inserts s.{inserted['provision']['number']}: "
                      f"{inserted['provision']['heading'][:55]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
