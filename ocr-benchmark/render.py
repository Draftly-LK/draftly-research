"""Page rendering, preprocessing variants, crops, and the synthetic fixture.

The render loop is copied from scripts/convert_to_text.py:ocr_pdf, including the
explicit `del image, bitmap, page; gc.collect()`. That teardown is not
decoration: scripts/reextract_failed.py exists because the large bundles threw
bad_alloc, and the wider corpus includes a 168-page scan.

Every preprocessing variant returns the image AND a normalized 2x3 affine mapping
its frame back to the original render's frame, so boxes found on a deskewed page
remain comparable with boxes found on the raw page.
"""

from __future__ import annotations

import gc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import cv2
import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

import config
from contract import IDENTITY, Affine, BBox, bbox_to_pixels

VariantFn = Callable[[Image.Image], tuple[Image.Image, Affine]]


@dataclass
class RenderedPage:
    page_no: int
    image: Image.Image
    dpi: int
    variant: str
    transform_to_original: Affine
    blank: bool
    # Recorded, not hidden: preprocessing decisions that could corrupt a run.
    rotation_applied: int = 0
    rotation_confidence: float = 1.0
    skew_corrected: float = 0.0

    @property
    def size(self) -> tuple[int, int]:
        return self.image.size


# ── affine plumbing ──────────────────────────────────────────────────────────
def _pixel_affine_to_normalized(
    matrix: np.ndarray, src_size: tuple[int, int], dst_size: tuple[int, int]
) -> Affine:
    """Convert a 2x3 pixel-space affine into normalized units.

    `matrix` maps a pixel in `src_size` (the processed frame) to a pixel in
    `dst_size` (the original frame).
    """
    sw, sh = src_size
    dw, dh = dst_size
    (a, b, c), (d, e, f) = matrix[0], matrix[1]
    return (
        (a * sw / dw, b * sh / dw, c / dw),
        (d * sw / dh, e * sh / dh, f / dh),
    )


def _rotation_matrix(angle: float, size: tuple[int, int]) -> np.ndarray:
    w, h = size
    return cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)


def _invert(matrix: np.ndarray) -> np.ndarray:
    return cv2.invertAffineTransform(matrix)


# ── rendering ────────────────────────────────────────────────────────────────
def image_has_content(image: Image.Image) -> bool:
    """Blank-page skip, thresholds from scripts/convert_to_text.py:image_has_content."""
    gray = np.asarray(image.convert("L"))
    if not gray.size:
        return False
    ink_ratio = float(np.mean(gray < 235))
    return ink_ratio >= 0.004 and float(np.std(gray)) >= 8.0


def cache_path(doc_id: str, page_no: int, dpi: int, variant: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in doc_id)
    return config.RENDERS / safe / f"p{page_no:04d}@{dpi}-{variant}.png"


def render_doc(
    pdf_path: Path,
    dpi: int = config.DEFAULT_DPI,
    variant: str = "original",
    page_limit: int | None = None,
    use_cache: bool = True,
) -> list[RenderedPage]:
    """Render every page of a PDF at `dpi`, then apply the named variant.

    Pages are cached as PNG so no run re-renders. The affine is recomputed
    cheaply on a cache hit rather than stored, since it depends only on the
    variant and the image size.
    """
    if pdf_path.suffix.lower() != ".pdf":
        return _render_image(pdf_path, dpi, variant, use_cache)

    doc_id = pdf_path.name
    out: list[RenderedPage] = []
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        total = len(pdf)
        count = total if page_limit is None else min(total, page_limit)
        for index in range(count):
            page_no = index + 1
            dest = cache_path(doc_id, page_no, dpi, variant)
            cached = _load_cached(dest, page_no, dpi, variant) if use_cache else None
            if cached is not None:
                out.append(cached)
                continue

            page = pdf[index]
            bitmap = page.render(scale=dpi / 72.0)
            raw = bitmap.to_pil().convert("RGB")
            blank = not image_has_content(raw)
            rotation, confidence = detect_orientation(raw)
            skew = estimate_skew(raw) if variant in ("deskew", "full") else 0.0
            processed, affine = apply_variant(raw, variant)
            rendered = RenderedPage(
                page_no=page_no,
                image=processed,
                dpi=dpi,
                variant=variant,
                transform_to_original=affine,
                blank=blank,
                rotation_applied=rotation if variant != "original" else 0,
                rotation_confidence=confidence,
                skew_corrected=skew,
            )
            _save_cached(dest, rendered)
            out.append(rendered)
            del raw, bitmap, page
            gc.collect()
    finally:
        pdf.close()
    return out


