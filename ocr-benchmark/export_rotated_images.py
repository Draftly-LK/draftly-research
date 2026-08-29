"""Write upright page images using the corrections in extracted/final/.

    uv run python ocr-benchmark/export_rotated_images.py

Reads `rotation.correction_degrees` from each extracted/final/<page>.json and
applies it to the rendered page, writing the result to

    extracted/correctly-rotated-images/<original-name>.png

Rotation uses PIL's transpose operations rather than a general-angle rotate:
for exact multiples of 90 degrees transpose is lossless and resamples nothing,
so no glyph detail is lost. Note PIL's ROTATE_* constants are COUNTER-clockwise,
while `correction_degrees` is clockwise - the mapping below inverts that once,
in one place.

Pages marked `uncertain` are copied through unrotated and named accordingly,
rather than being guessed at.

PRIVACY: these are rendered client pages. The output directory sits under
extracted/, which must stay out of version control.
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import render

DPI = 200
VARIANT = "original"
CASE = "platform-case-001"

FINAL = Path(__file__).resolve().parent / "extracted" / "final"
OUT = Path(__file__).resolve().parent / "extracted" / "correctly-rotated-images"

# correction_degrees is CLOCKWISE; PIL's ROTATE_* are COUNTER-clockwise.
CLOCKWISE_TO_TRANSPOSE = {
    90: Image.Transpose.ROTATE_270,
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_90,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    case = next(c for c in config.case_dirs() if c.name == CASE)
    by_name = {doc.name: doc for doc in config.case_documents(case)}

    written = 0
    rotated = 0
    mismatches = []

    for meta_path in sorted(FINAL.glob("*-p*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        doc = by_name.get(meta["source_document"])
        if doc is None:
            print(f"  missing source for {meta_path.name}")
            continue

        page_no = meta["page_no"]
        correction = meta["rotation"]["correction_degrees"]
        status = meta["rotation"]["status"]

        page = render.render_doc(doc, dpi=DPI, variant=VARIANT, page_limit=page_no)[page_no - 1]
        try:
            image = page.image
            if status == "uncertain":
                out_image = image
                suffix = "-uncertain"
            elif correction:
                out_image = image.transpose(CLOCKWISE_TO_TRANSPOSE[correction])
                rotated += 1
                suffix = ""
            else:
                out_image = image
                suffix = ""

            dest = OUT / f"{meta_path.stem}{suffix}.png"
            out_image.save(dest)
            written += 1

            # The final JSON already recorded the post-correction dimensions;
            # if the saved image disagrees, one of the two is wrong.
            if (out_image.size != (meta["page_width"], meta["page_height"])
                    and status != "uncertain"):
                mismatches.append((dest.name, out_image.size,
                                   (meta["page_width"], meta["page_height"])))

            print(f"  {dest.name:56s} corr={correction:3d} {out_image.size[0]}x{out_image.size[1]}")
        finally:
            page.image.close()
            gc.collect()

    print(f"\n{written} images -> {OUT}")
    print(f"  {rotated} rotated, {written - rotated} already upright")
    if mismatches:
        print("\n  dimension mismatches against final JSON:")
        for name, got, expected in mismatches:
            print(f"    {name}: image {got} vs json {expected}")
    else:
        print("  all image dimensions match the corrected dimensions in final/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
