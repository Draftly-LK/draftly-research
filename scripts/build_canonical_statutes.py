"""Build a canonical, typed structure for each consolidated statute.

`parse_lankalaw_html.py` is the source-extraction layer: a flat list of sections
shaped like the existing section index. This is the layer above it. It reads the
same HTML and emits a structure that can carry the things a flat list cannot.

What this adds over the flat parse:

  recursive `children` with an explicit `type` on every node, rather than
    field names like `paragraphs` and `subparagraphs` that stop meaning
    anything once the drafting style changes
  typed definitions, one node per defined term, instead of a run of terms
    collapsed into whichever paragraph happened to come last
  cross-references lifted out of the prose, split into internal (this statute)
    and external (another enactment)
  amendment events per node, from the inline `[section, Act of Year]` markers
  `raw_text` and `text` only. `normalized_text` was a third copy of `text` in
    the older extractions and carried no information. Both hold this node alone
    and never its descendants: `raw_text` is the source fragment as printed,
    `text` the same wording with spacing normalised and any enumerator, marker
    or editor's note lifted out. A parent that opens straight into its first
    child carries an empty `text`, so no wording is stored twice.
  quality flags for suspected extraction damage, so an empty error list means
    "checked and clean" rather than "never looked"

Two markup traps this handles, both discovered against the Apartment Ownership
Law and both silent failures in the flat parse:

  * `sectioncontent` is overloaded. It holds a section number, and also each
    definition entry, and also the opening words that follow a section number.
    A definition is recognised by its leading quoted term, so it is no longer
    dropped for failing to look like a number.
  * The text after the section number lives outside the inner `</font>`, so a
    non-greedy match loses it. Section 26's "In this Law, unless the context
    otherwise requires-" vanished that way.

Nothing here is verified. LankaLaw is a private republisher, and an operation
such as substitution or repeal is not recorded anywhere in the markup, so every
amendment event carries `operation: unknown`.

    uv run python scripts/build_canonical_statutes.py
    uv run python scripts/build_canonical_statutes.py --source-id SRC012 --show
"""

from __future__ import annotations

import argparse
import collections
import csv
import html as html_module
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = REPO_ROOT / "data/legal-sources/library/statutes/HTML"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
COMMENCEMENT = REPO_ROOT / "data/processed/statute_commencement.csv"
OUT_DIR = REPO_ROOT / "data/processed/canonical-statutes"
OVERRIDES = REPO_ROOT / "data/processed/canonical-overrides.json"
MATCHES = REPO_ROOT / "data/processed/lankalaw-matches.csv"

CLASSES = (
    "actname|datesup|ordinancestitle|sectionpart|sectionparttitle|sectiontitle"
    "|sectionsubtitle|sectioncontent|sectionshorttitle"
    "|morginalnotes|subsectionshorttitle|subsectioncontent"
)
SPAN = re.compile(rf'class="({CLASSES})"[^>]*>(.*?)</font>', re.IGNORECASE | re.DOTALL)
# The section number sits in an inner bold font; the words after it are the
# section's opening text and belong to the same node.
SECTION_CELL = re.compile(
    r'class="sectioncontent"[^>]*>\s*<font[^>]*>(.*?)</font>(.*?)</font>', re.IGNORECASE | re.DOTALL
)
NUMBER_CELL = re.compile(r'<font size="1">\s*(\d{1,3})\s*of\s*(\d{4})\s*</font>', re.IGNORECASE)
CHAIN_HEAD = re.compile(r'class="ordinancestitle"[^>]*>\s*(Ordinance|Act|Law)s?\s*Nos?', re.IGNORECASE)
LONG_TITLE = re.compile(r'<META NAME="description" CONTENT="(.*?)"', re.IGNORECASE | re.DOTALL)

MARKER = re.compile(r"\[\s*([0-9]{1,3}[A-Z]?)\s*,\s*([^\]]+?)\s*\]")
SECTION_NUMBER = re.compile(r"^\d{1,3}[A-Z]{0,2}$")
FILE_NUMBER_YEAR = re.compile(r"^(\d{1,3})-(1[78]\d{2}|19\d{2}|20\d{2})-")
# A definition entry opens with the defined term in quotes of some flavour.
DEFINITION = re.compile(r'^["“‘\']\s*(.+?)\s*["”’\']+\s*(.*)$', re.DOTALL)
# A quoted opening alone is not enough, because statutes quote terms in ordinary
# prose too. The definitional verb after the term is what settles it, and testing
# for it also catches definitions that sit in subsectioncontent rather than
# sectioncontent, which is where the Kandyan Succession Ordinance puts them.
# A term can be defined after a lead-in rather than as a bare entry in an
# interpretation list: 'In this Ordinance "instrument affecting land" means ...'.
DEFINITION_LEAD_IN = re.compile(
    r"^(?:In|For the purposes of)\s+th(?:is|e)\s+(?:Ordinance|Act|Law|Code|subsection|section|Part)[\s,]*",
    re.IGNORECASE,
)
# A term is often qualified before the verb arrives: '"holder", in relation to
# any nindagama land, means ...'. Testing the verb against the text straight
# after the closing quote fails on those, and the definition is lost.
# Several defined terms can share one markup block. Each new quoted term
# followed by a definitional verb starts another definition, so the block has to
# be split before any of it is typed.
# A qualifier is usually comma-delimited ("'X', in relation to Y, means...")
# but a bare "in this Ordinance/Act/Law/Code" reads the same way with no
# commas at all: "'Public Trustee' in this Ordinance means..." (Buddhist
# Temporalities Ordinance section 2). Both shapes have to be recognised or
# the qualifier is read as the start of the definition text instead, and
# DEFINITION_VERB then fails to match because "in this Ordinance means..."
# does not start with a verb.
BARE_QUALIFIER = r"in\s+this\s+(?:Ordinance|Act|Law|Code)"
DEFINITION_START = re.compile(
    r"[\"“‘]\s*[^\"”’]{2,60}?\s*[\"”’]+\s*"
    rf"(?:,\s*[^,]{{1,90}},\s*|{BARE_QUALIFIER}\s+)?"
    r"(?:means|includes|shall\s+mean|shall\s+include|shall\s+be\s+interpreted)",
    re.IGNORECASE,
)
DEFINITION_QUALIFIER = re.compile(
    rf"^\s*(?:,\s*(?P<qualifier>[^,]{{1,90}}),\s*|(?P<bare_qualifier>{BARE_QUALIFIER})\s+)",
    re.IGNORECASE,
)
DEFINITION_VERB = re.compile(
    r"^(means\b|includes\b|shall mean\b|shall include\b|shall be interpreted\b"
    r"|has the same meaning\b|does not include\b|shall be deemed\b)",
    re.IGNORECASE,
)

