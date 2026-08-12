"""Segment a CommonLII judgment into its real parts.

`parse_case.py` gets the page down to a list of paragraphs. This module does the
part that matters for a legal corpus: deciding what each paragraph *is*.

An NLR report page is laid out in a fixed order, and the HTML preserves the
typographic signals the flat text version destroys:

    <b>87</b>                    printed page number  -> page break
    <b>ACHCHI</b> v <b>AGO</b>   party line
    P. <i>C. Ratnapura, 20,026</i>   originating court + its case number
    <i>catchwords-topic-topic</i>    reporter's catchwords
    Per Moncreiff, J,-...            headnote (the reporter's statement of the rule)
    IN the course of the trial...    statement of facts
    Bawa, for appellants.-...        counsel submissions
    <b>MONCREIFF, J.--</b>           <- the judgment proper starts here
    ...                              the judge's own words

That last boundary is the important one. Everything above it is the *reporter's*
work; everything below is the *court's*. A rule quoted from the headnote and a
rule quoted from the judgment are different kinds of authority, and a corpus that
cannot tell them apart will attribute the editor's summary to the judge.

Page-number paragraphs are recorded rather than deleted, so extracted text can be
cited back to a printed page.
"""

from __future__ import annotations

import re

# `<b>87</b>` alone in a paragraph -- a printed page number, not prose.
PAGE_NO = re.compile(r"^\d{1,4}$")
# "P. C. Ratnapura, 20,026." / "D. C, Jaffna, 20,463." / "C. R. Colombo, 1234"
REGISTRY = re.compile(
    r"^(?P<court>[A-Z]\.\s*[A-Z]\.?|[A-Z]\.\s*[A-Z]\.\s*[A-Z]\.?)\s*,?\s*"
    r"(?P<place>[A-Z][A-Za-z\s'\-]{2,30}?)\s*,\s*"
    r"(?P<number>[\d,]{3,12})\s*\.?$")
# "MONCREIFF, J.--" / "Bonser, C.J.-" / "WITHERS, J. -"
# Case-sensitive and bounded on purpose. With re.I the [A-Z] classes match any
# letter, so the judge-name group can swallow a whole paragraph and the repeated
# group backtracks catastrophically; MARKER_MAX_CHARS below is the second guard.
JUDGMENT_START = re.compile(
    r"^(?P<judge>[A-Z][A-Za-z'\-]+(?:\s*,?\s*[A-Z][A-Za-z'\-]+){0,3})\s*,?\s*"
    r"(?P<rank>A\.?\s*C\.?\s*J|C\.?\s*J|JJ?)\s*\.{0,2}\s*[-–—]{1,3}\s*$")

# Structural markers are always short lines. Never run the marker patterns over
# a full paragraph of prose -- it is both wrong and slow.
MARKER_MAX_CHARS = 120
# "Bawa, for appellants.-" / "Van Langenberg, for the respondent -"
COUNSEL = re.compile(
    r"^(?P<name>[A-Z][A-Za-z'\.\s\-]{1,40}?)\s*,?\s*"
    r"for\s+(?:the\s+)?(?P<party>appellants?|respondents?|plaintiffs?|"
    r"defendants?|petitioners?|accused|complainant)", re.I)
# "Per Moncreiff, J,-" opening a reporter's headnote
HEADNOTE_LEAD = re.compile(r"^(?:Per\s+[A-Z][A-Za-z'\-]+|Held)\b", re.I)
# A catchword line: dash-separated topics, no sentence-final punctuation.
CATCHWORD_SPLIT = re.compile(r"\s*[-–—]\s*")
# Case citations inside the text: "Andris v. Juanis, 2 N. L. R. 74"
CITED_CASE = re.compile(
    r"([A-Z][A-Za-z'\.\s]{2,40}?\s+v\.?\s+[A-Z][A-Za-z'\.\s]{2,40}?)\s*,\s*"
    r"(\d{1,3}\s*(?:N\.\s*L\.\s*R\.|NLR|S\.\s*L\.\s*R\.|SLR)\s*\.?\s*\d{1,4})")
PARTY_LINE = re.compile(r"\bv\.?\b", re.I)


def looks_like_catchwords(text: str) -> bool:
    """Reporter catchwords: several dash-separated topics, not a sentence."""
    parts = [p for p in CATCHWORD_SPLIT.split(text) if p.strip()]
    if len(parts) < 2 or len(text) > 400:
        return False
    # a real sentence usually ends in a full stop and contains a finite verb;
    # catchword lists rarely do either
    return not re.search(r"\.\s*$", text) or len(parts) >= 3


def segment(paragraphs: list[str]) -> dict:
    """Split judgment paragraphs into reporter matter and the court's words."""
    pages: list[dict] = []
    body: list[str] = []          # paragraphs with page numbers removed
    current_page: str | None = None

    for p in paragraphs:
        t = p.strip()
        if PAGE_NO.match(t):
            current_page = t
            pages.append({"page": t, "at_paragraph": len(body)})
            continue
        body.append(t)

    party_line = registry = None
    catchwords: list[str] = []
    judgment_at: int | None = None
    judge = None
    counsel: list[dict] = []

    for i, t in enumerate(body):
        short = len(t) <= MARKER_MAX_CHARS
        if short and judgment_at is None:
            m = JUDGMENT_START.match(t)
            if m:
                judgment_at = i
                rank = re.sub(r"[\s.]", "", m.group("rank")).upper()
                judge = f"{m.group('judge').strip().rstrip(',')} {rank}"
                continue
        m = COUNSEL.match(t[:MARKER_MAX_CHARS])
        if m and (judgment_at is None or i < judgment_at):
            counsel.append({"name": m.group("name").strip().rstrip(","),
                            "role": f"for {m.group('party').lower()}"})
        if short and registry is None:
            rm = REGISTRY.match(t)
            if rm:
                registry = {"court": re.sub(r"\s+", " ", rm.group("court")).strip(),
                            "place": rm.group("place").strip(),
                            "number": rm.group("number").strip()}
                continue
        if party_line is None and i < 3 and PARTY_LINE.search(t) and len(t) < 160:
            party_line = t
            continue
        if not catchwords and looks_like_catchwords(t) and (
                judgment_at is None or i < judgment_at):
            catchwords = [c.strip(" .,") for c in CATCHWORD_SPLIT.split(t)
                          if c.strip(" .,")]

    # reporter matter above the judgment marker; the court's words below
    head = body[:judgment_at] if judgment_at is not None else body
    judgment = body[judgment_at + 1:] if judgment_at is not None else []

    headnote = [t for t in head
                if HEADNOTE_LEAD.match(t)
                or (catchwords and t not in (party_line,) and len(t) > 80
                    and not COUNSEL.match(t) and not looks_like_catchwords(t))]
    # facts and submissions are the remainder of the reporter's matter
    submissions = [t for t in head if COUNSEL.match(t)]

    cited, seen = [], set()
    for t in body:
        for m in CITED_CASE.finditer(t):
            name = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
            cite = re.sub(r"\s+", " ", m.group(2)).strip()
            key = name.lower()
            if key not in seen:
                seen.add(key)
                cited.append({"case": name, "citation": cite})

    return {
        "party_line": party_line,
        "registry": registry,
        "catchwords": catchwords,
        "headnote": "\n\n".join(headnote) if headnote else None,
        "counsel": counsel,
        "submissions": submissions,
        "judgment_author": judge,
        "judgment_paragraphs": judgment,
        "judgment_text": "\n\n".join(judgment),
        "has_judgment_boundary": judgment_at is not None,
        "printed_pages": pages,
        "cited_cases": cited,
    }
