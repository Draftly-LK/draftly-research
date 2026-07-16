"""Harvest conveyancing judgments from the official Sri Lankan court sites.

Since 2012 the Supreme Court and Court of Appeal publish their judgments directly
(not just the reported NLR/SLR subset). These are free, official, primary-source
PDFs — legitimate to harvest.

Sources:
  - Supreme Court:   https://supremecourt.lk/judgements/ (one page, ~2,580 PDF links
    under /wp-content/uploads/judgements/)
  - Court of Appeal: attempted from judgements.courtofappeal.lk (if reachable)

For each PDF: download, extract the text layer with pypdfium2 (no OCR — scanned
PDFs come out empty and are flagged needs_ocr for Lahiru's pipeline), score for
conveyancing, and keep the matches. Manifests are tracked; the PDFs/text are
gitignored (rebuildable).
"""

from __future__ import annotations

import csv
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pypdfium2 as pdfium

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
DELAY = 0.3
THRESHOLD = 4  # full judgments; tunable — all text is kept so re-filtering is free

OUT = Path("data/legal-sources/library/case-law/courts")
MANIFEST = Path("data/legal-sources/manifests/case-law-courts.csv")
PROGRESS = Path("tmp/harvest/courts-progress.log")

SOURCES = {
    "sc": "https://supremecourt.lk/judgements/",
    "coa": "https://courtofappeal.lk/judgements/",
}

STRONG = re.compile(
    r"\b(deeds?|notar\w*|prescripti\w*|servitude|fidei[\s-]?commiss\w*|partition|"
    r"mortgage|hypothec\w*|conveyanc\w*|usufruct|donation|last will|testament\w*|"
    r"codicil|power of attorney|lease|easement|co-?owner\w*|undivided|vendor|"
    r"purchaser|land registrat\w*|deed of gift|title deed|prescriptive|"
    r"transfer of|gift deed|ownership of the land|immovable propert)\b", re.I)


def log(m: str) -> None:
    print(m, flush=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as fh:
        fh.write(m + "\n")


def get(url: str, binary: bool, tries: int = 3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                log(f"[warn] GET {url}: {e}")
            time.sleep(1.5)
    return None


def pdf_links(page_url: str) -> list[str]:
    html = get(page_url, binary=False)
    if not html:
        return []
    raw = re.findall(r'href="([^"]+\.pdf)"', html, re.I)
    out = []
    for h in raw:
        out.append(urllib.parse.urljoin(page_url, h))
    return sorted(set(out))


def extract_text(pdf_bytes: bytes) -> str:
    try:
        doc = pdfium.PdfDocument(pdf_bytes)
        parts = []
        for i in range(len(doc)):
            tp = doc[i].get_textpage()
            parts.append(tp.get_text_range())
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception as e:  # noqa: BLE001
        log(f"[warn] pdf parse: {e}")
        return ""


def main() -> None:
    rows = []
    total = matched = scanned = 0
    only = os.environ.get("COURTS")  # e.g. "coa" or "sc"; default = all
    sources = {k: v for k, v in SOURCES.items() if not only or k in only.split(",")}
    for court, url in sources.items():
        links = pdf_links(url)
        log(f"== {court}: {len(links)} PDF links from {url} ==")
        cdir = OUT / court
        cdir.mkdir(parents=True, exist_ok=True)
        for i, purl in enumerate(links, 1):
            total += 1
            name = purl.rsplit("/", 1)[-1]
            txt_dest = cdir / (name + ".txt")
            if txt_dest.exists():
                continue  # already processed (resume); manifest rebuildable from disk
            time.sleep(DELAY)
            blob = get(purl, binary=True)
            if not blob:
                continue
            text = extract_text(blob)
            needs_ocr = 1 if len(text) < 200 else 0
            if needs_ocr:
                scanned += 1
            hits = len(STRONG.findall(text))
            keep = hits >= THRESHOLD
            if text:
                txt_dest.write_text(text, encoding="utf-8")  # keep ALL text (re-tunable)
            if keep:
                (cdir / name).write_bytes(blob)               # keep matched PDF too
                matched += 1
            rows.append({
                "court": court, "file": name, "url": purl,
                "chars": len(text), "hits": hits,
                "conveyancing": int(keep), "needs_ocr": needs_ocr,
                "text_file": str(txt_dest).replace("\\", "/") if text else "",
            })
            if i % 100 == 0:
                log(f"  {court}: {i}/{len(links)} | matched={matched} scanned={scanned}")
                _flush(rows)
        _flush(rows)
        log(f"  {court} done. total={total} matched={matched} scanned(needs_ocr)={scanned}")
    _flush(rows)
    log(f"DONE-COURTS total={total} conveyancing_matched={matched} needs_ocr={scanned}")


FIELDS = ["court", "file", "url", "chars", "hits", "conveyancing", "needs_ocr", "text_file"]


def _flush(rows: list[dict]) -> None:
    """Merge this run's rows into the existing manifest (keyed by court+file), so a
    second run (e.g. Court of Appeal) does not clobber the Supreme Court rows."""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    merged: dict[tuple[str, str], dict] = {}
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                merged[(r["court"], r["file"])] = r
    for r in rows:
        merged[(r["court"], r["file"])] = {k: str(r.get(k, "")) for k in FIELDS}
    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(merged.values())


if __name__ == "__main__":
    main()
