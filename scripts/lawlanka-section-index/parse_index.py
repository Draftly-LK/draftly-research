"""Parse LawLanka structural pages.

Two things are taken, and only these two:

- the **section list** with its marginal-note heading, from a
  `consShortTitleView` index page;
- the inline **amendment markers** `[n, Act of Year]` that the index prints
  after a heading, plus the amending-instrument list in the document header.

The consolidated body prose is not read and not stored. `consSelectedSection` is
never fetched -- it returns the whole Act on every call.

A heading such as

    s.756  Security to be by bond and with surety. [50, 79 of 1980] [50, 79 of 1988]

yields heading "Security to be by bond and with surety." and two markers, each
naming the amending section and the amending Act.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

# `[50, 79 of 1980]` -> amending section 50 of Act 79 of 1980.
MARKER_RE = re.compile(r"\[\s*(\d+[A-Za-z]?)\s*,\s*([^\]]+?)\s*\]")
# An amending instrument as the document header writes it: "No. 79 of 1980",
# "Ordinance No. 2 of 1889", "43 of 2024".
INSTRUMENT_RE = re.compile(
    r"((?:(?:Act|Ordinance|Law)\s+)?No\.?\s*\d+\s+of\s+\d{4}|\b\d+\s+of\s+\d{4})",
    re.I)
SECTION_LINK_RE = re.compile(r"consSelectedSection", re.I)
# Leading "s.4", "4.", "Section 4" on a heading line.
LEAD_SECTION_RE = re.compile(r"^\s*(?:s(?:ec(?:tion)?)?\.?\s*)?(\d+[A-Za-z]?)\s*[.\-:)]?\s+",
                             re.I)


def _sectionno(href: str) -> str:
    q = parse_qs(urlparse(href).query)
    for key in ("sectionno", "sectionNo", "secno", "section"):
        if key in q and q[key] and q[key][0].strip():
            return q[key][0].strip()
    return ""


def _chapterid(href: str) -> str:
    q = parse_qs(urlparse(href).query)
    for key in ("chapterid", "chapterId", "chapid"):
        if key in q and q[key]:
            return q[key][0].strip()
    return ""


def split_markers(text: str) -> tuple[str, list[dict]]:
    """Separate a heading from its trailing amendment markers."""
    markers = []
    for m in MARKER_RE.finditer(text):
        markers.append({"amending_section": m.group(1).strip(),
                        "amending_act": re.sub(r"\s+", " ", m.group(2)).strip(),
                        "verbatim": m.group(0)})
    heading = MARKER_RE.sub("", text)
    heading = re.sub(r"\s+", " ", heading).strip(" .,;:-–—")
    return heading, markers


def _row_text(anchor) -> str:
    """Heading text for an anchor, widening to the containing row if needed."""
    own = anchor.get_text(" ", strip=True)
    # If the anchor is just the number ("4", "s.4"), the heading sits beside it.
    if len(own) <= 12 and re.fullmatch(r"(?:s(?:ec(?:tion)?)?\.?\s*)?\d+[A-Za-z]?\.?",
                                      own, re.I):
        # Widen outwards. The row is checked before the cell: the nearest <td>
        # holds only the number, and the heading is in the cell beside it.
        for tag in ("tr", "li", "p", "div", "td"):
            holder = anchor.find_parent(tag)
            if holder is None:
                continue
            wider = holder.get_text(" ", strip=True)
            if len(wider) > len(own):
                return wider
    return own


def parse_section_index(html: str) -> list[dict]:
    """Every section the index page lists, in page order, de-duplicated.

    The section number comes from the link's `sectionno` query parameter, which
    is authoritative -- the printed label is sometimes missing or misprinted.
    """
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not SECTION_LINK_RE.search(href):
            continue
        sec = _sectionno(href)
        if not sec:
            continue
        raw = _row_text(a)
        heading, markers = split_markers(raw)
        # drop a leading section label the heading may repeat
        heading = LEAD_SECTION_RE.sub("", heading, count=1).strip()
        key = f"{sec}|{heading[:40]}"
        if key in seen:
            continue
        seen.add(key)
        out.append({"section": sec, "heading": heading, "markers": markers,
                    "href": href, "chapterid": _chapterid(href),
                    "raw": re.sub(r"\s+", " ", raw).strip()})
    return out


def parse_amending_instruments(html: str) -> list[str]:
    """The amending-instrument list printed in the document header.

    The header sits above the section list, so only text before the first
    section link is considered -- otherwise every `[n, Act of Year]` marker in
    the body would be counted as a header entry.
    """
    soup = BeautifulSoup(html, "html.parser")
    first = soup.find("a", href=SECTION_LINK_RE)
    if first is not None:
        for el in list(first.find_all_next()):
            el.extract()
    head = soup.get_text(" ", strip=True)
    found, seen = [], set()
    for m in INSTRUMENT_RE.finditer(head):
        s = re.sub(r"\s+", " ", m.group(1)).strip()
        norm = re.sub(r"^(?:act|ordinance|law)\s+", "", s, flags=re.I)
        norm = re.sub(r"^no\.?\s*", "", norm, flags=re.I).lower()
        if norm in seen:
            continue
        seen.add(norm)
        found.append(s)
    return found


def parse_consolidation_index(html: str) -> list[dict]:
    """Statute name -> act code, from one letter of the A-Z consolidation index."""
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # `consShortTitleView` on the consolidation index,
        # `revised1981ShortTitleView` on the 1981 revised index.
        if "shorttitleview" not in href.lower():
            continue
        name = a.get_text(" ", strip=True)
        if not name:
            continue
        q = parse_qs(urlparse(href).query)
        code = ""
        for key in ("selectedAct", "actcode", "actCode", "chapterid",
                    "chapterId", "id"):
            if key in q and q[key]:
                code = q[key][0].strip()
                break
        key2 = (name.lower(), code)
        if key2 in seen:
            continue
        seen.add(key2)
        out.append({"statute_name": name, "act_code": code, "href": href})
    return out


def summarise(sections: list[dict]) -> dict:
    numeric = []
    for s in sections:
        m = re.match(r"(\d+)", s["section"])
        if m:
            numeric.append(int(m.group(1)))
    with_heading = sum(1 for s in sections if len(s["heading"]) > 3)
    n_markers = sum(len(s["markers"]) for s in sections)
    return {
        "n_sections": len(sections),
        "n_distinct": len({s["section"] for s in sections}),
        "highest_section": max(numeric) if numeric else 0,
        "with_heading": with_heading,
        "headings_missing": len(sections) - with_heading,
        "n_amendment_markers": n_markers,
        "sections_with_markers": sum(1 for s in sections if s["markers"]),
    }
