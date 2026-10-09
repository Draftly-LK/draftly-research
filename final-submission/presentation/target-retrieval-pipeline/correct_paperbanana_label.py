"""Correct one hallucinated label in the PaperBanana reference image.

The image model omitted the word "No" before "invented citations". The
topology and all other labels remain from PaperBanana's second candidate.
"""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Draftly-Target-Hybrid-Retrieval-PaperBanana.png"
OUTPUT = HERE / "Draftly-Target-Hybrid-Retrieval-PaperBanana-reviewed.png"

image = cv2.imread(str(SOURCE))
if image is None:
    raise SystemExit(f"Missing source image: {SOURCE}")

# The lower two-line subtitle in the Sanitized rewrite panel is the only
# region touched. Inpainting removes its dark glyphs while retaining the
# generated panel's pale-blue texture.
mask = np.zeros(image.shape[:2], dtype=np.uint8)
x1, y1, x2, y2 = 715, 1133, 947, 1332
region = image[y1:y2, x1:x2]
dark = cv2.inRange(region, (0, 0, 0), (165, 165, 165))
mask[y1:y2, x1:x2] = cv2.dilate(dark, np.ones((5, 5), np.uint8))
clean = cv2.inpaint(image, mask, 7, cv2.INPAINT_TELEA)

pil = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(pil)
draw.rounded_rectangle(
    (699, 1128, 956, 1335),
    radius=18,
    fill=(238, 243, 253),
    outline=(197, 210, 235),
    width=2,
)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 35)
draw.multiline_text(
    (827, 1173),
    "Search terms only\nNo new citations",
    fill=(8, 13, 25),
    font=font,
    anchor="ma",
    align="center",
    spacing=8,
)
pil.save(OUTPUT)
print(OUTPUT)
