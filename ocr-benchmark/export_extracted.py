"""Export Vision OCR text, JSON and overlays for platform-case-001 to extracted/.

    uv run python ocr-benchmark/export_extracted.py

Produces, for every page of the case:

    extracted/text/<document>-pNNNN.txt      recognised text, reading order
    extracted/json/<document>-pNNNN.json     boxes, confidence, script, languages
    extracted/overlays/<document>-pNNNN.png  two-panel overlay
    extracted/INDEX.csv                      one row per page, counts only

Vision responses are cached under renders/vision-cache/, so re-running costs
nothing. Only the missing pages are called.

NOTE: extracted/ holds recognised text and rendered images of real client
documents. Keep it out of version control.
"""

from __future__ import annotations

import csv
import gc
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pypdfium2 as pdfium

import config
import render
import viz

DPI = 200
VARIANT = "original"
CASE = "platform-case-001"
LANGUAGE_HINTS = ["si", "ta", "en"]

BOX_CACHE = config.RENDERS / "vision-cache" / "fullpage-boxes"
TEXT_CACHE = config.RENDERS / "vision-cache" / "fullpage"
OUT = Path(__file__).resolve().parent / "extracted"

SCRIPT_COLOUR = {
    "sinhala": viz.SERIES[0],
    "tamil": viz.SERIES[1],
    "latin": viz.SERIES[2],
    "numeric": viz.SERIES[3],
    "none": viz.MUTED,
}

_client = None


def client():
    global _client
    if _client is None:
        from dotenv import load_dotenv

        load_dotenv(config.ROOT / ".env")
        from google.cloud import vision

        _client = vision.ImageAnnotatorClient()
    return _client


def safe(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in text)


def script_of(text: str) -> str:
    counts = {
        "sinhala": len(re.findall(r"[඀-෿]", text)),
        "tamil": len(re.findall(r"[஀-௿]", text)),
        "latin": len(re.findall(r"[A-Za-z]", text)),
        "numeric": len(re.findall(r"[0-9]", text)),
    }
    return max(counts, key=lambda k: counts[k]) if sum(counts.values()) else "none"