# Enumerators, outermost first. Numbering style is the only signal the markup
# gives for depth, so the level is inferred from the shape of the label.
ENUMERATORS = (
    ("subsection", re.compile(r"^\(\s*(\d{1,3}[A-Z]?)\s*\)\s*(.*)$", re.DOTALL)),
    ("subparagraph", re.compile(r"^\(\s*([ivxlc]{1,6})\s*\)\s*(.*)$", re.DOTALL | re.IGNORECASE)),
    ("paragraph", re.compile(r"^\(\s*([a-z]{1,2})\s*\)\s*(.*)$", re.DOTALL)),
)
# Depth drives the nesting. Not every statute uses every level: the Apartment
# Ownership Law is Act -> Section, the Companies Act is Act -> Part ->
# crossheading -> Section. Levels simply do not appear when the statute omits them.
#
# `subheading` sits BELOW `crossheading` here, which inverts the usual
# Part/Chapter/Division/Crossheading ordering. That follows the markup: LankaLaw
# emits sectionsubtitle inside a sectiontitle group, not above it.
# Spaced by tens so a level can be slotted between two others without renumbering.
# `definition` sits just below `subsection` and just above `paragraph`: an
# interpretation section may wrap its terms in a subsection, and a single term may
# itself be split into lettered limbs, as "common elements" is.
DEPTH = {
    "part": 0,
    "chapter": 10,
    "crossheading": 20,
    "subheading": 30,
    "section": 40,
    # Text that follows a lettered list and closes the section belongs to the
    # section, not to the last paragraph it happens to sit after.
    "closing_text": 45,
    # A bare entry in a list the provision introduces, such as the four
    # Ordinances named in s.2(3). Sits with paragraphs, not below them.
    "item": 60,
    "subsection": 50,
    "definition": 55,
    "paragraph": 60,
    "proviso": 65,
    "subparagraph": 70,
    "text": 80,
}
# LankaLaw prints the statute's place in the revised edition at the foot of the
# page: "Chapter 114, Volume No. 5 Page No.278."
SOURCE_LOCATION = re.compile(
    r"Chapter\s*([0-9]{1,3})\s*,\s*Volume\s*No\.?\s*([0-9]{1,2})\s*Page\s*No\.?\s*([0-9]{1,4})",
    re.IGNORECASE,
)
# A gazette running header/footer ("<Short Title> <page no.> Act, No. NN of
# YYYY") occasionally sits on the same line as the last provision on the page
# and gets read straight into it, as "...or Urban Development Authority
# (Special Provisions) 5 Act, No. 44 of 1984". Genuine prose never has a bare
# page number wedged between a title and the Ordinance/Act/Law/Code keyword,
# so that shape is a safe, statute-agnostic signature for the artifact -
# anchored to the end of the fragment so it can only ever trim a trailing
# bleed, never touch the substance before it.
RUNNING_FOOTER = re.compile(
    r"\s+(?:[A-Z][A-Za-z'-]*|\([A-Za-z\s]+\))"
    r"(?:\s+(?:[A-Z][A-Za-z'-]*|\([A-Za-z\s]+\)|of|and|the|for)){1,8}"
    r"\s+\d{1,3}\s+(?:Ordinance|Act|Law|Code)\s*,?\s*N[o°]?\.?\s*\d{1,3}\s+of\s+\d{4}\s*$"
)


def strip_running_footer(text: str) -> str:
    return RUNNING_FOOTER.sub("", text).rstrip()
ROMAN_PART = re.compile(r"^PART\s+([IVXLC]+|\d+)\s*$", re.IGNORECASE)
# A statute with a single schedule just calls it "the Schedule", so requiring an
# ordinal reports no schedule at all for those.
SCHEDULE_REF = re.compile(
    r"\b((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth"
    r"|Eleventh|Twelfth|Thirteenth)\s+Schedule|the\s+Schedule)\b"
)
# "subsection (1) of section 20" and "section 20 (1)" both point at a provision,
# not merely at a section.
SUBSECTION_REF = re.compile(
    r"\bsubsection\s*\(\s*(\d{1,3}[A-Z]?)\s*\)\s*of\s+section\s+(\d{1,3}[A-Z]{0,2})"
    r"|\bsection\s+(\d{1,3}[A-Z]{0,2})\s*\(\s*(\d{1,3}[A-Z]?)\s*\)",
    re.IGNORECASE,
)

INTERNAL_REF = re.compile(r"\bsections?\s+(\d{1,3}[A-Z]{0,2})\b(?!\s+of\s+the)", re.IGNORECASE)
# A reference can name a run of sections: "sections 36 to 39 of the Registration
# of Documents Ordinance". Matching only the last number leaves the earlier ones
# to be read as references to this statute's own sections, which they are not.
EXTERNAL_REF = re.compile(
    # A run can restate "section(s)" for each further number ("section 287 or
    # section 288") rather than just listing bare numbers, and a range can
    # carry a parenthetical aside before naming its statute ("sections 120 to
    # 127 (both inclusive) of the Land Development Ordinance"). Both still
    # name an external statute at the end, so both belong to it and not to
    # this one.
    r"\bsections?\s+(\d{1,3}[A-Z]{0,2}(?:\s*(?:,|and|or|to)\s*(?:sections?\s+)?\d{1,3}[A-Z]{0,2})*)"
    r"(?:\s*\([^()]{0,40}\))?"
    r"\s+of\s+the\s+([A-Z][A-Za-z'()\s,.-]{4,70}?(?:Ordinance|Act|Law|Code))",
)
SECTION_IN_LIST = re.compile(r"\d{1,3}[A-Z]{0,2}")
# Every word of a title is capitalised apart from short connectors. Allowing any
# run of characters lets "Abolished by the Abolition of Fideicommissa and Entails
# Act" be captured whole, which names a document that does not exist.
TITLE_WORD = r"(?:[A-Z][A-Za-z'()\-]*|of|and|the|for|on|in|to)"
ENACTMENT_REF = re.compile(
    rf"\b((?:{TITLE_WORD}\s+){{1,9}}?(?:Ordinance|Act|Law|Code))\s*,?\s*"
    r"N[o°]?\.?\s*(\d{1,3})\s+of\s+(\d{4})"
)
# An editor's note is not part of the provision it sits in. It appears either as
# its own asterisked line, or spliced into the middle of the text at the point it
# annotates, as `fideicommissa*(*. Abolished by ... .)`.
EDITORIAL_NOTE = re.compile(r"^\*+\s*\(?\s*\*?\s*\.?\s*(?P<text>.+?)\s*\)?\s*$", re.DOTALL)
INLINE_NOTE = re.compile(
    r"(?P<anchor>(?:[A-Z][A-Za-z'()\-]*\s+)*[A-Z][A-Za-z'()\-]*|\w+)"
    r"(?P<sep>\s*[;,]?\s*)"
    r"\*\s*[\(\[]\s*\*?\.?\s*(?P<text>[^)\]]+?)\s*[\)\]]"
)
# A footnote often cites an instrument without naming it: "Repealed by Act No.
# 44 of 1952". The citation is recorded; identifying which statute that is would
# be a legal judgement, so target_document is left empty.
# A note can also stand alone at the end of a provision, its asterisk left back
# on the word it annotates: "...such cessation. [* See the List of Enactments
# omitted from the Revised Edition]".
# The marker is not always an asterisk: "[+ Section 30 ... is omitted]".
DETACHED_NOTE = re.compile(r"\[\s*[*+†‡]\s*(?P<text>[^\]]+?)\s*\]")
BARE_CITATION = re.compile(
    r"(Act|Ordinance|Law)\s+N[o°]?\.?\s*(\d{1,3})\s+of\s+(\d{4})", re.IGNORECASE
)

