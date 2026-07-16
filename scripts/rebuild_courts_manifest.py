"""Rebuild the court case-law manifest cleanly from the text files on disk.

The SC and CoA harvests ran in parallel and shared the manifest CSV; this
regenerates it deterministically by scanning every saved .txt, recomputing the
conveyancing hit count, and flagging scanned (needs_ocr) pages.
"""

from __future__ import annotations

import csv
import importlib.util
from collections import Counter
from pathlib import Path

spec = importlib.util.spec_from_file_location("h", "scripts/harvest_courts_caselaw.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

OUT = Path("data/legal-sources/library/case-law/courts")
MAN = Path("data/legal-sources/manifests/case-law-courts.csv")
BASE = {
    "sc": "https://supremecourt.lk/wp-content/uploads/judgements/",
    "coa": "https://courtofappeal.lk/wp-content/uploads/judgements/",
}

rows = []
for tf in OUT.rglob("*.txt"):
    court = tf.parts[-2]
    name = tf.name[:-4]
    text = tf.read_text(encoding="utf-8", errors="ignore")
    hits = len(h.STRONG.findall(text))
    needs_ocr = 1 if len(text) < 200 else 0
    rows.append({
        "court": court, "file": name, "url": BASE.get(court, "") + name,
        "chars": len(text), "hits": hits, "conveyancing": int(hits >= h.THRESHOLD),
        "needs_ocr": needs_ocr, "text_file": str(tf).replace("\\", "/"),
    })

rows.sort(key=lambda r: (r["court"], r["file"]))
MAN.parent.mkdir(parents=True, exist_ok=True)
with MAN.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=h.FIELDS)
    w.writeheader()
    w.writerows(rows)

proc = Counter(r["court"] for r in rows)
conv = Counter(r["court"] for r in rows if r["conveyancing"])
ocr = Counter(r["court"] for r in rows if r["needs_ocr"])
print("processed txt:", dict(proc))
print("conveyancing matches:", dict(conv), "| total:", sum(conv.values()))
print("needs_ocr:", dict(ocr), "| total:", sum(ocr.values()))
print("manifest rows:", len(rows), "->", MAN)