def fetch_boxes(image, doc_id: str, page_no: int) -> tuple[dict[str, Any], bool]:
    """Vision geometry + per-paragraph text. Returns (payload, was_new_call)."""
    dest = BOX_CACHE / safe(doc_id) / f"p{page_no:04d}@{DPI}-{VARIANT}.json"
    if dest.is_file():
        payload = json.loads(dest.read_text(encoding="utf-8"))
        if payload.get("paragraphs") and "text" in (payload["paragraphs"][0] or {}):
            return payload, False

    from google.cloud import vision

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    began = time.time()
    response = client().document_text_detection(
        image=vision.Image(content=buffer.getvalue()),
        image_context=vision.ImageContext(language_hints=LANGUAGE_HINTS),
    )
    if response.error.message:
        raise RuntimeError(response.error.message[:200])

    annotation = response.full_text_annotation
    blocks: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []
    languages: list[str] = []
    for page in annotation.pages:
        width = page.width or image.size[0]
        height = page.height or image.size[1]
        for lang in getattr(page.property, "detected_languages", []) or []:
            languages.append(lang.language_code)
        for block in page.blocks:
            verts = block.bounding_box.vertices
            blocks.append({
                "bbox": [min(v.x for v in verts) / width, min(v.y for v in verts) / height,
                         max(v.x for v in verts) / width, max(v.y for v in verts) / height],
                "confidence": round(block.confidence, 4),
            })
            for paragraph in block.paragraphs:
                pv = paragraph.bounding_box.vertices
                text = "".join(
                    "".join(s.text for s in word.symbols) + " " for word in paragraph.words
                ).strip()
                paragraphs.append({
                    "bbox": [min(v.x for v in pv) / width, min(v.y for v in pv) / height,
                             max(v.x for v in pv) / width, max(v.y for v in pv) / height],
                    "confidence": round(paragraph.confidence, 4),
                    "script": script_of(text),
                    "text": text,
                })
    payload = {
        "blocks": blocks,
        "paragraphs": paragraphs,
        "full_text": annotation.text or "",
        "detected_languages": sorted(set(languages)),
        "seconds": round(time.time() - began, 2),
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload, True


def reading_order(paragraphs: list[dict[str, Any]]) -> str:
    """Top-to-bottom, left-to-right, blank line on a paragraph gap."""
    ordered = sorted(paragraphs, key=lambda p: (round(p["bbox"][1], 3), p["bbox"][0]))
    out: list[str] = []
    previous_bottom = None
    for paragraph in ordered:
        text = " ".join(paragraph["text"].split())
        if not text:
            continue
        if previous_bottom is not None and paragraph["bbox"][1] - previous_bottom > 0.018:
            out.append("")
        out.append(text)
        previous_bottom = paragraph["bbox"][3]
    return "\n".join(out)


def draw(page, payload: dict[str, Any], title: str, dest: Path) -> None:
    width, height = page.size
    fig, axes = plt.subplots(1, 2, figsize=(14, 9.5))

    ax = axes[0]
    ax.imshow(page.image)
    for block in payload["blocks"]:
        x0, y0, x1, y1 = (block["bbox"][0] * width, block["bbox"][1] * height,
                          block["bbox"][2] * width, block["bbox"][3] * height)
        confidence = block["confidence"]
        colour = (viz.STATUS["correct"] if confidence >= 0.90
                  else viz.STATUS["missing"] if confidence >= 0.70
                  else viz.STATUS["wrong"])
        ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                                        linewidth=1.5, edgecolor=colour))
    ax.set_title(f"blocks by confidence — {len(payload['blocks'])}  "
                 "(green ≥.90, amber ≥.70, red <.70)", fontsize=10)

    ax = axes[1]
    ax.imshow(page.image)
    seen: list[str] = []
    for paragraph in payload["paragraphs"]:
        x0, y0, x1, y1 = (paragraph["bbox"][0] * width, paragraph["bbox"][1] * height,
                          paragraph["bbox"][2] * width, paragraph["bbox"][3] * height)
        seen.append(paragraph["script"])
        ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=1.5,
                                        edgecolor=SCRIPT_COLOUR.get(paragraph["script"], viz.MUTED)))
    ax.set_title(f"paragraphs by script — {len(payload['paragraphs'])}", fontsize=10)
    handles = [mpatches.Patch(color=SCRIPT_COLOUR[s], label=s)
               for s in dict.fromkeys(seen) if s in SCRIPT_COLOUR]
    if handles:
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    fig.suptitle(title, fontsize=12)
    fig.savefig(dest, dpi=85, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    viz.use_style()
    for sub in ("text", "json", "overlays"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    case = next(c for c in config.case_dirs() if c.name == CASE)
    rows: list[dict[str, Any]] = []
    calls = 0

    for doc in sorted(config.case_documents(case)):
        pdf = pdfium.PdfDocument(doc)
        try:
            total = len(pdf)
        finally:
            pdf.close()
        stem = doc.stem.replace("source-", "")

        for page_no in range(1, total + 1):
            doc_id = f"{case.name}/{doc.name}"
            page = render.render_doc(doc, dpi=DPI, variant=VARIANT, page_limit=page_no)[page_no - 1]
            try:
                payload, is_new = fetch_boxes(page.image, doc_id, page_no)
                calls += int(is_new)

                base = f"{stem[:44]}-p{page_no:04d}"
                text = reading_order(payload["paragraphs"]) or payload.get("full_text", "")
                (OUT / "text" / f"{base}.txt").write_text(text, encoding="utf-8")
                (OUT / "json" / f"{base}.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
                draw(page, payload, f"{stem[:46]}  page {page_no}/{total}",
                     OUT / "overlays" / f"{base}.png")

                stripped = re.sub(r"\s+", "", text)
                rows.append({
                    "document": doc.name,
                    "page": page_no,
                    "chars": len(stripped),
                    "blocks": len(payload["blocks"]),
                    "paragraphs": len(payload["paragraphs"]),
                    "sinhala": len(re.findall(r"[඀-෿]", text)),
                    "tamil": len(re.findall(r"[஀-௿]", text)),
                    "latin": len(re.findall(r"[A-Za-z]", text)),
                    "digits": len(re.findall(r"[0-9]", text)),
                    "mean_confidence": round(
                        sum(b["confidence"] for b in payload["blocks"]) / len(payload["blocks"]), 4
                    ) if payload["blocks"] else 0.0,
                    "languages": ",".join(payload.get("detected_languages", [])),
                })
                print(f"  {base:52s} chars={len(stripped):5d} paras={len(payload['paragraphs']):3d}"
                      f"{'  (new call)' if is_new else ''}")
            except Exception as exc:  # noqa: BLE001
                print(f"  {stem[:44]} p{page_no}: {type(exc).__name__}: {str(exc)[:90]}")
            finally:
                page.image.close()
                gc.collect()

    if rows:
        index = OUT / "INDEX.csv"
        with index.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n{len(rows)} pages exported to {OUT}")
        print(f"  text/     {len(rows)} .txt")
        print(f"  json/     {len(rows)} .json")
        print(f"  overlays/ {len(rows)} .png")
        print(f"  INDEX.csv")
        print(f"\n{calls} new Vision calls (~${calls * 0.0015:.4f})")
        print(f"totals: chars={sum(r['chars'] for r in rows)} "
              f"sinhala={sum(r['sinhala'] for r in rows)} "
              f"tamil={sum(r['tamil'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
