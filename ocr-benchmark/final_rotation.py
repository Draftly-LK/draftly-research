"""Rotation-aware final JSON for platform-case-001.

    uv run python ocr-benchmark/export_extracted.py     # produces extracted/json/
    uv run python ocr-benchmark/final_rotation.py       # produces extracted/final/

Writes extracted/final/<original-name>.json plus extracted/final/rotation-report.json.
Nothing in extracted/json/ is read for geometry, modified, or deleted.

WHY THIS EXISTS
The boxes in extracted/json/ are axis-aligned [x0, y0, x1, y1] rectangles. That
representation cannot express rotation: a word rotated 90 degrees and a word
sitting upright produce the same kind of rectangle. Rotation therefore cannot be
recovered from those files, and guessing it from box aspect ratios would be
invention. This module goes back to Cloud Vision for the original four-point
vertex order and derives orientation from that.

RAW RESPONSES ARE CACHED with word-level polygons under
renders/vision-cache/raw-words/, so the geometry never has to be re-fetched again.

CONVENTIONS
  detected_orientation_degrees
      How far the text is rotated CLOCKWISE from upright, snapped to 0/90/180/270.
  correction_degrees
      Degrees to rotate the PAGE CLOCKWISE so the text reads upright,
      i.e. (360 - detected) % 360.
  polygons
      Normalized [[x, y] x4] in the ORIGINAL page frame for `original_polygon`,
      and in the CORRECTED (upright) frame for `corrected_polygon`.

PRIVACY: full text and word text live in the per-page files, which are
gitignored. The rotation report and all console output carry counts and angles
only - no recognised text, no client values.
"""

from __future__ import annotations

import gc
import hashlib
import io
import json
import math
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import render

SCHEMA_VERSION = "1.0"
DPI = 200
VARIANT = "original"
CASE = "platform-case-001"
LANGUAGE_HINTS = ["si", "ta", "en"]
PROVIDER = "google-cloud-vision:document_text_detection"

RAW_CACHE = config.RENDERS / "vision-cache" / "raw-words"
OUT = Path(__file__).resolve().parent / "extracted" / "final"

# Vote thresholds, per the spec. Below either of these the page is `uncertain`.
MIN_USABLE_WORDS = 10
MIN_VOTE_SHARE = 0.70
MIN_WORD_CONFIDENCE = 0.60      # "high-confidence" words only
MIN_TOP_EDGE = 1e-6             # degenerate polygons contribute nothing

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


# ── orientation ──────────────────────────────────────────────────────────────
def top_edge(polygon: Sequence[Sequence[float]]) -> tuple[float, float]:
    """Vector along the polygon's first edge (v0 -> v1).

    Vision emits vertices starting at the text's own top-left and proceeding
    clockwise in reading order, so v0 -> v1 runs along the top of the glyphs and
    points in the direction the text is read. That is the rotation signal.
    """
    (x0, y0), (x1, y1) = polygon[0], polygon[1]
    return (x1 - x0, y1 - y0)


def snap_orientation(dx: float, dy: float) -> int | None:
    """Angle of the top edge, snapped to 0/90/180/270 degrees clockwise.

    Image coordinates have y increasing downward, so a positive atan2 angle is
    already a clockwise rotation.
    """
    if math.hypot(dx, dy) < MIN_TOP_EDGE:
        return None
    degrees = math.degrees(math.atan2(dy, dx)) % 360
    return int(round(degrees / 90.0) * 90) % 360


