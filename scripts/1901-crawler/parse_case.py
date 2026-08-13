"""Parse a CommonLII judgment page into a structured record.

These pages are 1990s-era static HTML with no semantic container -- no
`<main id="judgment">`. The boundaries are positional:

    <h1>court</h1>
    breadcrumb / neutral citation
    <h2>case name</h2>
    <p>...judgment...</p>
    <hr>            <- judgment ends
    site footer

So the parser anchors on the first <h2>, walks forward collecting <p>, and stops
at the first <hr>. lxml is used rather than html.parser because these pages carry
genuinely malformed constructs (unclosed and criss-crossed <b>/<i>/<p>) that the
stdlib parser recovers from badly.

Extraction is source-faithful. Page numbers, reporter headers and OCR noise are
kept here and removed in a separate derived stage -- never silently correct legal
text without retaining the original.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

import structure

# --- citation patterns -------------------------------------------------------
# Report citations as the old reports write them: (1901) 5 NLR 87, [1995] 1 SLR 261.
REPORT_CITE = re.compile(
    r"[\(\[]?\d{4}[\)\]]?\s*\(?\d{0,2}\)?\s*"
    r"(?:NLR|N\.L\.R\.|SLR|S\.L\.R\.|Sri\s?L\.?\s?R\.?|CLW|C\.L\.W\.|CWR|Bal\.?\s?Rep)"
    r"\s*\.?\s*\d+", re.I)
NEUTRAL_CITE = re.compile(r"\[\d{4}\]\s*LK[A-Z]{2}\s*\d+", re.I)
# "section 440 of the Criminal Procedure Code"
LEGISLATION = re.compile(
    r"(?:[Ss]ection|[Ss]ec\.?|[Ss]\.)\s*(\d+[A-Za-z]?)\s+of\s+the\s+"
    r"([A-Z][A-Za-z0-9 ,'()\-]{3,60}?(?:Act|Ordinance|Code|Law))")
# "Moncreiff J.", "Bonser C.J.", "Withers, J."
JUDGE = re.compile(
    r"\b([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})\s*,?\s*"
    r"(C\.?\s?J\.?|A\.?\s?C\.?\s?J\.?|J{1,2}\.?)(?=\s|$|[.,\-])")
PATH_RE = re.compile(
    r"/cases/(?P<database>[^/]+)/(?P<year>\d{4})/(?P<number>\d+)\.html?$", re.I)
DOWNLOAD_PATH_RE = re.compile(
    r"/cases/(?P<database>[^/]+)/(?P<year>\d{4})/(?P<number>\d+)"
    r"\.(?P<file_type>html?|pdf)$", re.I)

# CommonLII leaves two machine-readable HTML comments under the <h2>. They are
# the cleanest metadata on the page and the flat-text corpus dropped both.
#   <!--sino date 1 January 1901-->
#   <!--make_docs: source=.../eng/NLR5V87.htm-->
SINO_DATE = re.compile(r"<!--\s*sino\s+date\s+(.+?)\s*-->", re.I | re.S)
MAKE_DOCS = re.compile(r"<!--\s*make_docs:\s*source=(.+?)\s*-->", re.I | re.S)
# NLR5V87 -> New Law Reports volume 5, page 87
NLR_REF = re.compile(r"NLR(\d{1,3})V(\d{1,4})", re.I)
MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}


def iso_date(raw: str) -> str | None:
    """'1 January 1901' -> '1901-01-01'."""
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw.strip())
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def report_provenance(source_path: str) -> dict:
    """Recover the printed report reference from the make_docs source path."""
    out: dict = {"build_source": source_path}
    m = NLR_REF.search(source_path)
    if m:
        out.update({"report_series": "NLR", "report_volume": int(m.group(1)),
                    "report_page": int(m.group(2))})
    return out

TITLE_REPORT = re.compile(
    r"-\s*(?P<series>NLR|SLR|Sri\s?LR)\s*-\s*(?P<page>\d{1,4})\s+of\s+(?P<volume>\d{1,3})",
    re.I)
TITLE_CITE = re.compile(
    r"\((?P<year>\d{4})\)\s*(?P<volume>\d{1,3})\s*(?P<series>NLR|SLR|Sri\s?LR)"
    r"\s*(?P<page>\d{1,4})", re.I)
TITLE_DATE = re.compile(r"\((\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\)")


def report_from_title(title: str) -> dict:
    """Printed-report reference parsed out of the page title."""
    m = TITLE_REPORT.search(title) or TITLE_CITE.search(title)
    if not m:
        return {}
    g = m.groupdict()
    series = re.sub(r"\s+", "", g["series"]).upper()
    return {"report_series": "SLR" if series.startswith("SRI") else series,
            "report_volume": int(g["volume"]), "report_page": int(g["page"])}


def case_name_from_title(title: str) -> str:
    """The party names, with the citation tail trimmed off."""
    return re.split(r"\s+-\s+(?:NLR|SLR|Sri\s?LR)\s+-\s+", title, maxsplit=1,
                    flags=re.I)[0].strip(" .,-")


def clean_text(node) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def identity_from_url(url: str) -> dict:
    m = PATH_RE.search(urlparse(url).path)
    if not m:
        return {}
    d = m.groupdict()
    return {"database": d["database"].upper(), "year": int(d["year"]),
            "case_number": d["number"],
            "case_id": f"{d['database'].upper()}-{d['year']}-{d['number']}"}


def extract_paragraphs(title_node) -> list[str]:
    """Judgment paragraphs between the case heading and the closing rule."""
    out: list[str] = []
    for node in title_node.find_all_next(["p", "hr"]):
        if node.name == "hr":
            break
        # malformed nesting produces <p> inside <p>; keep only the outermost
        if node.find_parent("p") is not None:
            continue
        text = clean_text(node)
        if text:
            out.append(text)
    return out


def parse_case(html: str, url: str, *, retrieved_at: str = "") -> dict:
    soup = BeautifulSoup(html, "lxml")

    title_node = soup.find("h2")
    if title_node is None:
        raise ValueError(f"no <h2> case heading found: {url}")
    court_node = soup.find("h1")

    paragraphs = extract_paragraphs(title_node)
    case_text = "\n\n".join(paragraphs)
    display_title = clean_text(title_node)

    # The breadcrumb above the heading carries the neutral citation.
    head_text = clean_text(soup) [:1200]
    neutral = NEUTRAL_CITE.search(head_text)

    reports, seen = [], set()
    for m in REPORT_CITE.finditer(f"{display_title} {case_text[:4000]}"):
        c = re.sub(r"\s+", " ", m.group(0)).strip()
        if c.lower() not in seen:
            seen.add(c.lower())
            reports.append(c)

    legislation, lseen = [], set()
    for m in LEGISLATION.finditer(case_text):
        title = re.sub(r"\s+", " ", m.group(2)).strip(" ,")
        key = (title.lower(), m.group(1))
        if key not in lseen:
            lseen.add(key)
            legislation.append({"title": title, "section": m.group(1)})
    # Counsel abbreviate ("the Procedure Code" for "the Criminal Procedure
    # Code"), which yields two edges to one enactment. Where one title is a
    # suffix of another at the same section, keep the fuller name.
    legislation = [
        a for a in legislation
        if not any(b is not a and b["section"] == a["section"]
                   and b["title"].lower().endswith(a["title"].lower())
                   and len(b["title"]) > len(a["title"])
                   for b in legislation)
    ]

    judges, jseen = [], set()
    for m in JUDGE.finditer(" ".join(paragraphs[:3]) if paragraphs else ""):
        name = re.sub(r"\s+", " ", f"{m.group(1)} {m.group(2)}").strip()
        if name.lower() not in jseen and len(m.group(1)) > 2:
            jseen.add(name.lower())
            judges.append(name)

    # metadata from the HTML comments, before BeautifulSoup discards them
    sino = SINO_DATE.search(html)
    docs = MAKE_DOCS.search(html)
    provenance = report_provenance(docs.group(1)) if docs else {}
    # Both comments are missing from many pages; the title line carries the same
    # date and report reference, so fall back to it rather than losing the field.
    if not provenance.get("report_series"):
        provenance = {**provenance, **report_from_title(display_title)}
    raw_date = sino.group(1).strip() if sino else None
    if not raw_date:
        tm = TITLE_DATE.search(display_title)
        raw_date = tm.group(1) if tm else None
    decision_date = iso_date(raw_date) if raw_date else None

    parts = structure.segment(paragraphs)

    ident = identity_from_url(url)
    return {
        **ident,
        "decision_date": decision_date,
        "decision_date_raw": raw_date,
        "date_source": ("sino-comment" if sino else
                        "title-line" if raw_date else None),
        **provenance,
        **parts,
        "court": clean_text(court_node) if court_node else None,
        "case_name": case_name_from_title(display_title),
        "page_title": display_title,
        "neutral_citation": neutral.group(0) if neutral else None,
        "report_citations": reports,
        "judges": judges[:6],
        "cited_legislation": legislation,
        "source_url": url,
        "retrieved_at": retrieved_at,
        "content_hash": "sha256:" + hashlib.sha256(
            case_text.encode("utf-8")).hexdigest(),
        "n_paragraphs": len(paragraphs),
        "n_chars": len(case_text),
        "paragraphs": paragraphs,
        "case_text": case_text,
        "status": "unverified",
    }


def extract_links(html: str, base_url: str) -> list[str]:
    """Judgment links on a year index. Crawl real hyperlinks, never guess
    /1.html, /2.html -- numbering is not contiguous across these databases."""
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, str(a["href"]))
        if PATH_RE.search(urlparse(href).path) and href not in seen:
            seen.add(href)
            out.append(href)
    return out


def extract_download_links(html: str, base_url: str) -> list[str]:
    """All downloadable judgments on an index, including later PDF records."""
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, str(a["href"]))
        if DOWNLOAD_PATH_RE.search(urlparse(href).path) and href not in seen:
            seen.add(href)
            out.append(href)
    return out