# An enactment is often named without a citation: "the Kandyan Marriage Ordinance,
# the Kandyan Marriage and Divorce Act". Two or more capitalised words before the
# keyword keeps "this Ordinance" and "the said Act" out.
NAMED_ENACTMENT = re.compile(
    # A word may open with a bracket: "Kandyan Marriages (Removal of Doubts)
    # Ordinance". Requiring a capital first character drops the bracketed part
    # and with it the whole title.
    r"\bthe\s+((?:[A-Z(][A-Za-z'()\-]*\s+(?:of\s+|and\s+|the\s+)?){1,8}"
    r"(?:Ordinance|Act|Law|Code))\b"
)

# Tokens that are almost certainly extraction damage rather than drafting.
# Errors seen in the sources so far. Listing them means an empty quality_flags
# says "checked against these" rather than "never looked".
SUSPECT_TOKENS = (
    "Mm ", "Proprety", "redvision", "logging of persons", "�",
    "Jess than", "take slops",
)
PROVISO = re.compile(
    # "it is provided that" is an ordinary statement of what the instrument
    # says, not a legal proviso qualifying the provision; splitting it off
    # left National Housing Act section 58's own text as the sentence
    # fragment "...it is". A real proviso opens its own clause.
    r"(?<!it is )\bProvided\s*,?\s*(?:however|always|further|nevertheless)?\s*,?\s*that\b",
    re.IGNORECASE,
)

# One markup element can carry several provisions: "(1) Nothing ... shall
# affect- (a) the mutual rights ...". Splitting on every bracketed token would
# also break "paragraphs (c) and (d)" mid-sentence, so a split point must follow
# a list-introducing character rather than an ordinary word.
ENUM_TOKEN = re.compile(
    # A stray quote can stand where the colon should be: `Plan" (i) file the...`.
    r"(?:(?<=^)|(?<=[;:\-–—.\"”’]\s)|(?<=[;:\-–—])\s*)"
    r"\(\s*(\d{1,3}[A-Z]?|[a-z]{1,2})\s*\)",
    re.IGNORECASE,
)


def text_of(fragment: str) -> str:
    plain = html_module.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", plain.replace("\xa0", " ")).strip()


def raw_of(fragment: str) -> str:
    plain = html_module.unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"[ \t]+", " ", plain.replace("\xa0", " ")).strip()


def bare_citations(text: str) -> list[dict]:
    return [
        {
            "kind": "enactment",
            "target_document": "",
            "target_citation": f"{m.group(1).title()} No. {m.group(2)} of {m.group(3)}",
            "verbatim": m.group(0),
            "note": "the source names no title for this instrument",
        }
        for m in BARE_CITATION.finditer(text)
    ]


def split_inline_notes(
    text: str, self_title: str, current_section: str = ""
) -> tuple[str, list[dict]]:
    """Pull an editor's note out of the middle of a provision."""
    notes = []
    for match in INLINE_NOTE.finditer(text):
        body = match.group("text").strip()
        notes.append(
            {
                "marker": "*",
                "anchor_text": match.group("anchor"),
                "raw_text": match.group(0),
                "text": body,
                "cross_references": cross_references(body, self_title) or bare_citations(body),
            }
        )
    cleaned = INLINE_NOTE.sub(lambda m: m.group("anchor") + m.group("sep"), text)
    for match in DETACHED_NOTE.finditer(cleaned):
        body = match.group("text").strip()
        notes.append(
            {
                "marker": "*",
                "anchor_text": "",
                "raw_text": match.group(0),
                "text": body,
                "cross_references": cross_references(body, self_title) or bare_citations(body),
            }
        )
    cleaned = DETACHED_NOTE.sub("", cleaned)
    # Removing the note leaves the space that stood before it, so the following
    # comma is left floating: "fideicommissa , usufructs".
    cleaned = re.sub(r"\s+([,;.:])", r"\1", re.sub(r"\s{2,}", " ", cleaned))
    return cleaned.strip(), notes


def split_markers(text: str) -> tuple[str, list[dict[str, str]]]:
    events = []
    for match in MARKER.finditer(text):
        act = re.sub(r"\s+", " ", match.group(2)).strip()
        if not re.search(r"\d{4}", act):
            continue
        number_year = re.match(r"(\d{1,3})\s*of\s*(\d{4})", act)
        events.append(
            {
                "amending_act": act,
                "amending_act_no": int(number_year.group(1)) if number_year else None,
                "amending_year": int(number_year.group(2)) if number_year else None,
                "amending_section": match.group(1),
                "operation": "unknown",
                "verbatim": match.group(0),
            }
        )
    # Normalisation removes spacing noise, not punctuation. A trailing full stop
    # is part of the provision. Only the separator debris a removed marker leaves
    # behind is cleaned up.
    stripped = re.sub(r"\s{2,}", " ", MARKER.sub("", text)).strip()
    stripped = re.sub(r"^[;,]\s*", "", stripped).strip()
    return stripped, events


def split_provisos(pieces: list[str]) -> list[str]:
    """A proviso is usually printed inside the provision it qualifies. Splitting
    it out is what lets it be typed, rather than left inside the parent's text."""
    out = []
    for piece in pieces:
        start = PROVISO.search(piece)
        if start and start.start() > 0:
            head, tail = piece[: start.start()].strip(), piece[start.start():].strip()
            out.extend(x for x in (head, tail) if x)
        else:
            out.append(piece)
    return out


