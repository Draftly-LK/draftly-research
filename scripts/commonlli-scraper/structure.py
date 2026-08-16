"""Segment a CommonLII judgment into its real parts.

`parse_case.py` reduces the page to a list of paragraphs. This module decides
what each paragraph *is*, because a legal corpus needs to know whose words it is
holding.

An NLR report runs in a fixed order, and the landmarks below were read off the
archived LKSC 1906 pages rather than assumed:

    142                                   printed page number
    Present : Mr. Justice Wendt.          the panel
    <CAPS party line>                     the parties
    Quo warranto-Jurisdiction-...         reporter's catchwords
    Held , by WENDT, J.-                  reporter's headnote
    The facts are fully set out in ...    reporter's note
    W. Pereira, K.C., for the petitioner. counsel
    Cur. adv. vult.                       argument closes
    12th February, 1906. WENDT J.-        <- an opinion starts here
    ...                                   the judge's own words
    MIDDLETON J,-                         <- a second opinion
    WOOD RENTON J.-                       <- a third

Two things that a first pass gets wrong, both fixed here:

* opinions usually open with the delivery date in front of the judge's name, so
  an `^JUDGE J.-` pattern matches none of them;
* a case can carry several opinions, so capturing one loses the rest and can
  attribute the whole judgment to the last judge on the page.

Everything above the first opinion is the *reporter's* work; from there down it
is the *court's*. That boundary matters: NLR/SLR headnotes are Council of Law
Reporting copyright, while judgment text is public record, and only the court's
words can carry a ratio.
"""

from __future__ import annotations

import re

# Structural markers are always short lines. Running these patterns over a full
# paragraph of prose is both wrong and slow.
MARKER_MAX_CHARS = 140

PAGE_NO = re.compile(r"^\d{1,4}$")

# "23rd March, 1906. WOOD RENTON J.-" / "MIDDLETON J,-" / "LASCELLES A.C.J.-"
# The date prefix is optional; the judge's name is set in capitals.
OPINION_START = re.compile(
    r"^(?:(?P<date>\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+,?\s+\d{4})\s*[.,]\s*)?"
    r"(?P<judge>[A-Z][A-Z'\-]*(?:\s+[A-Z][A-Z'\-]*){0,3})\s*[.,]?\s*"
    r"(?P<rank>A\.\s*C\.\s*J|C\.\s*J|A\.C\.J|C\.J|JJ|J)"
    r"\s*[.,]{0,2}\s*[-–—:]+\s*$")

# The reporter's statement of the rule opens either way:
#   "Held , by WENDT, J.-"      "Per Moncreiff, J,-Section 440 ..."
HELD = re.compile(r"^(?:Held\b|Per\s+[A-Z][A-Za-z'\-]+)", re.I)
# "Present : Mr. Justice Wendt." lists the panel.
PRESENT = re.compile(r"^Present\s*:\s*(?P<panel>.+?)\s*$", re.I)
JUSTICE = re.compile(r"(?:Mr\.\s*)?Justice\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})")
# Argument closes; the court reserves judgment.
CUR_ADV_VULT = re.compile(r"^Cur\.?\s*adv\.?\s*vult", re.I)
# "The facts are fully set out in the judgment of Wood Renton J."
FACTS_NOTE = re.compile(r"^The facts (?:are|appear)", re.I)

# "D. C, Jaffna, 20,463." / "P. C. Ratnapura, 20,026."
REGISTRY = re.compile(
    r"^(?P<court>[A-Z]\.\s*[A-Z]\.?)\s*,?\s*"
    r"(?P<place>[A-Z][A-Za-z\s'\-]{2,30}?)\s*,\s*"
    r"(?P<number>[\d,]{3,12})\s*\.?$")

# "W. Pereira, K.C. (A. St. V. Jayewardene with him), for applicant."
# Several counsel can share one paragraph, so this is used with finditer.
COUNSEL_ENTRY = re.compile(
    r",\s*for\s+(?:the\s+)?(?P<party>[A-Za-z][A-Za-z\s\-']{2,40}?)\s*(?=[.;]|$)")

CITED_CASE = re.compile(
    r"([A-Z][A-Za-z'\.]{1,20}(?:\s+[A-Z][A-Za-z'\.]{1,20}){0,3}"
    r"\s+v\.?\s+"
    r"[A-Z][A-Za-z'\.]{1,20}(?:\s+[A-Z][A-Za-z'\.]{1,20}){0,3})"
    r"\s*,?\s*\(?(\d{1,3}\s*(?:N\.\s*L\.\s*R\.|NLR|S\.\s*L\.\s*R\.|SLR)\s*\.?\s*\d{1,4})")