def detect_orientation(words: list[dict[str, Any]]) -> dict[str, Any]:
    """Confidence x top-edge-length weighted vote over high-confidence words.

    Deterministic: no randomness, no model, no tie-breaking by chance. A tie
    between two orientations cannot reach a 70% share, so it resolves to
    `uncertain` by construction.
    """
    votes: dict[int, float] = defaultdict(float)
    usable = 0
    for word in words:
        if (word.get("confidence") or 0.0) < MIN_WORD_CONFIDENCE:
            continue
        polygon = word.get("original_polygon") or []
        if len(polygon) < 2:
            continue
        dx, dy = top_edge(polygon)
        orientation = snap_orientation(dx, dy)
        if orientation is None:
            continue
        length = math.hypot(dx, dy)
        votes[orientation] += float(word["confidence"]) * length
        usable += 1

    total = sum(votes.values())
    if usable < MIN_USABLE_WORDS or total <= 0:
        return {
            "detected_orientation_degrees": None,
            "correction_degrees": 0,
            "status": "uncertain",
            "vote_share": 0.0,
            "usable_word_count": usable,
            "threshold": {"min_usable_words": MIN_USABLE_WORDS,
                          "min_vote_share": MIN_VOTE_SHARE},
            "method": "confidence x top-edge-length weighted vote, snapped to 90 deg",
        }

    best = max(votes, key=lambda k: votes[k])
    share = votes[best] / total
    if share < MIN_VOTE_SHARE:
        return {
            "detected_orientation_degrees": None,
            "correction_degrees": 0,
            "status": "uncertain",
            "vote_share": round(share, 4),
            "usable_word_count": usable,
            "threshold": {"min_usable_words": MIN_USABLE_WORDS,
                          "min_vote_share": MIN_VOTE_SHARE},
            "method": "confidence x top-edge-length weighted vote, snapped to 90 deg",
        }

    correction = (360 - best) % 360
    return {
        "detected_orientation_degrees": best,
        "correction_degrees": correction,
        "status": "upright" if best == 0 else "rotate",
        "vote_share": round(share, 4),
        "usable_word_count": usable,
        "threshold": {"min_usable_words": MIN_USABLE_WORDS,
                      "min_vote_share": MIN_VOTE_SHARE},
        "method": "confidence x top-edge-length weighted vote, snapped to 90 deg",
    }


def rotate_point(x: float, y: float, degrees_cw: int) -> tuple[float, float]:
    """Rotate a normalized point as the PAGE rotates clockwise by `degrees_cw`."""
    d = degrees_cw % 360
    if d == 0:
        return (x, y)
    if d == 90:
        return (1.0 - y, x)
    if d == 180:
        return (1.0 - x, 1.0 - y)
    if d == 270:
        return (y, 1.0 - x)
    raise ValueError(f"unsupported rotation {degrees_cw}")


def rotate_polygon(polygon: Sequence[Sequence[float]], degrees_cw: int) -> list[list[float]]:
    return [list(rotate_point(p[0], p[1], degrees_cw)) for p in polygon]


def reading_order_key(polygon: Sequence[Sequence[float]], band: float = 0.02):
    """Sort key in the CORRECTED frame: top-to-bottom by band, then left-to-right."""
    ys = [p[1] for p in polygon]
    xs = [p[0] for p in polygon]
    return (round(min(ys) / band), min(xs))


