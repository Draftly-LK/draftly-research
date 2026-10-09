"""Make a presentation-safe crop of a real OCR region overlay."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "ocr-benchmark/renders/overlays/vision"
    / "vision-003-title-certificate-parcel-p1.png"
)
OUT = Path(__file__).with_name("assets") / "redacted-real-ocr-boxed-page.png"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    # The left panel shows confidence-coloured OCR blocks on one actual page.
    crop = source.crop((19, 113, 411, 678))
    redacted = crop.filter(ImageFilter.GaussianBlur(3.5))

    # Restore only the green region outlines, never the text beneath them.
    pixels = crop.load()
    mask = Image.new("L", crop.size, 0)
    mask_pixels = mask.load()
    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b = pixels[x, y]
            if g > 95 and g > r * 1.45 and g > b * 1.25:
                mask_pixels[x, y] = 255
    ink = Image.new("RGB", crop.size, "#148B4D")
    redacted.paste(ink, (0, 0), mask)

    scale = 2
    redacted = redacted.resize(
        (crop.width * scale, crop.height * scale), Image.Resampling.NEAREST
    )
    canvas = Image.new("RGB", (redacted.width + 64, redacted.height + 152), "#EEF3F8")
    draw = ImageDraw.Draw(canvas)
    draw.text((32, 18), "REAL OCR REGION OVERLAY", font=font(28), fill="#17345E")
    canvas.paste(redacted, (32, 65))
    draw.text(
        (32, canvas.height - 63),
        "Source text redacted; region boxes retained",
        font=font(22),
        fill="#17345E",
    )
    draw.text(
        (32, canvas.height - 34),
        "Illustrates detection, not field accuracy",
        font=font(20),
        fill="#55708D",
    )
    OUT.parent.mkdir(exist_ok=True)
    canvas.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
