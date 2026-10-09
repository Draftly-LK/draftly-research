"""Trim redundant AI-added headings from the PaperBanana corpus figure.

The source image remains intact. The factual note removed here is placed in
the LaTeX caption, where it stays editable and accessible.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "syllabus-guided-corpus-paperbanana.png"
OUTPUT = HERE / "syllabus-guided-corpus-paper-ready.png"

image = Image.open(SOURCE).convert("RGB")
if image.size != (2752, 1536):
    raise ValueError(f"PaperBanana source dimensions changed: {image.size}")

# The generated footer has an unwanted literal "Footer:" prefix. Its full
# sentence belongs in the paper caption rather than in the graphic.
ImageDraw.Draw(image).rectangle((0, 1370, 1875, 1535), fill="white")

# Remove the redundant Stage 1/2/3 headings without touching the actual boxes.
image = image.crop((0, 155, 2752, 1510))
image.save(OUTPUT, optimize=True)
print(f"Saved {OUTPUT} ({image.width} x {image.height})")