def split_enumerated(text: str) -> list[str]:
    """One element into one block per provision it actually carries."""
    points = []
    for m in ENUM_TOKEN.finditer(text):
        # "the provisions of subsection- (1) of section 19c" is a cross-reference
        # that happens to land right after a hyphen, not a new item introduced by
        # one: a line-wrap hyphenation before "subsection" leaves the same shape
        # as a genuine "as follows- (1) ...". A real list item never opens with
        # "of section", so that tail is enough to tell the two apart.
        tail = text[m.end():m.end() + 15]
        if re.match(r"\s*of\s+section\b", tail, re.IGNORECASE):
            continue
        points.append(m.start())
    # One enumerator still needs splitting when text runs ahead of it, as in
    # "Provided that- (i) the fact that ...": the proviso and its first limb.
    if not points or (len(points) == 1 and points[0] == 0):
        return [text]
    if points[0] > 0:
        points.insert(0, 0)
    parts = []
    for start, end in zip(points, points[1:] + [len(text)]):
        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
    return parts


def split_definitions(text: str) -> list[str]:
    """One block into one piece per term it defines."""
    starts = [m.start() for m in DEFINITION_START.finditer(text)]
    if len(starts) < 2:
        return [text]
    if starts[0] > 0:
        starts.insert(0, 0)
    pieces = []
    for start, end in zip(starts, starts[1:] + [len(text)]):
        piece = text[start:end].strip(" ;,")
        if piece:
            pieces.append(piece)
    return pieces


def parse_definition(body: str) -> tuple[str, str, str] | None:
    """(term, qualifier, definition text) when the block defines a term."""
    match = DEFINITION.match(body)
    if not match:
        return None
    rest = match.group(2).strip()
    qualifier = ""
    qualified = DEFINITION_QUALIFIER.match(rest)
    if qualified:
        candidate = rest[qualified.end():]
        if DEFINITION_VERB.match(candidate):
            found = qualified.group("qualifier") or qualified.group("bare_qualifier")
            qualifier, rest = found.strip(), candidate
    if not DEFINITION_VERB.match(rest):
        return None
    # A doubled opening quote leaves one inside the captured term.
    term = re.sub(r"\s+", " ", match.group(1)).strip().strip("\"“”‘’' ")
    return term, qualifier, rest


ROMAN_DIGITS = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def roman_value(label: str) -> int:
    """The numeric value of a roman label, or 0 if it is not one."""
    label = label.lower()
    if not label or any(ch not in ROMAN_DIGITS for ch in label):
        return 0
    total, previous = 0, 0
    for ch in reversed(label):
        value = ROMAN_DIGITS[ch]
        total = total - value if value < previous else total + value
        previous = max(previous, value)
    return total


def classify(text: str) -> tuple[str, str, str]:
    """(type, number, remaining text) for one body block."""
    for kind, pattern in ENUMERATORS:
        match = pattern.match(text)
        if match:
            label = match.group(1)
            # (c), (i), (v), (x) and (l) are all valid roman numerals and all
            # valid paragraph letters. Lettered paragraphs are much the commoner
            # use at that level, so a single character is read as a paragraph and
            # only a multi-character roman such as (ii) or (iv) as a subparagraph.
            # A genuine one-item roman list is misread by this, which is the
            # cheaper error.
            if kind == "subparagraph" and len(label) == 1:
                return "paragraph", label, strip_running_footer(match.group(2).strip())
            return kind, label, strip_running_footer(match.group(2).strip())
    if PROVISO.match(text):
        return "proviso", "", strip_running_footer(text)
    return "text", "", strip_running_footer(text)


KEYWORD_ONLY = re.compile(r"^(?:Act|Ordinance|Law|Code)", re.IGNORECASE)


def clean_title(name: str) -> str:
    """Trim the article and reject a capture that began at the keyword itself.

    "Act and of the Apartment Ownership Law" is what a greedy match produces
    when it starts on the trailing keyword of the previous title.
    """
    # Strip every leading connector, not just one: "of the Apartment Ownership
    # Law" must lose both words, or the article survives into the title.
    name = re.sub(
        r"^(?:(?:the|of|and|for|on|in|to)\s+)+", "",
        re.sub(r"\s+", " ", name).strip(" ,."), flags=re.IGNORECASE,
    )
    return "" if KEYWORD_ONLY.match(name) else name


# "section 2 of that Ordinance" points at whichever enactment was last named,
# not at this one. Reading it as internal sends the reference to the wrong Act.
THAT_ENACTMENT = re.compile(
    r"sections?\s+(\d{1,3}[A-Z]{0,2})\s+of\s+(?:that|the said)\s+(Ordinance|Act|Law|Code)",
    re.IGNORECASE,
)
BARE_SUBSECTION = re.compile(
    r"(?:under|in|of|to|by|from)\s+subsection\s*\(\s*(\d{1,3}[A-Z]?)\s*\)(?!\s*of)", re.IGNORECASE
)


def cross_references(
    text: str, self_title: str, self_section: str = "", last_named: str = ""
) -> list[dict[str, str]]:
    refs = []
    for match in THAT_ENACTMENT.finditer(text):
        refs.append(
            {
                "kind": "external" if last_named else "unresolved",
                "target_document": last_named,
                "target_section": match.group(1),
                "verbatim": match.group(0),
                "note": "" if last_named else "refers back to an enactment named earlier in the section",
            }
        )
    covered = []
    covered_that = [(m.start(), m.end()) for m in THAT_ENACTMENT.finditer(text)]
    for match in BARE_SUBSECTION.finditer(text):
        # "under subsection (1)" with no section named means this section's own.
        if not self_section:
            continue
        refs.append(
            {
                "kind": "internal",
                "target_document": self_title,
                "target_section": self_section,
                "target_subsection": match.group(1),
                "verbatim": match.group(0),
            }
        )
    for match in SUBSECTION_REF.finditer(text):
        covered.append((match.start(), match.end()))
        section = match.group(2) or match.group(3)
        subsection = match.group(1) or match.group(4)
        refs.append(
            {
                "kind": "internal",
                "target_document": self_title,
                "target_section": section,
                "target_subsection": subsection,
                "verbatim": match.group(0),
            }
        )
    for match in EXTERNAL_REF.finditer(text):
        covered.append((match.start(), match.end()))
        title = clean_title(match.group(2))
        for number in SECTION_IN_LIST.findall(match.group(1)):
            refs.append(
                {
                    "kind": "external",
                    "target_document": title,
                    "target_section": number,
                    "verbatim": match.group(0),
                }
            )
    for match in INTERNAL_REF.finditer(text):
        # A number inside an external reference belongs to that statute, not this
        # one. Ranges are why this has to be a span check and not a lookahead.
        if any(start <= match.start() < end for start, end in covered + covered_that):
            continue
        refs.append(
            {
                "kind": "internal",
                "target_document": self_title,
                "target_section": match.group(1),
                "verbatim": match.group(0),
            }
        )
    for match in NAMED_ENACTMENT.finditer(text):
        name = clean_title(match.group(1))
        if not name or len(re.findall(r"[A-Z][a-z]+", name)) < 2:
            continue
        # The short title declares the statute's own name. That is not a
        # cross-reference to anything, so it is dropped rather than retyped.
        if name.lower() == self_title.lower():
            continue
        refs.append(
            {
                "kind": "enactment",
                "target_document": name,
                "verbatim": match.group(0).strip(),
            }
        )
    for match in ENACTMENT_REF.finditer(text):
        refs.append(
            {
                "kind": "enactment",
                "target_document": clean_title(match.group(1)),
                "target_document_note": ""
                if clean_title(match.group(1))
                else "the title could not be read from the surrounding text",
                "target_citation": f"No. {match.group(2)} of {match.group(3)}",
                "verbatim": match.group(0),
            }
        )
    seen, unique = set(), []
    for ref in refs:
        if not ref.get("target_document") and not ref.get("target_citation"):
            continue
        if ref["kind"] == "enactment" and ref["target_document"].lower() == self_title.lower():
            continue
        key = (ref["kind"], ref["target_document"], ref.get("target_section"), ref.get("target_citation"))
        if key not in seen:
            seen.add(key)
            unique.append(ref)
    return unique


