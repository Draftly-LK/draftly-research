"""Harvest statute text as HTML from CommonLII's Sri Lankan Numbered Acts.

Why this database and not the other one
---------------------------------------
CommonLII carries two Sri Lanka legislation databases and only one of them has
HTML:

    lk/legis/consol_act   1980 Revised Edition, 516 documents, last updated
                          2005. Every document answers "There is no available
                          HTML version of this document." PDF and txt only.
    lk/legis/num_act      Sri Lankan Numbered Acts, 2054 documents, 1956-2006.
                          Full text as HTML, one page per section, free.

So `num_act` is the only free HTML source we have found for statute text. Both
LawLanka and srilankalaw.lk are Blackhall Publishing's *Laws of Sri Lanka* behind
the same subscription wall -- srilankalaw cut the National Housing Development
Authority Act at section 21 of 93, and the account in `.env` reports
"You are a Free/Promotional User" and cuts at section 2. Neither is usable
without a paid seat.

What this buys, and what it does not
------------------------------------
14 of the 44 statutes in `data/legal-sources/library/statutes/`. `num_act`
begins at 1956, so the pre-1956 Ordinances the conveyancing curriculum leans on
hardest -- Prevention of Frauds 1840, Notaries 1907, Powers of Attorney 1902,
Registration of Documents 1927, Wills 1844, Trusts 1917, Civil Procedure Code
1889 -- are not here at all. They exist in `consol_act` as Chapters, which is
PDF-only. Statutes after its 2006 cutoff (Companies Act 2007, Land
(Restrictions on Alienation) 2014, Revocation of Deeds of Gift 2017) are
likewise absent. Those stay recorded as holes; nothing is substituted for them.

The ACTS table below was built by matching the source registry on Act number AND
year AND a title-token overlap. Matching on title alone paired Land Reform Law
No. 1 of 1972 with the University of Ceylon Act No. 1 of 1972, so all three
tests are required and every row was eyeballed afterwards.

Provenance and terms
--------------------
CommonLII's robots.txt says `Allow: /` for a general agent, with
`Content-Signal: search=yes,ai-train=no,use=reference`. Reference corpus is
signalled as permitted; training a model on this text is not. Under
`data/legal-sources/conveyancing-source-checklist.md` CommonLII is a priority-3
consolidator, not the Government Printer, so everything here is
`status: unverified` and the official PDFs remain the text authority.

There is no whole-act URL -- `.txt` and `.rtf` both 403 -- so each section is a
separate request. Pages are cached under `tmp/`, so a re-run makes zero
requests.

    python scripts/harvest_commonlii_statutes.py --dry-run
    python scripts/harvest_commonlii_statutes.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.commonlii.org/lk/legis/num_act"
OUT_DIR = ROOT / "data/legal-sources/library/statutes/HTML"
MANIFEST = ROOT / "data/legal-sources/manifests/statute-html-commonlii.csv"
CACHE = ROOT / "tmp/commonlii-statutes-cache"
FETCH_LOG = CACHE / "fetch-log.csv"

# A browser UA is required: the honest research UA gets a Cloudflare 403 on this
# tree, the same mitigation documented in scripts/commonlii-scraper/fetch.py.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}
DELAY_S = 1.5
TIMEOUT_S = 45
MAX_RETRIES = 4
BACKOFF_MULT = 6      # extra patience once Cloudflare has thrown a 403/429
RETRIEVED_FROM = "commonlii/lk/legis/num_act"

# source_id, output slug, CommonLII act code, official title as we record it.
ACTS = [
    ("SRC011", "registration-of-title-act-21-1998", "rota21o1998290",
     "Registration of Title Act, No. 21 of 1998"),
    ("SRC012", "apartment-ownership-law-11-1973", "aoa11o1973284",
     "Apartment Ownership Law, No. 11 of 1973"),
    ("SRC023", "tea-and-rubber-estates-control-of-fragmentation-act-2-1958",
     "tareofa2o1958487",
     "Tea and Rubber Estates (Control of Fragmentation) Act, No. 2 of 1958"),
    ("SRC025", "wills-amendment-act-5-1993", "wa5o1993217",
     "Wills (Amendment) Act, No. 5 of 1993"),
    ("SRC027", "partition-law-21-1977", "pl21o1977192",
     "Partition Law, No. 21 of 1977"),
    ("SRC028", "rent-act-7-1972", "ra7o1972120",
     "Rent Act, No. 7 of 1972"),
    ("SRC034", "stamp-duty-act-43-1982", "sda43o1982197",
     "Stamp Duty Act, No. 43 of 1982"),
    ("SRC068", "stamp-duty-special-provisions-act-12-2006", "sdpa12o2006401",
     "Stamp Duty (Special Provisions) Act, No. 12 of 2006"),
    ("SRC043", "survey-act-17-2002", "sa17o2002171",
     "Survey Act, No. 17 of 2002"),
    ("SRC052", "land-grants-special-provisions-act-43-1979", "lgpa43o1979371",
     "Land Grants (Special Provisions) Act, No. 43 of 1979"),
    ("SRC062", "pradeshiya-sabhas-act-15-1987", "psa15o1987207",
     "Pradeshiya Sabhas Act, No. 15 of 1987"),
    ("SRC072", "nindagama-lands-act-30-1968", "nla30o1968167",
     "Nindagama Lands Act, No. 30 of 1968"),
    ("SRC073", "local-authorities-housing-act-14-1964", "laha14o1964325",
     "Local Authorities Housing Act, No. 14 of 1964"),
    ("SRC074", "state-mortgage-and-investment-bank-law-13-1975",
     "smaibl13o1975388",
     "State Mortgage and Investment Bank Law, No. 13 of 1975"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Fetcher:
    """One request per DELAY_S, cached to disk, every request logged.

    A cached URL is never re-fetched, so the run is resumable and re-running it
    costs nothing.
    """

    def __init__(self, *, delay_s: float = DELAY_S, offline: bool = False):
        self.delay_s = delay_s
        self.offline = offline
        self.requests_made = 0
        self.cache_hits = 0
        self._last = 0.0
        CACHE.mkdir(parents=True, exist_ok=True)

    def _path(self, url: str) -> Path:
        return CACHE / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html")

    def _log(self, url: str, status: object, nbytes: int, note: str = "") -> None:
        new = not FETCH_LOG.exists()
        with FETCH_LOG.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["url", "status", "bytes", "fetched_at", "note"])
            w.writerow([url, status, nbytes, utc_now(), note])

    def _wait(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.delay_s:
            time.sleep(self.delay_s - gap)
        self._last = time.monotonic()

    def get(self, url: str, *, note: str = "") -> str:
        cached = self._path(url)
        if cached.exists():
            self.cache_hits += 1
            return cached.read_text(encoding="utf-8", errors="replace")
        if self.offline:
            raise FileNotFoundError(f"offline and not cached: {url}")

        last: Exception | None = None
        throttled = False
        for attempt in range(1, MAX_RETRIES + 1):
            self._wait()
            try:
                with urllib.request.urlopen(
                        urllib.request.Request(url, headers=HEADERS),
                        timeout=TIMEOUT_S) as resp:
                    body = resp.read().decode("utf-8", "replace")
                    status = resp.status
            except urllib.error.HTTPError as e:
                self._log(url, e.code, 0, f"attempt {attempt}")
                if e.code == 404:
                    raise
                # 403 here is Cloudflare throttling a burst, not a standing
                # refusal: the same URL succeeds moments later. Back off hard
                # and retry rather than abandoning the act mid-way.
                throttled = throttled or e.code in (403, 429)
                last = e
            except Exception as e:  # noqa: BLE001
                self._log(url, type(e).__name__, 0, f"attempt {attempt}")
                last = e
            else:
                self.requests_made += 1
                cached.write_text(body, encoding="utf-8")
                self._log(url, status, len(body.encode("utf-8")), note)
                return body
            time.sleep(self.delay_s * (BACKOFF_MULT if throttled else 1)
                       * attempt)

        code = getattr(last, "code", None)
        if code in (401, 403, 429):
            raise RuntimeError(
                f"CommonLII returned HTTP {code} for {url} on all "
                f"{MAX_RETRIES} attempts. The mitigation on this tree may have "
                f"tightened, or this IP is rate-limited. Raise --delay and "
                f"retry; cached pages are kept, so the run resumes where it "
                f"stopped.")
        raise RuntimeError(f"giving up on {url}: {last}")

    def summary(self) -> str:
        return f"{self.requests_made} fetched, {self.cache_hits} from cache"


# --- parsing ---------------------------------------------------------------
#
# A num_act section page is consistently shaped:
#
#     <HR><H3>{act title} - Sect {n}</H3>
#     <p><b>{marginal note}</b></p>
#     <table><tr><td> {body} </td></tr></table>
#     <BR>
#     <HR>
#
# so the content is everything between the <H3> and the <BR> that closes it.
# Anchoring on <H3> rather than on the table matters: the page chrome is itself
# built from nested tables.

H3_RE = re.compile(r"<H3>(.*?)</H3>(.*?)<BR>", re.S | re.I)
HEADING_RE = re.compile(r"<p><b>(.*?)</b></p>", re.S | re.I)
CELL_RE = re.compile(r"<table>(.*?)</table>", re.S | re.I)
SECT_LINK_RE = re.compile(r'href="(s\d+[A-Za-z]?\.html)"', re.I)
LONGTITLE_RE = re.compile(r'href="(longtitle\.html)"', re.I)


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_section(page: str) -> dict | None:
    """Pull one section's title, marginal note and body out of a section page."""
    m = H3_RE.search(page)
    if not m:
        return None
    title, rest = m.group(1), m.group(2)
    heading = HEADING_RE.search(rest)
    cell = CELL_RE.search(rest)
    if cell is None:
        # Some sections carry no table wrapper; fall back to the whole block
        # minus the marginal note rather than dropping the section silently.
        body_src = HEADING_RE.sub("", rest)
    else:
        body_src = cell.group(1)
    return {
        "title": strip_tags(title),
        "heading": strip_tags(heading.group(1)) if heading else "",
        "text": strip_tags(body_src),
    }