# ── Vision fetch ─────────────────────────────────────────────────────────────
def fetch_raw(image, doc_id: str, page_no: int) -> tuple[dict[str, Any], bool]:
    """Word/paragraph/block four-point polygons. Cached; (payload, was_new_call)."""
    dest = RAW_CACHE / safe(doc_id) / f"p{page_no:04d}@{DPI}-{VARIANT}.json"
    if dest.is_file():
        return json.loads(dest.read_text(encoding="utf-8")), False

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
    words: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    languages: list[dict[str, Any]] = []

    def poly(bounding, width: int, height: int) -> list[list[float]]:
        """Preserve VERTEX ORDER; do not sort or hull, that is the rotation signal."""
        return [[round(v.x / width, 6), round(v.y / height, 6)] for v in bounding.vertices]

    for page in annotation.pages:
        width = page.width or image.size[0]
        height = page.height or image.size[1]
        for lang in getattr(page.property, "detected_languages", []) or []:
            languages.append({"code": lang.language_code,
                              "confidence": round(lang.confidence, 4)})
        for block in page.blocks:
            blocks.append({"polygon": poly(block.bounding_box, width, height),
                           "confidence": round(block.confidence, 4)})
            for paragraph in block.paragraphs:
                paragraphs.append({"polygon": poly(paragraph.bounding_box, width, height),
                                   "confidence": round(paragraph.confidence, 4)})
                for word in paragraph.words:
                    words.append({
                        "text": "".join(s.text for s in word.symbols),
                        "confidence": round(word.confidence, 4),
                        "polygon": poly(word.bounding_box, width, height),
                    })

    payload = {
        "provider": PROVIDER,
        "full_text": annotation.text or "",
        "detected_languages": languages,
        "words": words,
        "paragraphs": paragraphs,
        "blocks": blocks,
        "page_width": image.size[0],
        "page_height": image.size[1],
        "seconds": round(time.time() - began, 2),
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload, True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def build_page(raw: dict[str, Any], doc: Path, page_no: int,
               source_sha: str) -> dict[str, Any]:
    words = [{"text": w["text"], "confidence": w["confidence"],
              "original_polygon": w["polygon"]} for w in raw["words"]]

    rotation = detect_orientation(words)
    correction = rotation["correction_degrees"] if rotation["status"] == "rotate" else 0

    for word in words:
        word["corrected_polygon"] = rotate_polygon(word["original_polygon"], correction)
    ordered = sorted(words, key=lambda w: reading_order_key(w["corrected_polygon"]))
    for index, word in enumerate(ordered):
        word["reading_order"] = index

    swapped = correction in (90, 270)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_document": doc.name,
        "page_no": page_no,
        "source_sha256": source_sha,
        "page_width": raw["page_height"] if swapped else raw["page_width"],
        "page_height": raw["page_width"] if swapped else raw["page_height"],
        "original_page_width": raw["page_width"],
        "original_page_height": raw["page_height"],
        "dpi": DPI,
        "full_text": raw["full_text"],
        "detected_languages": raw["detected_languages"],
        "rotation": rotation,
        "words": words,
        "paragraphs": [{"confidence": p["confidence"],
                        "original_polygon": p["polygon"],
                        "corrected_polygon": rotate_polygon(p["polygon"], correction)}
                       for p in raw["paragraphs"]],
        "blocks": [{"confidence": b["confidence"],
                    "original_polygon": b["polygon"],
                    "corrected_polygon": rotate_polygon(b["polygon"], correction)}
                   for b in raw["blocks"]],
        "provider": raw["provider"],
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    import pypdfium2 as pdfium

    OUT.mkdir(parents=True, exist_ok=True)
    case = next(c for c in config.case_dirs() if c.name == CASE)
    report: list[dict[str, Any]] = []
    calls = 0

    for doc in sorted(config.case_documents(case)):
        pdf = pdfium.PdfDocument(doc)
        try:
            total = len(pdf)
        finally:
            pdf.close()
        source_sha = sha256_file(doc)
        stem = doc.stem.replace("source-", "")

        for page_no in range(1, total + 1):
            doc_id = f"{case.name}/{doc.name}"
            page = render.render_doc(doc, dpi=DPI, variant=VARIANT, page_limit=page_no)[page_no - 1]
            try:
                raw, is_new = fetch_raw(page.image, doc_id, page_no)
                calls += int(is_new)
                final = build_page(raw, doc, page_no, source_sha)

                name = f"{stem[:44]}-p{page_no:04d}.json"
                (OUT / name).write_text(
                    json.dumps(final, ensure_ascii=False, indent=1), encoding="utf-8")

                rotation = final["rotation"]
                report.append({
                    "document": doc.name,
                    "page": page_no,
                    "detected_orientation_degrees": rotation["detected_orientation_degrees"],
                    "correction_degrees": rotation["correction_degrees"],
                    "status": rotation["status"],
                    "vote_share": rotation["vote_share"],
                    "usable_word_count": rotation["usable_word_count"],
                })
                print(f"  {name:52s} {rotation['status']:9s} "
                      f"det={str(rotation['detected_orientation_degrees']):>4s} "
                      f"corr={rotation['correction_degrees']:3d} "
                      f"share={rotation['vote_share']:.2f} words={rotation['usable_word_count']:4d}"
                      f"{'  (new call)' if is_new else ''}")
            except Exception as exc:  # noqa: BLE001
                print(f"  {stem[:44]} p{page_no}: {type(exc).__name__}: {str(exc)[:90]}")
            finally:
                page.image.close()
                gc.collect()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case": CASE,
        "provider": PROVIDER,
        "method": "confidence x top-edge-length weighted vote over high-confidence word polygons",
        "thresholds": {"min_usable_words": MIN_USABLE_WORDS,
                       "min_vote_share": MIN_VOTE_SHARE,
                       "min_word_confidence": MIN_WORD_CONFIDENCE},
        "counts": {
            "pages": len(report),
            **{status: sum(1 for r in report if r["status"] == status)
               for status in ("upright", "rotate", "uncertain")},
        },
        "pages": report,
        "note": ("Angles and counts only. No recognised text or client values appear "
                 "in this report."),
    }
    (OUT / "rotation-report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n{len(report)} pages -> {OUT}")
    print("status:", summary["counts"])
    print(f"{calls} new Vision calls (~${calls * 0.0015:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