def nest(blocks: list[dict]) -> list[dict]:
    """Turn a flat run of typed blocks into a tree by their depth.

    A block may carry `_depth` to sit at a level its type alone cannot express,
    so the stack has to remember the depth each node was placed at rather than
    re-deriving it from the type.
    """
    roots: list[dict] = []
    stack: list[tuple[int, dict]] = []
    for block in blocks:
        depth = block.pop("_depth", None) or DEPTH[block["type"]]
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            stack[-1][1].setdefault("children", []).append(block)
        else:
            roots.append(block)
        stack.append((depth, block))
    return roots


def parse(page: str, self_title: str) -> tuple[list[dict], list[tuple[str, int, int]], str]:
    """Return (body, chain, long_title)."""
    long_title_match = LONG_TITLE.search(page)
    long_title = text_of(long_title_match.group(1)) if long_title_match else ""

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
    chain = list(dict.fromkeys(chain))

    # Section cells need the number and its trailing opening text together, so
    # they are matched separately and spliced back into the span stream by offset.
    stream: list[tuple[int, str, str, str]] = []
    for match in SPAN.finditer(page):
        stream.append((match.start(), match.group(1).lower(), match.group(2), ""))
    section_cells = {}
    for match in SECTION_CELL.finditer(page):
        section_cells[match.start()] = (match.group(1), match.group(2))

    has_crossheadings = 'class="sectiontitle"' in page
    current_section = ""
    last_named_enactment = ""
    sections: list[dict] = []
    outline: list[dict] = []
    editorial: list[dict] = []
    pending_heading, pending_events = "", []
    pending_trailing: list[str] = []
    pending_part = ""
    in_definitions = False
    current_blocks: list[dict] = []

    def track_named(refs: list[dict]) -> list[dict]:
        nonlocal last_named_enactment
        for ref in refs:
            if ref["kind"] == "enactment" and ref.get("target_document"):
                last_named_enactment = ref["target_document"]
        return refs

    def flush() -> None:
        # Anything the section cell carried that no later element repeated is
        # added now, so a provision printed only once is never dropped.
        for piece in pending_trailing:
            head = classify(piece)[2][:40]
            if head and not any(b.get("text", "").startswith(head) for b in current_blocks):
                kind, label, remainder = classify(piece)
                current_blocks.append(
                    {
                        "type": kind,
                        "number": label,
                        "raw_text": piece,
                        "text": remainder,
                        "amendment_events": [],
                        "cross_references": track_named(cross_references(remainder, self_title, current_section, last_named_enactment)),
                    }
                )
        pending_trailing.clear()
        if sections and current_blocks:
            # A lettered list read by OCR can yield a digit: "(6)" for "(b)"
            # after "(a)". Retype it only when the letter it resembles is the one
            # the sequence is waiting for, and keep the printed label.
            confusable = {"6": "b", "1": "i", "0": "o", "5": "s", "8": "B", "9": "g"}
            for earlier, later in zip(current_blocks, current_blocks[1:]):
                if later["type"] != "subsection" or earlier["type"] != "paragraph":
                    continue
                expected = chr(ord(earlier.get("number", "a")[:1]) + 1)
                if confusable.get(later.get("number", "")) == expected:
                    later["raw_label"] = f"({later['number']})"
                    later["number"] = expected
                    later["type"] = "paragraph"
                    later["label_correction_status"] = "inferred_from_sequence"
            # A single character is read as a paragraph letter, which is right for
            # (a), (b), (c) but wrong for (v) sitting in a roman run. Once a
            # roman list is open, a following single roman character continues it.
            # It continues the run only if it is the next numeral: (v) after
            # (iv) does, but (c) after (vi) is paragraph (c), not 100.
            for index in range(1, len(current_blocks)):
                block, previous = current_blocks[index], current_blocks[index - 1]
                if block["type"] != "paragraph" or previous["type"] != "subparagraph":
                    continue
                here, before = roman_value(block.get("number", "")), roman_value(previous.get("number", ""))
                if here and before and here == before + 1:
                    block["type"] = "subparagraph"
                    block["label_correction_status"] = "roman_run_continued"
            # "(i)" reads as a paragraph letter on its own, but an "(ii)" right
            # after it makes both roman. Settle that before nesting, or the two
            # land at different depths and (ii) becomes a child of (i).
            for earlier, later in zip(current_blocks, current_blocks[1:]):
                if earlier.get("number", "").lower() == "i" and later.get("number", "").lower() == "ii":
                    earlier["type"] = "subparagraph"
            # Text after a lettered list closes the list rather than belonging
            # to its last item, so it takes that list's own level. A run of
            # bare entries introduced by a colon or dash is a list of items.
            for index, block in enumerate(current_blocks):
                if block["type"] != "text" or index == 0:
                    continue
                previous = current_blocks[index - 1]
                if previous["type"] == "item":
                    block["type"] = "item"
                elif previous["type"] in {"paragraph", "subparagraph"}:
                    block["type"] = "closing_text"
                    block["_depth"] = DEPTH[previous["type"]]
                elif previous["type"] == "subsection" and previous["text"].rstrip().endswith(
                    (":", "-", ":-", ";")
                ):
                    block["type"] = "item"
            # A stray block in the middle of a run of definitions is an entry the
            # source damaged past recognition -- a term whose opening quote is
            # missing, say -- not a container. `closing_text` sits above
            # `definition` in DEPTH, so left alone such a block adopts every term
            # printed after it as a child. Same rule as above: text inside a list
            # takes that list's own level.
            # Two damaged entries can sit next to each other, so it is the run
            # the block falls inside that settles this, not the one block before
            # it: a definition on either side means the block is in the list.
            for index, block in enumerate(current_blocks):
                # A block the rule above already placed is closing a list of its
                # own, one nested inside a definition among others. Leave it.
                if block["type"] != "closing_text" or "_depth" in block:
                    continue
                before = any(b["type"] == "definition" for b in current_blocks[:index])
                after = any(b["type"] == "definition" for b in current_blocks[index + 1 :])
                if before and after:
                    block["_depth"] = DEPTH["definition"]
            nested = nest(list(current_blocks))
            parent = sections[-1]
            # Where a section opens straight into its first subsection, that text
            # is printed both in the section cell and again as the subsection.
            # Keeping both duplicates the wording for anything reading `text`.
            # A section that opens straight into its first subsection has that
            # wording printed twice: once in the section cell and again as the
            # subsection. Drop the copy on the section so `text` is not duplicated.
            opening = re.sub(r"^\(\s*\w{1,4}\s*\)\s*", "", parent.get("text", ""))
            first = nested[0].get("text", "") if nested else ""
            if opening and first and opening.startswith(first[:60]):
                parent["text"] = ""
            parent["children"] = nested
        current_blocks.clear()

    for offset, name, fragment, _ in stream:
        value = text_of(fragment)
        if not value:
            continue

        if name == "sectionpart":
            match_part = ROMAN_PART.match(value)
            pending_part = match_part.group(1) if match_part else value
        elif name == "sectionparttitle":
            flush()
            node = {"type": "part", "number": pending_part, "heading": value}
            outline.append(node)
            sections.append(node)
            pending_part = ""
        elif name in {"sectiontitle", "sectionsubtitle"}:
            flush()
            # The same class means different things in different statutes. Where
            # a document also uses sectiontitle, sectionsubtitle is the deeper of
            # the two; where it is the only structural heading, as in the
            # Registration of Title Act, it is the crossheading level itself.
            node = {
                "type": "crossheading"
                if name == "sectiontitle" or not has_crossheadings
                else "subheading",
                "number": "",
                "heading": value,
            }
            outline.append(node)
            sections.append(node)
        elif name == "datesup":
            tail = value.split("]")[-1].strip()
            if tail:
                pending_heading, extra = split_markers(tail)
                pending_events.extend(extra)
        elif name in {"sectionshorttitle", "morginalnotes"}:
            heading, extra = split_markers(value)
            if name == "sectionshorttitle" and heading:
                pending_heading = heading
            pending_events.extend(extra)
        elif name == "subsectionshorttitle":
            _, extra = split_markers(value)
            if current_blocks:
                current_blocks[-1].setdefault("amendment_events", []).extend(extra)
            elif sections:
                sections[-1].setdefault("amendment_events", []).extend(extra)
        elif name == "sectioncontent":
            number, opening = section_cells.get(offset, (value, ""))
            number = text_of(number)
            opening_raw = text_of(opening)
            # A section-letter suffix sometimes sits outside the number's own
            # font tag, e.g. "<a>90</a>E. Notwithstanding..." for what the
            # print calls section 90E. Reattach it when doing so still yields
            # a well-formed section number, so the digits and the letter do
            # not end up split across two different nodes (National Housing
            # Act section 90E, lost to a bare duplicate "90" otherwise).
            suffix_match = re.match(r"^([A-Z])\.\s+(?=\S)", opening_raw)
            if suffix_match and SECTION_NUMBER.match(number + suffix_match.group(1)):
                number = number + suffix_match.group(1)
                opening_raw = opening_raw[suffix_match.end():]
            opening_text = opening_raw.lstrip(". ").strip()

            if value.lstrip().startswith("*"):
                note = EDITORIAL_NOTE.match(value.strip())
                body = (note.group("text") if note else value).strip()
                editorial.append(
                    {
                        "marker": "*",
                        "anchor_section": sections[-1]["number"] if sections else "",
                        "raw_text": raw_of(fragment),
                        "text": body,
                        "cross_references": track_named(cross_references(body, self_title, current_section, last_named_enactment)),
                    }
                )
                continue
            definition = DEFINITION.match(value)
            if SECTION_NUMBER.match(number):
                flush()
                body, extra = split_markers(opening_text)
                body, inline = split_inline_notes(body, self_title)
                for note in inline:
                    editorial.append({**note, "anchor_section": number})
                # The section cell can carry the introduction and the first
                # provisions together. The section keeps only its introduction;
                # the rest become children, so nothing is stored at two levels.
                opening_parts = split_provisos(split_enumerated(body))
                if ENUM_TOKEN.match(body):
                    body, trailing = "", opening_parts
                else:
                    body, trailing = opening_parts[0], opening_parts[1:]
                node = {
                    "type": "section",
                    "number": number,
                    "heading": pending_heading,
                    # Kept in step with `text`: the section holds only its own
                    # opening, never the children that follow it.
                    "raw_text": f"{number}. {body}".strip() if body else f"{number}.",
                    "text": body,
                    "amendment_events": pending_events + extra,
                    "cross_references": track_named(cross_references(body, self_title, current_section, last_named_enactment)),
                }
                current_section = number
                last_named_enactment = ""
                sections.append(node)
                outline.append(node)
                pending_trailing = list(trailing)
                # A whole section can be one definition. Emitting it as a typed
                # child keeps every defined term reachable the same way.
                lead = DEFINITION_LEAD_IN.match(body)
                if lead:
                    rest = body[lead.end():]
                    defined_here = DEFINITION.match(rest)
                    if defined_here and DEFINITION_VERB.match(defined_here.group(2).strip()):
                        node["text"] = body[: lead.end()].strip()
                        current_blocks.append(
                            {
                                "type": "definition",
                                "term": re.sub(r"\s+", " ", defined_here.group(1)).strip(),
                                "raw_text": rest,
                                "text": defined_here.group(2).strip(),
                                "amendment_events": [],
                                "cross_references": cross_references(
                                    defined_here.group(2), self_title
                                ),
                            }
                        )
                in_definitions = bool(re.search(r"\bunless the context otherwise requires\b", body, re.I))
                pending_heading, pending_events = "", []
            elif definition and in_definitions:
                parsed = parse_definition(value)
                term = parsed[0] if parsed else re.sub(r"\s+", " ", definition.group(1)).strip()
                body, extra = split_markers(parsed[2] if parsed else definition.group(2))
                parts = split_enumerated(body)
                current_blocks.append(
                    {
                        "type": "definition",
                        "term": term,
                        "raw_text": raw_of(fragment),
                        # A term defined as "means- (a) ... (b) ..." keeps only
                        # the lead-in; the limbs become children.
                        "text": parts[0],
                        "amendment_events": pending_events + extra,
                        "cross_references": cross_references(parts[0], self_title, current_section),
                    }
                )
                for limb in parts[1:]:
                    kind, label, remainder = classify(limb)
                    current_blocks.append(
                        {
                            "type": kind,
                            "number": label,
                            "raw_text": limb,
                            "text": remainder,
                            "amendment_events": [],
                            "cross_references": track_named(cross_references(remainder, self_title, current_section, last_named_enactment)),
                        }
                    )
                pending_events = []
            elif sections:
                body, extra = split_markers(value)
                for piece in split_provisos(split_enumerated(body)):
                    kind, label, remainder = classify(piece)
                    current_blocks.append(
                        {
                            # A sectioncontent block that is neither a number nor
                            # a definition is the section's own continuation.
                            "type": "closing_text" if kind == "text" else kind,
                            "number": label,
                            "raw_text": piece,
                            "text": remainder,
                            "amendment_events": extra,
                            "cross_references": track_named(cross_references(remainder, self_title, current_section, last_named_enactment)),
                        }
                    )
                    extra = []
        elif name == "subsectioncontent" and sections:
            body, extra = split_markers(value)
            body, inline = split_inline_notes(body, self_title)
            for note in inline:
                editorial.append(
                    {**note, "anchor_section": sections[-1]["number"] if sections else ""}
                )
            # "In this subsection \"interest\" means ..." defines a term for the
            # whole subsection, so it is lifted to sit beside the paragraphs.
            scope_lead = DEFINITION_LEAD_IN.match(body)
            after_lead = body[scope_lead.end():] if scope_lead else body
            # One block can carry several terms; each becomes its own node.
            definition_pieces = split_definitions(after_lead)
            if len(definition_pieces) > 1 and not scope_lead:
                for piece in definition_pieces:
                    parsed_piece = parse_definition(piece)
                    if not parsed_piece:
                        continue
                    term_p, qualifier_p, text_p = parsed_piece
                    current_blocks.append(
                        {
                            "type": "definition",
                            "term": term_p,
                            "qualifier": qualifier_p,
                            "raw_text": piece,
                            "text": text_p,
                            "amendment_events": extra,
                            "cross_references": track_named(
                                cross_references(text_p, self_title, current_section, last_named_enactment)
                            ),
                        }
                    )
                    extra = []
                continue
            defined = parse_definition(after_lead)
            if defined and scope_lead:
                term, qualifier, definition_text = defined
                current_blocks.append(
                    {
                        "type": "definition",
                        "term": term,
                        "qualifier": qualifier,
                        "scope": body[: scope_lead.end()].strip(" ,"),
                        "raw_text": raw_of(fragment),
                        "text": definition_text,
                        "amendment_events": extra,
                        "cross_references": cross_references(
                            definition_text, self_title, current_section
                        ),
                    }
                )
                continue
            if defined:
                term, qualifier, definition_text = defined
                parts = split_enumerated(definition_text)
                current_blocks.append(
                    {
                        "type": "definition",
                        "term": term,
                        "qualifier": qualifier,
                        "raw_text": raw_of(fragment),
                        # "owner means- (a) ... (b) ..." keeps only "means-" here;
                        # the limbs become children so none is left inside the text.
                        "text": parts[0],
                        "amendment_events": extra,
                        "cross_references": cross_references(parts[0], self_title, current_section),
                    }
                )
                for limb in parts[1:]:
                    kind, label, remainder = classify(limb)
                    current_blocks.append(
                        {
                            "type": kind,
                            "number": label,
                            "raw_text": limb,
                            "text": remainder,
                            "amendment_events": [],
                            "cross_references": track_named(cross_references(remainder, self_title, current_section, last_named_enactment)),
                        }
                    )
                continue
            for piece in split_provisos(split_enumerated(body)):
                kind, label, remainder = classify(piece)
                current_blocks.append(
                    {
                        "type": kind,
                        "number": label,
                        "raw_text": piece,
                        "text": remainder,
                        "amendment_events": extra,
                        "cross_references": track_named(cross_references(remainder, self_title, current_section, last_named_enactment)),
                    }
                )
                extra = []

    flush()
    # Parts, crossheadings and sections are one stream; nest() turns the flat
    # run into a tree using DEPTH, so a statute with no Parts is unaffected.
    return nest(outline), chain, long_title, editorial


