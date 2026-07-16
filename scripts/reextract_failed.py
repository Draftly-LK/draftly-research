"""Re-extract the statute conversions that failed under docling (std::bad_alloc).

Uses pypdfium2 text extraction (no page rendering -> no OOM). Updates the failed
conversion-registry rows in place. Rows whose PDF has no text layer stay flagged
for OCR.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data/legal-sources/manifests/conversion-registry.csv"
OK = {"converted", "fallback-pdftotext"}


def extract(pdf: Path) -> tuple[str, int]:
    doc = pdfium.PdfDocument(str(pdf))
    parts = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    text = "\n".join(parts)
    return text, len(doc)


with REG.open(encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
    fields = rows[0].keys()

fixed = still = 0
for r in rows:
    if r.get("status") in OK:
        continue
    src = ROOT / r["source_path"]
    md = ROOT / r["markdown_path"] if r.get("markdown_path") else None
    if not src.exists() or md is None:
        print(f"[skip] {r['source_id']}: pdf/markdown path missing")
        continue
    try:
        text, pages = extract(src)
    except Exception as e:  # noqa: BLE001
        print(f"[fail] {r['source_id']}: {e}")
        continue
    nz = len(re.sub(r"\s+", "", text))
    if nz < 200:
        r["status"] = "needs-ocr"
        r["quality_notes"] = f"pypdfium2 re-extract: no text layer (pages={pages}, non_ws={nz}); scanned -> OCR."
        still += 1
        print(f"[ocr ] {r['source_id']}: scanned, {pages}p, {nz} chars -> needs-ocr")
    else:
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(text, encoding="utf-8")
        r["status"] = "converted"
        r["converter"] = "pypdfium2"
        r["converter_version"] = getattr(pdfium, "__version__", "")
        r["ocr_enabled"] = "false"
        r["quality_notes"] = f"Re-extracted with pypdfium2 after docling bad_alloc; pages={pages}, non_ws={nz}."
        r["converted_at"] = datetime.now().isoformat(timespec="seconds")
        fixed += 1
        print(f"[ok  ] {r['source_id']}: {pages}p, {nz} chars -> converted")

with REG.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(fields))
    w.writeheader()
    w.writerows(rows)
print(f"\nre-extracted: {fixed} converted, {still} still need OCR")