# "Reg. v. Cousins (1) followed" -- a case reference whose citation sits in a
# footnote. Bounded on both sides so it does not swallow surrounding prose.
CASE_NAME_ONLY = re.compile(
    r"\b([A-Z][A-Za-z'\.]{1,18}(?:\s+[A-Z][A-Za-z'\.]{1,18}){0,2}"
    r"\s+v\.\s+"
    r"[A-Z][A-Za-z'\.]{1,18}(?:\s+[A-Z][A-Za-z'\.]{1,18}){0,2})\b")

CATCHWORD_SPLIT = re.compile(r"\s*[-–—]\s*")
PARTY_LINE = re.compile(r"\bv\.?\b", re.I)


def looks_like_catchwords(text: str) -> bool:
    """Reporter catchwords: several dash-separated topics, not a sentence."""
    if len(text) > 500:
        return False
    parts = [p for p in CATCHWORD_SPLIT.split(text) if len(p.strip(" .,")) > 2]
    return len(parts) >= 3


# Silk and office suffixes, and the "(X with him)" junior parenthetical, are not
# part of an advocate's name.
NAME_NOISE = re.compile(
    r"\s*\(?\s*(?:with\s+him|with\s+her)\s*\)?|"
    r"\s*,?\s*(?:[KQ]\.?\s*C\.?|S\.?\s*-?\s*G\.?|A\.?\s*-?\s*G\.?|"
    r"Solicitor[- ]General|Attorney[- ]General)\s*\.?", re.I)


def clean_name(raw: str) -> str:
    name = NAME_NOISE.sub("", raw)
    name = re.sub(r"[()]", " ", name)
    return re.sub(r"\s+", " ", name).strip(" .,;-")


def parse_counsel(text: str) -> list[dict]:
    """Counsel appearances in one paragraph; several may share a line."""
    out = []
    for m in COUNSEL_ENTRY.finditer(text):
        party = re.sub(r"\s+", " ", m.group("party")).strip(" .,")
        # the advocate's name runs back to the previous sentence boundary
        before = text[:m.start()]
        seg = re.split(r"(?<=[.;])\s+", before)[-1]
        # a junior is named inside brackets; the leader is the text before them
        name = clean_name(re.split(r"\(", seg)[0] or seg)
        if name and 1 < len(name) < 60:
            out.append({"name": name, "role": f"for {party.lower()}"})
    return out