def dedupe_events(nodes: list[dict]) -> None:
    """A marker printed in both the heading and the marginal-note block is one
    amendment, not two. Collecting from both sources counts it twice."""
    for node in nodes:
        seen, unique = set(), []
        for event in node.get("amendment_events", []):
            key = (event.get("amending_act"), event.get("amending_section"))
            if key not in seen:
                seen.add(key)
                unique.append(event)
        if "amendment_events" in node:
            node["amendment_events"] = unique
        dedupe_events(node.get("children", []))


def apply_heading_overrides(nodes: list[dict], corrections: dict) -> None:
    """Replace a damaged heading, keeping the printed one as `heading_raw`."""
    for node in nodes:
        if node.get("type") == "section" and node.get("number") in corrections:
            fix = corrections[node["number"]]
            if node.get("heading") != fix["heading"]:
                node["heading_raw"] = node.get("heading", "")
                node["heading"] = fix["heading"]
                node["heading_correction_status"] = fix["status"]
                node["heading_correction_reason"] = fix.get("reason", "")
        apply_heading_overrides(node.get("children", []), corrections)


def apply_text_corrections(nodes: list[dict], corrections: list[dict], section: str = "") -> None:
    """A LankaLaw transcription slip verified against a second source (not a
    defect in the Act itself) is corrected in `text`; `raw_text` keeps the
    literal printed reading so the defect stays visible. The fix can land in
    any descendant of the named section, not only a node numbered like it."""
    by_section = collections.defaultdict(list)
    for fix in corrections:
        by_section[fix["section"]].append(fix)
    for node in nodes:
        here = node["number"] if node.get("type") == "section" else section
        for fix in by_section.get(here, []):
            if fix["find"] in node.get("text", ""):
                node["text"] = node["text"].replace(fix["find"], fix["replace"])
                node.setdefault("text_corrections", []).append(
                    {"find": fix["find"], "replace": fix["replace"], "reason": fix.get("reason", "")}
                )
        apply_text_corrections(node.get("children", []), corrections, here)