def _render_image(
    path: Path, dpi: int, variant: str, use_cache: bool
) -> list[RenderedPage]:
    """A photographed or scanned page that is already an image.

    Roughly a third of the corpus is JPEG photos of documents rather than PDFs,
    so they are first-class inputs. There is no PDF page geometry to scale, so
    `dpi` only records which cache slot this is; the pixels are whatever the
    camera produced.
    """
    dest = cache_path(path.name, 1, dpi, variant)
    cached = _load_cached(dest, 1, dpi, variant) if use_cache else None
    if cached is not None:
        return [cached]

    raw = Image.open(path).convert("RGB")
    blank = not image_has_content(raw)
    rotation, confidence = detect_orientation(raw)
    skew = estimate_skew(raw) if variant in ("deskew", "full") else 0.0
    processed, affine = apply_variant(raw, variant)
    page = RenderedPage(
        page_no=1,
        image=processed,
        dpi=dpi,
        variant=variant,
        transform_to_original=affine,
        blank=blank,
        rotation_applied=rotation if variant != "original" else 0,
        rotation_confidence=confidence,
        skew_corrected=skew,
    )
    _save_cached(dest, page)
    return [page]


def _sidecar(dest: Path) -> Path:
    return dest.with_suffix(".json")


def _save_cached(dest: Path, page: RenderedPage) -> None:
    """Cache the image plus the metadata that cannot be recovered from it.

    The affine matters: a deskewed page's boxes are only comparable with the
    original frame through it, and the skew angle is measured from the raw page,
    which the cached result no longer contains.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    page.image.save(dest)
    _sidecar(dest).write_text(
        json.dumps(
            {
                "page_no": page.page_no,
                "dpi": page.dpi,
                "variant": page.variant,
                "transform_to_original": [list(page.transform_to_original[0]),
                                          list(page.transform_to_original[1])],
                "blank": page.blank,
                "rotation_applied": page.rotation_applied,
                "rotation_confidence": page.rotation_confidence,
                "skew_corrected": page.skew_corrected,
            }
        ),
        encoding="utf-8",
    )


def _load_cached(dest: Path, page_no: int, dpi: int, variant: str) -> RenderedPage | None:
    side = _sidecar(dest)
    if not (dest.is_file() and side.is_file()):
        return None
    try:
        meta = json.loads(side.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    rows = meta.get("transform_to_original") or [[1, 0, 0], [0, 1, 0]]
    affine: Affine = (tuple(float(v) for v in rows[0]), tuple(float(v) for v in rows[1]))
    return RenderedPage(
        page_no=page_no,
        image=Image.open(dest),
        dpi=dpi,
        variant=variant,
        transform_to_original=affine,
        blank=bool(meta.get("blank", False)),
        rotation_applied=int(meta.get("rotation_applied", 0)),
        rotation_confidence=float(meta.get("rotation_confidence", 1.0)),
        skew_corrected=float(meta.get("skew_corrected", 0.0)),
    )


# ── preprocessing primitives ─────────────────────────────────────────────────
def _to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def _to_pil(array: np.ndarray) -> Image.Image:
    if array.ndim == 2:
        return Image.fromarray(array)
    return Image.fromarray(cv2.cvtColor(array, cv2.COLOR_BGR2RGB))


def _ink_mask(image: Image.Image, max_side: int = 800) -> np.ndarray:
    """Downsampled binary ink mask, for cheap angle search."""
    gray = image.convert("L")
    scale = max_side / max(gray.size)
    if scale < 1.0:
        gray = gray.resize((max(1, int(gray.width * scale)), max(1, int(gray.height * scale))))
    array = np.asarray(gray)
    mask = cv2.threshold(array, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return (mask > 0).astype(np.float32)


def _profile_score(mask: np.ndarray, angle: float) -> float:
    """Sharpness of the horizontal projection profile at a candidate angle.

    Upright text produces alternating dense rows and empty gutters, so the
    row-sum profile has large row-to-row swings. Skewed text smears them out.
    """
    h, w = mask.shape
    matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    rotated = cv2.warpAffine(mask, matrix, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    profile = rotated.sum(axis=1)
    return float(np.sum(np.diff(profile) ** 2))


def estimate_skew(image: Image.Image, max_angle: float = 15.0) -> float:
    """Skew angle in degrees, by maximizing projection-profile sharpness.

    Preferred over minAreaRect: on a sparse page of short text lines the
    minimum-area rect tracks the shape of the text block rather than the
    baseline angle, and its OpenCV angle convention wraps in a way that is easy
    to get wrong. The profile search is directly measuring what we care about.

    Returns the angle to pass to a counter-clockwise rotation to make the page
    upright. 0.0 when the page has too little ink to judge.
    """
    mask = _ink_mask(image)
    if mask.sum() < 50:
        return 0.0
    coarse = max(
        np.arange(-max_angle, max_angle + 0.5, 1.0),
        key=lambda a: _profile_score(mask, float(a)),
    )
    fine = max(
        np.arange(coarse - 1.0, coarse + 1.01, 0.1),
        key=lambda a: _profile_score(mask, float(a)),
    )
    angle = float(fine)
    return angle if abs(angle) <= max_angle else 0.0


def deskew(image: Image.Image) -> tuple[Image.Image, Affine]:
    """Rotate the page upright by its measured skew, preserving canvas size."""
    angle = estimate_skew(image)
    if abs(angle) < 0.1:
        return image, IDENTITY
    size = image.size
    forward = _rotation_matrix(angle, size)
    array = cv2.warpAffine(
        _to_cv(image), forward, size,
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
    )
    affine = _pixel_affine_to_normalized(_invert(forward), size, size)
    return _to_pil(array), affine


ROTATE_MARGIN = 1.35


def detect_orientation(image: Image.Image) -> tuple[int, float]:
    """Return (degrees_to_rotate, confidence_ratio).

    Exposed separately so the decision is auditable instead of silent. Diagram
    and survey-plan pages carry text at several angles, so this heuristic is
    genuinely unreliable on them; the ratio is recorded on every page and the
    notebook surfaces the borderline cases for a human to spot-check against the
    `correctRotation` routing labels.
    """
    mask = _ink_mask(image)
    if mask.sum() < 50:
        return 0, 1.0
    upright = _profile_score(mask, 0.0)
    sideways = _profile_score(np.ascontiguousarray(mask.T), 0.0)
    ratio = sideways / upright if upright > 0 else 1.0
    return (90 if ratio > ROTATE_MARGIN else 0), ratio


def rotate_upright(image: Image.Image, margin: float = ROTATE_MARGIN) -> tuple[Image.Image, Affine]:
    """Coarse 90-degree orientation fix, deliberately conservative.

    Compares projection-profile sharpness upright against the same page turned
    90 degrees, and only rotates when the sideways reading is clearly better by
    `margin`. Being timid is the right bias: most scans are already portrait, and
    wrongly rotating a correct page corrupts every downstream run, whereas
    leaving a sideways page alone merely costs accuracy on that page.

    Only distinguishes portrait from landscape. Detecting a 180-degree flip needs
    a text-direction signal, so it is left to the routing labels.
    """
    degrees, _ratio = detect_orientation(image)
    if degrees == 0:
        return image, IDENTITY

    w, h = image.size
    rotated = image.transpose(Image.Transpose.ROTATE_270)  # 90 deg clockwise
    # Processed pixel (x, y) came from original pixel (y, W_processed - x).
    forward = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, float(rotated.size[0])]])
    affine = _pixel_affine_to_normalized(forward, rotated.size, (w, h))
    return rotated, affine


def denoise(image: Image.Image) -> tuple[Image.Image, Affine]:
    gray = np.asarray(image.convert("L"))
    return Image.fromarray(cv2.fastNlMeansDenoising(gray, None, 7, 7, 21)), IDENTITY


def boost_contrast(image: Image.Image) -> tuple[Image.Image, Affine]:
    gray = np.asarray(image.convert("L"))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return Image.fromarray(clahe.apply(gray)), IDENTITY


def binarize(image: Image.Image) -> tuple[Image.Image, Affine]:
    gray = np.asarray(image.convert("L"))
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    return Image.fromarray(binary), IDENTITY


def _compose(*steps: VariantFn) -> VariantFn:
    def run(image: Image.Image) -> tuple[Image.Image, Affine]:
        current, affine = image, IDENTITY
        for step in steps:
            current, step_affine = step(current)
            affine = _compose_affine(step_affine, affine)
        return current, affine

    return run


def _compose_affine(inner: Affine, outer: Affine) -> Affine:
    """Compose two normalized affines: apply `inner` then `outer`."""
    if inner == IDENTITY:
        return outer
    if outer == IDENTITY:
        return inner
    a = np.array([list(inner[0]), list(inner[1]), [0.0, 0.0, 1.0]])
    b = np.array([list(outer[0]), list(outer[1]), [0.0, 0.0, 1.0]])
    m = b @ a
    return ((m[0][0], m[0][1], m[0][2]), (m[1][0], m[1][1], m[1][2]))


VARIANTS: dict[str, VariantFn] = {
    "original": lambda img: (img, IDENTITY),
    "rotated": rotate_upright,
    "deskew": _compose(rotate_upright, deskew),
    "full": _compose(rotate_upright, deskew, denoise, boost_contrast, binarize),
}


def apply_variant(image: Image.Image, variant: str) -> tuple[Image.Image, Affine]:
    if variant not in VARIANTS:
        raise KeyError(f"unknown variant {variant!r}; known: {sorted(VARIANTS)}")
    return VARIANTS[variant](image)


# ── crops ────────────────────────────────────────────────────────────────────
def crop(image: Image.Image, bbox: Sequence[float], pad: float = 0.02) -> Image.Image:
    """Crop a normalized bbox with padding, for critical-field re-reading.

    Padding is in normalized units and clipped at the page edge. Fine Sinhala
    diacritics sit just outside a tight box, so a too-tight crop loses them.
    """
    w, h = image.size
    x0, y0, x1, y1 = bbox
    padded = (max(0.0, x0 - pad), max(0.0, y0 - pad), min(1.0, x1 + pad), min(1.0, y1 + pad))
    px = bbox_to_pixels(padded, w, h)
    if px[2] - px[0] < 2 or px[3] - px[1] < 2:
        return image
    return image.crop(px)


# ── synthetic fixture ────────────────────────────────────────────────────────
# Invented values. They mirror the SHAPE of real fields — digit counts, leading
# zeros, the "/=" money suffix, NIC formats — because the tests depend on that
# shape, but every value here is fabricated.
#
# An earlier version of this list used real numbers from a case manifest for
# realism. That was a mistake: this file is tracked, so it put client values in
# git. A synthetic fixture that contains real data is not a synthetic fixture.
# There is a test asserting these do not collide with the labelled corpus.
SYNTHETIC_LINES: list[tuple[str, str]] = [
    ("titleCertificateNo", "00011122233"),
    ("cadastralMapNo", "999001"),
    ("blockNo", "07"),
    ("parcelNo", "0099"),
    ("extent", "0.0777 ha"),
    ("consideration", "Rs.1,234,500/="),
    ("transfereeNic", "199912345678"),
    ("holderDateOfBirth", "1999-01-02"),
]


def synthetic_page(
    width: int = 1200, height: int = 1600, lines: Sequence[tuple[str, str]] | None = None
) -> tuple[Image.Image, list[dict[str, object]]]:
    """A page with known text at known boxes, plus its own ground truth.

    This is the keystone of the offline verification path: with perfect labels,
    any deviation from 1.00 accuracy or 0.00 CER is a harness bug rather than a
    model result. Latin-only, because it validates the measurement chain, not
    Sinhala recognition.
    """
    rows = list(lines or SYNTHETIC_LINES)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _fixture_font()
    truth: list[dict[str, object]] = []
    y = 120
    step = (height - 240) // max(1, len(rows))
    for key, value in rows:
        label = f"{key}: {value}"
        x = 90
        box = draw.textbbox((x, y), label, font=font)
        draw.text((x, y), label, fill="black", font=font)
        # The value sits after the "key: " prefix; box just the value.
        prefix_w = draw.textlength(f"{key}: ", font=font)
        vx0 = x + prefix_w
        vx1 = box[2]
        truth.append(
            {
                "key": key,
                "verbatimValue": value,
                "page": 1,
                "bbox": (vx0 / width, box[1] / height, vx1 / width, box[3] / height),
                "text": label,
            }
        )
        # Filler beneath each row, so the page carries enough ink to look like a
        # real scan to image_has_content and to the skew estimator. Not part of
        # the ground truth.
        draw.text(
            (x, y + step // 2),
            "the quick brown fox jumps over the lazy dog 0123456789",
            fill="black",
            font=font,
        )
        y += step
    return image, truth


def _fixture_font():
    """Largest default font available, so the fixture is not pathologically sparse."""
    try:
        from PIL import ImageFont

        return ImageFont.load_default(size=30)
    except (ImportError, AttributeError, TypeError):  # pragma: no cover - old Pillow
        from PIL import ImageFont

        return ImageFont.load_default()


def synthetic_doc(pages: int = 2) -> list[tuple[Image.Image, list[dict[str, object]]]]:
    """A multi-page synthetic document; page 2 onward repeats with a shifted split."""
    half = len(SYNTHETIC_LINES) // 2
    chunks = [SYNTHETIC_LINES[:half], SYNTHETIC_LINES[half:]]
    return [synthetic_page(lines=chunks[i % len(chunks)]) for i in range(pages)]
