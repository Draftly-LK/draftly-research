"""Harvest public-domain Ceylon / Sri Lanka law reports from the Internet Archive.

Why IA: the comprehensive digital sources for NLR/SLR are not usable for
automated collection — CommonLII/WorldLII sit behind a Cloudflare bot challenge,
LawNet's site is gutted (returns "root directory"), and LawLanka is a commercial
service. The Internet Archive, by contrast, has an open API, hosts the
public-domain (pre-1978, mostly pre-1920) Ceylon law reports, and explicitly
sanctions programmatic download.

This script:
  1. Runs several IA advancedsearch queries.
  2. Filters hits to Ceylon/Sri Lanka law reports (title/creator heuristics).
  3. Fetches per-item metadata, downloads the plain-text (`*_djvu.txt`) file.
  4. Writes a manifest CSV.

Text only (not the large PDFs) — text is what the retrieval layer needs.
Public-record judgments; rights recorded per item. Polite: small delay between
requests.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path("data/legal-sources/library/case-law/internet-archive")
MANIFEST = Path("data/legal-sources/manifests/case-law-ia-manifest.csv")
UA = "DraftlyResearch/0.1 (academic legal-corpus research; contact via repo)"
DELAY = 0.7  # seconds between IA requests

QUERIES = [
    '(Ceylon AND "law reports")',
    'title:(Ceylon) AND title:(law)',
    '("New Law Reports" AND Ceylon)',
    '(Ceylon AND "Supreme Court" AND reports)',
    '(Ceylon AND appeal AND reports)',
    '("Sri Lanka Law Reports")',
    '(Ceylon AND "law recorder")',
]

# Title must look like a law report AND be Ceylon/Sri Lanka; exclude look-alikes.
REPORT_HINTS = (
    "law report", "law reports", "reports of cases", "reports of important",
    "supreme court", "court of appeal", "appeal reports", "law recorder",
    "new law reports", "decisions", "digest",
)
PLACE_HINTS = ("ceylon", "sri lanka")
EXCLUDE = (
    "new south wales", "new york", "new hampshire", "new jersey",
    "india", "pakistan", "liquor", "east-india", "dipavamsa", "mukkuva",
    "riots", "martial law", "agricultural",
)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def ia_search(q: str, rows: int = 200) -> list[dict]:
    base = "https://archive.org/advancedsearch.php"
    qs = urllib.parse.urlencode({"q": q, "rows": rows, "output": "json"})
    url = f"{base}?{qs}&fl[]=identifier&fl[]=title&fl[]=year&fl[]=mediatype&fl[]=creator"
    data = json.loads(_get(url))
    return data.get("response", {}).get("docs", [])


def is_ceylon_report(doc: dict) -> bool:
    title = str(doc.get("title", "")).lower()
    creator = str(doc.get("creator", "")).lower()
    blob = f"{title} {creator}"
    if any(x in blob for x in EXCLUDE):
        return False
    if doc.get("mediatype") != "texts":
        return False
    if not any(h in title for h in REPORT_HINTS):
        return False
    return any(p in blob for p in PLACE_HINTS)


def item_metadata(identifier: str) -> dict:
    return json.loads(_get(f"https://archive.org/metadata/{identifier}"))


def pick_text_file(meta: dict) -> str | None:
    for f in meta.get("files", []):
        if f.get("name", "").endswith("_djvu.txt"):
            return f["name"]
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: dict[str, dict] = {}
    for q in QUERIES:
        try:
            for d in ia_search(q):
                if is_ceylon_report(d):
                    seen.setdefault(d["identifier"], d)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] query failed: {q}: {e}")
        time.sleep(DELAY)

    print(f"Candidate Ceylon/SL law-report items: {len(seen)}")

    rows = []
    for i, (ident, doc) in enumerate(sorted(seen.items()), 1):
        try:
            meta = item_metadata(ident)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] metadata {ident}: {e}")
            continue
        m = meta.get("metadata", {})
        txt = pick_text_file(meta)
        rights = m.get("possible-copyright-status", "") or m.get("rights", "")
        title = str(m.get("title", ""))
        year = str(m.get("date", m.get("year", "")))[:4]
        dest_txt = ""
        chars = 0
        if txt:
            item_dir = OUT_DIR / ident
            item_dir.mkdir(parents=True, exist_ok=True)
            dest = item_dir / txt
            if not dest.exists():
                try:
                    blob = _get(f"https://archive.org/download/{ident}/{txt}")
                    dest.write_bytes(blob)
                    time.sleep(DELAY)
                except Exception as e:  # noqa: BLE001
                    print(f"[warn] download {ident}/{txt}: {e}")
            if dest.exists():
                dest_txt = str(dest).replace("\\", "/")
                chars = len(dest.read_text(encoding="utf-8", errors="ignore"))
        print(f"[{i}/{len(seen)}] {year:4} | {chars:>8} chars | {ident} | {title[:55]}")
        rows.append({
            "identifier": ident,
            "title": title,
            "year": year,
            "rights": rights,
            "text_file": dest_txt,
            "chars": chars,
            "detail_url": f"https://archive.org/details/{ident}",
        })
        time.sleep(DELAY)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "identifier", "title", "year", "rights", "text_file", "chars", "detail_url",
        ])
        w.writeheader()
        w.writerows(rows)
    got = sum(1 for r in rows if r["chars"] > 0)
    print(f"\nDone. {got}/{len(rows)} items with text. Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
