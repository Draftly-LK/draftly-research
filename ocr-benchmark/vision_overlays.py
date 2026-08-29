"""Draw what Google Vision actually saw, as overlays.

    uv run python ocr-benchmark/vision_overlays.py

The corpus run cached only text and confidence, not geometry, so this re-calls
Vision for a small page set and keeps the block/paragraph boxes. Responses are
cached separately under renders/vision-cache/fullpage-boxes/ and the run is
resumable, so a repeat costs nothing.

Two overlays per page:
  left  - blocks coloured by Vision's own confidence
  right - paragraphs coloured by the script Vision recognised in them

The right panel is the interesting one: it is the direct visual answer to
"does Vision read Sinhala and Tamil", which docTR and RapidOCR both failed.

PRIVACY: overlays render real client pages. They are written to
renders/overlays/vision/, which is gitignored. No recognised text is printed or
saved outside the gitignored cache.
"""

from __future__ import annotations

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

import config
import render
import viz

DPI = 200
VARIANT = "original"
LANGUAGE_HINTS = ["si", "ta", "en"]
CACHE = config.RENDERS / "vision-cache" / "fullpage-boxes"
OUT = config.RENDERS / "overlays" / "vision"

# 4 representative pages plus the 3 the corpus report flagged as difficult.
PAGES = [
    ("source-003-title-certificate-parcel-0021.pdf", 1, "si+ta+en"),
    ("source-004-form8-instrument-of-transfer-with-stamp-receipt.pdf", 1, "en, numerics"),
    ("source-005-rta-sale-instrument-sinhala-registered.pdf", 1, "sinhala"),
    ("source-002-survey-plan-2338-lot-17-18-extracts.pdf", 1, "diagram"),
    ("source-001-national-identity-card.pdf", 1, "flagged difficult 0.245"),
    ("source-001-national-identity-card.pdf", 2, "flagged difficult 0.172"),
    ("source-004-form8-instrument-of-transfer-with-stamp-receipt.pdf", 16, "flagged difficult 0.084"),
]

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


def classify(text: str) -> str:
    counts = {
        "sinhala": len(re.findall(r"[඀-෿]", text)),
        "tamil": len(re.findall(r"[஀-௿]", text)),
        "latin": len(re.findall(r"[A-Za-z]", text)),
        "numeric": len(re.findall(r"[0-9]", text)),
    }
    return max(counts, key=lambda k: counts[k]) if sum(counts.values()) else "none"


def cache_path(doc_id: str, page_no: int) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in doc_id)
    return CACHE / safe / f"p{page_no:04d}@{DPI}-{VARIANT}.json"


def fetch(image, doc_id: str, page_no: int) -> dict[str, Any]:
    """Vision response reduced to geometry + confidence + per-paragraph script."""
    dest = cache_path(doc_id, page_no)
    if dest.is_file():
        return json.loads(dest.read_text(encoding="utf-8"))

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
    for page in annotation.pages:
        width = page.width or image.size[0]
        height = page.height or image.size[1]
        for block in page.blocks:
            verts = block.bounding_box.vertices
            blocks.append(
                {
                    "bbox": [min(v.x for v in verts) / width, min(v.y for v in verts) / height,
                             max(v.x for v in verts) / width, max(v.y for v in verts) / height],
                    "confidence": round(block.confidence, 4),
                }
            )
            for paragraph in block.paragraphs:
                pv = paragraph.bounding_box.vertices
                text = "".join(
                    "".join(s.text for s in word.symbols) + " " for word in paragraph.words
                )
                paragraphs.append(
                    {
                        "bbox": [min(v.x for v in pv) / width, min(v.y for v in pv) / height,
                                 max(v.x for v in pv) / width, max(v.y for v in pv) / height],
                        "confidence": round(paragraph.confidence, 4),
                        "script": classify(text),   # label only; the text is not stored
                        "chars": len(text.strip()),
                    }
                )
    payload = {"blocks": blocks, "paragraphs": paragraphs,
               "seconds": round(time.time() - began, 2)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload), encoding="utf-8")
    return payload


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
                                        linewidth=1.6, edgecolor=colour))
    ax.set_title(f"blocks by confidence — {len(payload['blocks'])} "
                 "(green >=.90, amber >=.70, red <.70)", fontsize=10)

    ax = axes[1]
    ax.imshow(page.image)
    present = []
    for paragraph in payload["paragraphs"]:
        x0, y0, x1, y1 = (paragraph["bbox"][0] * width, paragraph["bbox"][1] * height,
                          paragraph["bbox"][2] * width, paragraph["bbox"][3] * height)
        script = paragraph["script"]
        present.append(script)
        ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                                        linewidth=1.6,
                                        edgecolor=SCRIPT_COLOUR.get(script, viz.MUTED)))
    ax.set_title(f"paragraphs by recognised script — {len(payload['paragraphs'])}", fontsize=10)
    handles = [mpatches.Patch(color=SCRIPT_COLOUR[s], label=s)
               for s in dict.fromkeys(present) if s in SCRIPT_COLOUR]
    if handles:
        ax.legend(handles=handles, loc="lower right", fontsize=8)

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    fig.suptitle(title, fontsize=12)
    fig.savefig(dest, dpi=85, bbox_inches="tight")
    plt.close(fig)


def all_pages(case) -> list[tuple[str, int, str]]:
    """Every page of every document in the case."""
    import pypdfium2 as pdfium

    out = []
    for doc in config.case_documents(case):
        if doc.suffix.lower() == ".pdf":
            pdf = pdfium.PdfDocument(doc)
            try:
                count = len(pdf)
            finally:
                pdf.close()
        else:
            count = 1
        for page_no in range(1, count + 1):
            out.append((doc.name, page_no, "full-case sweep"))
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true",
                        help="every page of the case, not just the representative set")
    args = parser.parse_args()

    viz.use_style()
    config.assert_inputs_private()
    OUT.mkdir(parents=True, exist_ok=True)

    case = next(c for c in config.case_dirs() if c.name == "platform-case-001")
    pages = all_pages(case) if args.all else PAGES
    print(f"{len(pages)} pages")
    calls = 0
    for filename, page_no, why in pages:
        path = case / filename
        if not path.is_file():
            print("missing:", filename)
            continue
        doc_id = f"{case.name}/{filename}"
        cached = cache_path(doc_id, page_no).is_file()
        page = render.render_doc(path, dpi=DPI, variant=VARIANT, page_limit=page_no)[page_no - 1]
        try:
            payload = fetch(page.image, doc_id, page_no)
            calls += 0 if cached else 1
            short = filename.replace("source-", "")[:30]
            dest = OUT / f"vision-{short[:28]}-p{page_no}.png"
            draw(page, payload, f"{short} p{page_no}  ({why})", dest)
            scripts = {}
            for paragraph in payload["paragraphs"]:
                scripts[paragraph["script"]] = scripts.get(paragraph["script"], 0) + 1
            print(f"  {short:32s} p{page_no:<3d} blocks={len(payload['blocks']):3d} "
                  f"paras={len(payload['paragraphs']):3d} {scripts}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {filename[:40]} p{page_no}: {type(exc).__name__}: {exc}"[:150])
        finally:
            page.image.close()
            gc.collect()

    print(f"\n{calls} new Vision calls (~${calls * 0.0015:.4f})")
    print(f"overlays in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
