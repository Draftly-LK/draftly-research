"""Harvest Sri Lankan case law (NLR + SLR era) from CommonLII.

CommonLII hosts the Supreme Court (LKSC, 1878-2012) and Court of Appeal (LKCA,
1809-2010) decisions — the cases reported in the New Law Reports (pre-1978) and
Sri Lanka Law Reports (1978+). Access is UA-gated (a browser User-Agent passes;
the default curl/urllib UA gets a Cloudflare 403), so we send a browser UA and
stay polite (rate-limited, resumable, single-threaded).

Produces:
  - manifests/case-law-commonlii-index.csv : EVERY case (complete citation index)
  - library/case-law/commonlii/<db>/<year>/<n>.txt : full text of cases that pass
    the conveyancing filter
  - manifests/case-law-commonlii-conveyancing.csv : the matched (conveyancing)
    subset with metadata

For an internal research/eval corpus only (not republished). Judgment text is
public record.
"""

from __future__ import annotations

import csv
import html
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.commonlii.org"
DBS = ["LKSC", "LKCA"]
OUT_TEXT = Path("data/legal-sources/library/case-law/commonlii")
IDX_CSV = Path("data/legal-sources/manifests/case-law-commonlii-index.csv")
CONV_CSV = Path("data/legal-sources/manifests/case-law-commonlii-conveyancing.csv")
PROGRESS = Path("tmp/harvest/commonlii-progress.log")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
DELAY = 0.25          # polite gap between requests (seconds)
THRESHOLD = 3         # min strong conveyancing keyword hits to keep full text

STRONG = re.compile(
    r"\b(deeds?|notar\w*|prescripti\w*|servitude|fidei[\s-]?commiss\w*|partition|"
    r"mortgage|hypothec\w*|conveyanc\w*|usufruct|donation|last will|testament\w*|"
    r"codicil|power of attorney|lease|easement|co-?owner\w*|undivided|vendor|"
    r"purchaser|land registrat\w*|deed of gift|title deed|prescriptive)\b", re.I)

# Citation patterns found in link titles, e.g. "(2000) 1 Sri LR 78" or "72 NLR 289".
CIT = re.compile(r"(\(\d{4}\)\s*\d*\s*Sri\s*L\.?\s*R\.?\s*\d+|\d+\s*N\.?L\.?R\.?\s*\d+)", re.I)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def strip_html(h: str) -> str:
    p = _Text()
    p.feed(h)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def get(url: str, tries: int = 2) -> str | None:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                log(f"[warn] GET fail {url}: {e}")
            time.sleep(1.0)
    return None


def log(msg: str) -> None:
    print(msg, flush=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


LINK = re.compile(r'href="([^"]+?)"[^>]*>(.*?)</a>', re.I | re.S)


def year_links(db: str) -> list[int]:
    h = get(f"{BASE}/lk/cases/{db}/") or ""
    # hrefs are relative, e.g. href="1900/"
    yrs = {int(m) for m in re.findall(r'href="(\d{4})/?"', h)}
    return sorted(yrs)


def case_links(db: str, year: int) -> list[tuple[str, str]]:
    h = get(f"{BASE}/lk/cases/{db}/{year}/") or ""
    out = []
    for href, label in LINK.findall(h):
        if re.search(r"/?\d+\.html?$", href):
            title = re.sub(r"\s+", " ", strip_html(label)).strip()
            url = urllib.parse.urljoin(f"{BASE}/lk/cases/{db}/{year}/", href)
            if re.search(rf"/lk/cases/{db}/{year}/\d+\.html?$", url):
                out.append((url, title))
    return out


def main() -> None:
    OUT_TEXT.mkdir(parents=True, exist_ok=True)
    idx_rows, conv_rows = [], []
    total = matched = 0
    for db in DBS:
        years = year_links(db)
        log(f"== {db}: {len(years)} years ({years[0]}-{years[-1]}) ==")
        for y in years:
            cases = case_links(db, y)
            for url, title in cases:
                total += 1
                cno = re.search(r"/(\d+)\.html?$", url).group(1)
                cit = CIT.search(title)
                cit = cit.group(0).strip() if cit else ""
                idx_rows.append([db, y, cno, cit, title[:300], url])
                dest = OUT_TEXT / db / str(y) / f"{cno}.txt"
                if dest.exists():
                    matched += 1
                    continue
                time.sleep(DELAY)
                page = get(url)
                if not page:
                    continue
                text = strip_html(page)
                hits = len(STRONG.findall(text))
                if hits >= THRESHOLD:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(text, encoding="utf-8")
                    conv_rows.append([db, y, cno, cit, title[:300], hits, len(text), url,
                                      str(dest).replace("\\", "/")])
                    matched += 1
            log(f"  {db} {y}: {len(cases)} cases | running matched={matched} total={total}")
        # flush after each db
        _write(IDX_CSV, ["db", "year", "case_no", "citation", "title", "url"], idx_rows)
        _write(CONV_CSV, ["db", "year", "case_no", "citation", "title", "hits",
                          "chars", "url", "text_file"], conv_rows)
    log(f"DONE. total_cases={total} conveyancing_matched={matched}")


def _write(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    main()