def source_location(page_text: str) -> dict[str, str]:
    match = SOURCE_LOCATION.search(page_text)
    if not match:
        return {}
    return {"chapter": match.group(1), "volume": match.group(2), "page": match.group(3)}


def quality_flags(page_text: str) -> list[dict]:
    flags = []
    for token in SUSPECT_TOKENS:
        count = page_text.count(token)
        if count:
            flags.append(
                {
                    "kind": "suspected-extraction-damage",
                    "token": token.strip() or "replacement-character",
                    "count": count,
                }
            )
    return flags


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    registry = read_csv(REGISTRY)
    lookup = {
        (int(r["act_or_ordinance_no"]), int(r["year"])): r
        for r in registry
        if r["act_or_ordinance_no"].isdigit() and r["year"].isdigit() and r["year"] != "0"
    }
    commencement = {r["source_id"]: r["commencement"] for r in read_csv(COMMENCEMENT)}
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    # A LankaLaw id ending in "A" is a standalone Act as enacted; one ending in
    # "C" is a chapter of a revised, consolidated edition.
    source_urls = {r["source_id"]: r["url"] for r in read_csv(MATCHES)} if MATCHES.exists() else {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written, totals = 0, collections.Counter()
    for file in sorted(HTML_DIR.glob("*.html")):
        match = FILE_NUMBER_YEAR.match(file.stem)
        if not match:
            continue
        key = (int(match.group(1)), int(match.group(2)))
        row = lookup.get(key)
        if not row or (args.source_id and row["source_id"] != args.source_id):
            continue

        page = file.read_text(encoding="utf-8", errors="replace")
        body, chain, long_title, editorial = parse(page, row["official_title"])
        if not body:
            continue

        chain_amendments = [
            {"type": k, "number": n, "year": y} for k, n, y in chain if (n, y) != key
        ]
        override = overrides.get(row["source_id"], {})
        dedupe_events(body)
        apply_heading_overrides(body, override.get("section_headings", {}))
        apply_text_corrections(body, override.get("text_corrections", []))
        stated = re.search(r"\[\s*([0-9]{1,2}\s*\w{0,4}\s+\w+\s*,?\s*[0-9]{4})\s*\]", text_of(page))
        # text_of() replaces every tag with a space and collapses whitespace to
        # one space rather than none, so a date's ordinal suffix marked up as
        # "1<sup>st</sup> July" comes out "1 st July", and a line break before
        # the trailing comma comes out "July , 1902" -- both belong to the
        # markup, not to the date as printed.
        date_stated = ""
        if stated:
            date_stated = re.sub(
                r"^(\d{1,2})\s+(st|nd|rd|th)\b", r"\1\2", stated.group(1).strip(), flags=re.IGNORECASE
            )
            date_stated = re.sub(r"\s+,", ",", date_stated)
        document = {
            "source_id": row["source_id"],
            "title": row["official_title"],
            "long_title": override.get("long_title", long_title),
            "long_title_raw": long_title if override.get("long_title") else "",
            "long_title_correction_status": override.get("long_title_status", ""),
            "citation": {
                # A standalone Act has no chain block to read the word "Act"
                # from, so the registry supplies it.
                "type": next(
                    (k for k, n, y in chain if (n, y) == key),
                    "Act" if row["source_type"] == "statute" and key[1] >= 1948 else "",
                ),
                "number": key[0],
                "year": key[1],
            },
            # The page prints a date without calling it a commencement. The
            # commencement below comes from statute_commencement.csv, a different
            # source, so the two are recorded separately rather than merged.
            "date_stated_in_source": date_stated,
            "commencement": commencement.get(row["source_id"], "") or None,
            "commencement_source": "statute_commencement.csv (srilankalaw)"
            if commencement.get(row["source_id"])
            else "",
            "language": "en",
            "edition": {
                "publisher": "lankalaw",
                # A page whose id ends in "A" is a standalone Act as enacted, not
                # a consolidated chapter of the revised edition.
                "kind": "original_or_unconfirmed_consolidation"
                if re.search(r"\d{4}Y0V0C\d+A", source_urls.get(row["source_id"], ""))
                else "consolidated",
                "source_url": source_urls.get(row["source_id"], ""),
                "local_path": file.relative_to(REPO_ROOT).as_posix(),
                "caveat": "private republisher, not the Government Printer",
            },
            "amendments": chain_amendments,
            "verification_status": override.get("verification_status", "unverified"),
            # Structure can be right while content is still missing.
            "content_completeness": override.get("content_completeness", ""),
            "amendment_history_status": (
                "listed_in_source_header" if chain_amendments else "none_listed_in_source_header"
            ),
            # The same note is printed against each provision it qualifies, so
            # the document-level list keeps one of each.
            "editorial_notes": list(
                {(n["text"], n["anchor_text"]): n for n in editorial}.values()
            ),
            "omitted_provisions": override.get("omitted_provisions", []),
            "overrides_applied": (
                {"checked_against": override["checked_against"], "note": override.get("note", "")}
                if override
                else {}
            ),
            "quality_flags": quality_flags(text_of(page)) + override.get("quality_notes", []),
            "source_location": source_location(text_of(page)) or override.get("source_location", {}),
            "alternate_edition_variants": override.get("alternate_edition_variants", []),
            # Schedules are referenced in the text but their bodies are not on
            # these pages, so they are recorded as references, not as content.
            # A body can only get here from an override, which means it was read
            # off a different edition; each entry says which one, so a schedule
            # recovered elsewhere is never mistaken for one this page carried.
            "schedules_referenced": sorted(
                {re.sub(r"\s+", " ", m.group(1)) for m in SCHEDULE_REF.finditer(text_of(page))}
            ),
            "schedules": override.get("schedules", []),
            "body": body,
        }

        target = OUT_DIR / f"{row['source_id']}-{key[0]}-{key[1]}.json"
        target.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

        def walk(nodes):
            for node in nodes:
                totals[node["type"]] += 1
                totals["amendment_events"] += len(node.get("amendment_events", []))
                totals["cross_references"] += len(node.get("cross_references", []))
                walk(node.get("children", []))

        walk(body)

        if args.show:
            print(f"=== {row['source_id']} {row['official_title']} ===")
            print(f"  long title: {long_title[:78]}")
            print(f"  amendments: {', '.join(f'{k} {n} of {y}' for k, n, y in chain if (n, y) != key)}")
            print(f"  quality flags: {document['quality_flags'] or 'none'}")
            for node in body[:4]:
                print(f"  s.{node['number']:<4} {node['heading'][:48]:50} children={len(node.get('children', []))}")
            defs = [d for n in body for d in n.get("children", []) if d["type"] == "definition"]
            print(f"  definitions: {len(defs)}")
            for d in defs[:6]:
                print(f"    {d['term'][:34]:36} {d['text'][:52]}")

    if args.source_id:
        return 0
    print(f"wrote {written} documents to {OUT_DIR.relative_to(REPO_ROOT)}")
    for key in ("section", "definition", "subsection", "paragraph", "subparagraph", "text"):
        print(f"  {key:14} {totals[key]}")
    print(f"  amendment events {totals['amendment_events']}")
    print(f"  cross references {totals['cross_references']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