def section_order(name: str) -> tuple[int, str]:
    m = re.match(r"s(\d+)([A-Za-z]?)\.html", name, re.I)
    return (int(m.group(1)), m.group(2).lower()) if m else (10**6, name)


def parse_index(page: str) -> list[str]:
    """Ordered list of the act's page names: long title first, then sections."""
    pages = []
    if LONGTITLE_RE.search(page):
        pages.append("longtitle.html")
    seen = set()
    for name in SECT_LINK_RE.findall(page):
        if name.lower() not in seen:
            seen.add(name.lower())
            pages.append(name)
    return pages[:1] + sorted(pages[1:], key=section_order)


# --- output ----------------------------------------------------------------

DOC = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="source-url" content="{index_url}">
<meta name="retrieved-from" content="{retrieved_from}">
<meta name="retrieved-at" content="{fetched_at}">
<meta name="status" content="unverified">
</head>
<body>
<!--
  Assembled from {n} CommonLII pages. Not an official publication: CommonLII is
  a priority-3 consolidator under data/legal-sources/conveyancing-source-checklist.md,
  and the official PDF remains the text authority. Section text is reproduced as
  served; only page chrome was removed. status: unverified, pending lawyer review.
-->
<h1>{title}</h1>
<p class="provenance">Source: <a href="{index_url}">{index_url}</a> &mdash; retrieved {fetched_at}</p>
{sections}
</body>
</html>
"""

SECTION = """<section class="section" id="{anchor}">
<h2 class="section-title">{title}</h2>
{heading}<div class="section-text">{text}</div>
</section>
"""


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_document(title: str, index_url: str, fetched_at: str,
                   sections: list[dict]) -> str:
    blocks = []
    for i, s in enumerate(sections):
        heading = (f'<p class="marginal-note">{esc(s["heading"])}</p>\n'
                   if s["heading"] else "")
        blocks.append(SECTION.format(
            anchor=f"sect-{i}" if not s.get("anchor") else s["anchor"],
            title=esc(s["title"]),
            heading=heading,
            text=esc(s["text"]),
        ))
    return DOC.format(
        title=esc(title), index_url=esc(index_url),
        retrieved_from=esc(RETRIEVED_FROM), fetched_at=esc(fetched_at),
        n=len(sections), sections="".join(blocks),
    )


def harvest(fetcher: Fetcher, source_id: str, slug: str, code: str,
            title: str) -> dict:
    index_url = f"{BASE}/{code}/index.html"
    index_page = fetcher.get(index_url, note=f"{slug} index")
    names = parse_index(index_page)
    if not names:
        raise RuntimeError(f"no section links found on {index_url}")

    sections = []
    for name in names:
        page = fetcher.get(f"{BASE}/{code}/{name}", note=f"{slug} {name}")
        parsed = parse_section(page)
        if parsed is None:
            print(f"    ! unparsed: {name}", file=sys.stderr)
            continue
        parsed["anchor"] = name[:-5].lower()
        sections.append(parsed)

    fetched_at = utc_now()
    document = build_document(title, index_url, fetched_at, sections)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{slug}.html"
    path.write_text(document, encoding="utf-8")

    return {
        "source_id": source_id,
        "official_title": title,
        "commonlii_code": code,
        "source_url": index_url,
        "local_html_path": path.relative_to(ROOT).as_posix(),
        "pages_fetched": len(names),
        "sections_written": len(sections),
        "expected_sections": len(names),
        "sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        "download_date": today(),
        "status": "unverified",
        "retrieved_from": RETRIEVED_FROM,
    }


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_id", "official_title", "commonlii_code", "source_url",
              "local_html_path", "pages_fetched", "sections_written",
              "expected_sections", "sha256", "download_date", "status",
              "retrieved_from"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would be fetched and exit")
    ap.add_argument("--offline", action="store_true",
                    help="build from cache only; never touch the network")
    ap.add_argument("--delay", type=float, default=DELAY_S,
                    help=f"seconds between requests (default {DELAY_S})")
    ap.add_argument("--only", action="append", default=[],
                    help="limit to these source_ids; repeatable")
    args = ap.parse_args()

    acts = [a for a in ACTS if not args.only or a[0] in args.only]
    if args.dry_run:
        for source_id, slug, code, title in acts:
            print(f"{source_id}  {code:<18} -> {slug}.html   ({title})")
        print(f"\n{len(acts)} act(s); one index request plus one per section.")
        return 0

    fetcher = Fetcher(delay_s=args.delay, offline=args.offline)
    rows, failed = [], []
    for source_id, slug, code, title in acts:
        print(f"{source_id}  {title}")
        try:
            row = harvest(fetcher, source_id, slug, code, title)
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED: {e}", file=sys.stderr)
            failed.append((source_id, str(e)))
            continue
        rows.append(row)
        print(f"    {row['sections_written']} section(s) -> "
              f"{row['local_html_path']}")

    if rows:
        write_manifest(rows)
        print(f"\nmanifest: {MANIFEST.relative_to(ROOT).as_posix()}")
    print(fetcher.summary())
    if failed:
        print(f"\n{len(failed)} act(s) failed:", file=sys.stderr)
        for source_id, err in failed:
            print(f"  {source_id}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
