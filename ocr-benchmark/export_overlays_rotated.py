"""Regenerate extracted/overlays/ on the UPRIGHT pages, using corrected polygons.

    uv run python ocr-benchmark/export_rotated_images.py     # upright PNGs first
    uv run python ocr-benchmark/export_overlays_rotated.py   # then these overlays

The previous overlays were drawn on the original, un-rotated renders. On the 16
rotated pages that put sideways boxes over sideways text: readable only by
tilting your head, and useless for judging reading order.

This draws `corrected_polygon` from extracted/final/ onto the upright image from
extracted/correctly-rotated-images/. Both are in the same frame, so no further
transformation is applied here - if a box is misplaced, the fault is in the
rotation step, not in the drawing, which is the point of keeping them separate.

Panels per page:
  left  - blocks and paragraphs, coloured by Vision confidence
  right - words, coloured by recognised script, with reading order sampled

Pages marked `uncertain` are drawn on the unrotated image and labelled as such.

PRIVACY: these render real client pages into extracted/, which must stay out of
version control. No recognised text is printed to the console.
"""

from __future__ import annotations

import gc
import json
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import viz

BASE = Path(__file__).resolve().parent / "extracted"
FINAL = BASE / "final"
IMAGES = BASE / "correctly-rotated-images"
OUT = BASE / "overlays"

SCRIPT_COLOUR = {
    "sinhala": viz.SERIES[0],
    "tamil": viz.SERIES[1],
    "latin": viz.SERIES[2],
    "numeric": viz.SERIES[3],
    "none": viz.MUTED,
}


def script_of(text: str) -> str:
    counts = {
        "sinhala": len(re.findall(r"[඀-෿]", text)),
        "tamil": len(re.findall(r"[஀-௿]", text)),
        "latin": len(re.findall(r"[A-Za-z]", text)),
        "numeric": len(re.findall(r"[0-9]", text)),
    }
    return max(counts, key=lambda k: counts[k]) if sum(counts.values()) else "none"


def to_pixels(polygon, width: int, height: int):
    return [(p[0] * width, p[1] * height) for p in polygon]


def draw_page(meta: dict[str, Any], image: Image.Image, dest: Path) -> None:
    width, height = image.size
    rotation = meta["rotation"]
    uncertain = rotation["status"] == "uncertain"
    key = "original_polygon" if uncertain else "corrected_polygon"

    fig, axes = plt.subplots(1, 2, figsize=(15, 10))

    # --- left: structure by confidence ---------------------------------------
    ax = axes[0]
    ax.imshow(image)
    for block in meta["blocks"]:
        points = to_pixels(block[key], width, height)
        if len(points) >= 3:
            ax.add_patch(mpatches.Polygon(points, closed=True, fill=False,
                                          linewidth=2.0, edgecolor=viz.INK_2, alpha=0.55))
    for paragraph in meta["paragraphs"]:
        points = to_pixels(paragraph[key], width, height)
        if len(points) < 3:
            continue
        confidence = paragraph["confidence"]
        colour = (viz.STATUS["correct"] if confidence >= 0.90
                  else viz.STATUS["missing"] if confidence >= 0.70
                  else viz.STATUS["wrong"])
        ax.add_patch(mpatches.Polygon(points, closed=True, fill=False,
                                      linewidth=1.4, edgecolor=colour))
    ax.set_title(f"{len(meta['blocks'])} blocks (grey) · {len(meta['paragraphs'])} paragraphs "
                 "(green ≥.90, amber ≥.70, red <.70)", fontsize=9)

    # --- right: words by script ----------------------------------------------
    ax = axes[1]
    ax.imshow(image)
    seen: list[str] = []
    words = sorted(meta["words"], key=lambda w: w.get("reading_order", 0))
    for word in words:
        points = to_pixels(word[key], width, height)
        if len(points) < 3:
            continue
        script = script_of(word["text"])
        seen.append(script)
        ax.add_patch(mpatches.Polygon(points, closed=True, fill=False, linewidth=1.1,
                                      edgecolor=SCRIPT_COLOUR.get(script, viz.MUTED)))
    # Sample the reading order rather than numbering every word, which would be
    # unreadable at 400+ words per page.
    step = max(1, len(words) // 12)
    for index in range(0, len(words), step):
        word = words[index]
        points = to_pixels(word[key], width, height)
        if points:
            ax.text(points[0][0], points[0][1] - 4, str(word.get("reading_order", index)),
                    fontsize=6, color=viz.INK, alpha=0.8)
    ax.set_title(f"{len(words)} words by script · reading order sampled every {step}",
                 fontsize=9)
    handles = [mpatches.Patch(color=SCRIPT_COLOUR[s], label=s)
               for s in dict.fromkeys(seen) if s in SCRIPT_COLOUR]
    if handles:
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)

    detected = rotation["detected_orientation_degrees"]
    banner = (f"{meta['source_document'][:44]}  page {meta['page_no']}   "
              f"[{rotation['status']}] detected={detected}° "
              f"correction={rotation['correction_degrees']}° "
              f"vote={rotation['vote_share']:.2f}")
    if uncertain:
        banner += "   — drawn on the ORIGINAL page, rotation not applied"
    fig.suptitle(banner, fontsize=11)
    fig.savefig(dest, dpi=85, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    viz.use_style()
    OUT.mkdir(parents=True, exist_ok=True)

    metas = sorted(FINAL.glob("*-p*.json"))
    if not metas:
        print(f"no page JSON in {FINAL}; run final_rotation.py first")
        return 1

    written = 0
    missing = []
    for meta_path in metas:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        uncertain = meta["rotation"]["status"] == "uncertain"
        candidate = IMAGES / f"{meta_path.stem}{'-uncertain' if uncertain else ''}.png"
        if not candidate.is_file():
            missing.append(candidate.name)
            continue

        image = Image.open(candidate)
        try:
            dest = OUT / f"{meta_path.stem}.png"
            draw_page(meta, image, dest)
            written += 1
            print(f"  {dest.name:56s} corr={meta['rotation']['correction_degrees']:3d} "
                  f"words={len(meta['words']):4d} {image.size[0]}x{image.size[1]}")
        finally:
            image.close()
            gc.collect()

    print(f"\n{written} overlays -> {OUT}")
    if missing:
        print(f"  {len(missing)} upright images missing; run export_rotated_images.py")
        for name in missing[:5]:
            print(f"    {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