def segment(paragraphs: list[str]) -> dict:
    """Split paragraphs into reporter matter and each judge's own opinion."""
    pages: list[dict] = []
    body: list[str] = []
    for p in paragraphs:
        t = p.strip()
        if PAGE_NO.match(t):
            pages.append({"page": t, "at_paragraph": len(body)})
            continue
        if t:
            body.append(t)

    party_line = registry = None
    panel: list[str] = []
    catchwords: list[str] = []
    counsel: list[dict] = []
    held_at: int | None = None
    facts_at: int | None = None
    closed_at: int | None = None          # Cur. adv. vult.
    counsel_at: int | None = None         # first appearance line
    quote_at: int | None = None           # first block of quoted material
    opinions: list[dict] = []             # {judge, rank, date, at}

    for i, t in enumerate(body):
        short = len(t) <= MARKER_MAX_CHARS

        if short:
            m = OPINION_START.match(t)
            if m and not HELD.match(t):
                rank = re.sub(r"[\s.]", "", m.group("rank")).upper()
                opinions.append({
                    "judge": f"{m.group('judge').strip().rstrip(',')} {rank}",
                    "rank": rank,
                    "delivered": m.group("date"),
                    "at": i,
                })
                continue
            if CUR_ADV_VULT.match(t) and closed_at is None:
                closed_at = i
                continue
            if FACTS_NOTE.match(t) and facts_at is None:
                facts_at = i
            pm = PRESENT.match(t)
            if pm and not panel:
                panel = [j.strip() for j in JUSTICE.findall(pm.group("panel"))]
                continue
            if registry is None:
                rm = REGISTRY.match(t)
                if rm:
                    registry = {
                        "court": re.sub(r"\s+", " ", rm.group("court")).strip(),
                        "place": rm.group("place").strip(),
                        "number": rm.group("number").strip()}
                    continue

        if held_at is None and HELD.match(t):
            held_at = i
        if not catchwords and looks_like_catchwords(t) and i < 12:
            catchwords = [c.strip(" .,") for c in CATCHWORD_SPLIT.split(t)
                          if len(c.strip(" .,")) > 2]
            continue
        if party_line is None and i < 4 and PARTY_LINE.search(t) and len(t) < 200:
            party_line = t
        if quote_at is None and t[:1] in ('"', "“"):
            quote_at = i
        found = parse_counsel(t) if len(t) < 400 else []
        if found and counsel_at is None:
            counsel_at = i
        counsel.extend(found)

    # --- boundaries ---------------------------------------------------------
    first_opinion = opinions[0]["at"] if opinions else None
    # Reporter matter ends at the first of: the first opinion, Cur. adv. vult.
    reporter_end = min([x for x in (first_opinion, closed_at) if x is not None],
                       default=len(body))

    # The headnote is the reporter's short statement of the rule -- a few
    # paragraphs, not the whole front matter. In these writ cases the petition is
    # recited at length between the headnote and the opinions, so the stop has to
    # be the *earliest* of every following landmark, not just the first opinion.
    landmarks = {"facts-note": facts_at, "counsel": counsel_at,
                 "quoted-material": quote_at, "opinion-or-close": reporter_end}
    head_stop = min([x for x in landmarks.values() if x is not None],
                    default=reporter_end)
    bounded_by = next((k for k, v in landmarks.items() if v == head_stop), None)
    headnote_paras = (body[held_at:head_stop] if held_at is not None
                      and held_at < head_stop else [])

    # --- opinions -----------------------------------------------------------
    for n, op in enumerate(opinions):
        start = op["at"] + 1
        end = opinions[n + 1]["at"] if n + 1 < len(opinions) else len(body)
        op["paragraphs"] = body[start:end]
        op["text"] = "\n\n".join(op["paragraphs"])
    judgment_paras = body[first_opinion + 1:] if first_opinion is not None else []

    cited, seen = [], set()
    for t in body:
        for m in CITED_CASE.finditer(t):
            name = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
            key = name.lower()
            if key not in seen:
                seen.add(key)
                cited.append({"case": name,
                              "citation": re.sub(r"\s+", " ", m.group(2)).strip()})
    # These reports often carry the citation in a footnote and leave only a
    # marker in the text ("Reg. v. Cousins (1) followed"). Record the reference
    # with a null citation rather than dropping the edge entirely.
    for t in body:
        for m in CASE_NAME_ONLY.finditer(t):
            name = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
            # A trailing connective belongs to the sentence, not the case name
            # ("The Queen v. York. With" -> "The Queen v. York").
            name = re.sub(r"\.\s+(?:With|And|In|But|See|Cf)$", ".", name).strip(" ,.")
            # The report sets the parties of *this* case in capitals, so an
            # all-caps match is the case citing itself. The "v." separator stays
            # lower case, so test the party names without it.
            if re.sub(r"\bv\.?\b", "", name).isupper():
                continue
            key = name.lower()
            if key not in seen and len(name) > 6:
                seen.add(key)
                cited.append({"case": name, "citation": None})

    # de-duplicate counsel, keep order
    cseen, ded = set(), []
    for c in counsel:
        k = (c["name"].lower(), c["role"].lower())
        if k not in cseen:
            cseen.add(k)
            ded.append(c)

    # Not every report prints a "Present :" line; the judges who delivered
    # opinions are then the best available record of who sat. A panel taken from
    # the opinions is weaker evidence -- a judge who concurred without writing
    # leaves no trace -- so say which source it came from.
    panel_source = "present-line" if panel else None
    if not panel and opinions:
        panel = [o["judge"] for o in opinions]
        panel_source = "opinions"

    return {
        "party_line": party_line,
        "registry": registry,
        "panel": panel,
        "panel_source": panel_source,
        "catchwords": catchwords,
        "headnote": "\n\n".join(headnote_paras) if headnote_paras else None,
        # Which landmark closed the headnote, and whether it stayed a plausible
        # length. A reporter's headnote runs to a few hundred words; anything
        # much longer has probably swallowed the statement of facts and should
        # be checked before it is treated as the reporter's rule.
        "headnote_bounded_by": bounded_by if headnote_paras else None,
        "headnote_suspect": bool(headnote_paras)
                            and sum(len(p) for p in headnote_paras) > 2500,
        "counsel": ded,
        "argument_closed": closed_at is not None,
        "opinions": [{"judge": o["judge"], "delivered": o["delivered"],
                      "n_paragraphs": len(o["paragraphs"]), "text": o["text"]}
                     for o in opinions],
        "judgment_author": opinions[0]["judge"] if opinions else None,
        "judgment_paragraphs": judgment_paras,
        "judgment_text": "\n\n".join(judgment_paras),
        "has_judgment_boundary": first_opinion is not None,
        "printed_pages": pages,
        "cited_cases": cited,
    }
