"""The one output shape every runner returns, so runs stay comparable.

BBOX CONVENTION — stated once, enforced here, assumed nowhere else:

    [x0, y0, x1, y1]
    normalized floats in [0, 1]
    origin TOP-LEFT, y increases DOWNWARD
    x0 <= x1 and y0 <= y1

Normalized because the DPI ablation renders the same page at 150/200/300/400 and
the boxes have to be comparable across all of them. Top-left because both
pypdfium2's `bitmap.to_pil()` and OpenCV are top-left, so no axis flips.

Every box carries `bbox` (in the frame the run actually read) *and* `bbox_original`
(in the unprocessed render's frame). Deskew and rotation change the geometry, so
without the second box a run-B box cannot be compared against a run-A box or
against any future human annotation. `bbox_apply` does that mapping.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, Field

BBox = tuple[float, float, float, float]
Affine = tuple[tuple[float, float, float], tuple[float, float, float]]

IDENTITY: Affine = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))

Script = Literal["sinhala", "latin", "tamil", "mixed", "unknown"]
BoxSource = Literal["surya-det", "rapidocr-det", "gemini-box", "crop", "synthetic", "none"]
ProvenanceLevel = Literal["none", "page", "region"]
RunStatus = Literal["completed", "partial", "skipped"]


# ── bbox helpers ─────────────────────────────────────────────────────────────
def clamp_bbox(bbox: Sequence[float]) -> BBox:
    """Order the corners and clip to [0, 1]. Models return inverted boxes."""
    x0, y0, x1, y1 = (float(v) for v in bbox)
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    f = lambda v: min(1.0, max(0.0, v))  # noqa: E731
    return (f(x0), f(y0), f(x1), f(y1))


def bbox_from_gemini(box: Sequence[float], scale: float = 1000.0) -> BBox:
    """Gemini 2D boxes are [ymin, xmin, ymax, xmax] as ints 0-1000.

    Transposed and divided here. The prompt asks for exactly this ordering so
    there is one place to get it wrong.
    """
    ymin, xmin, ymax, xmax = (float(v) for v in box)
    return clamp_bbox((xmin / scale, ymin / scale, xmax / scale, ymax / scale))


def bbox_from_pixels(box: Sequence[float], width: int, height: int) -> BBox:
    """Pixel [x0, y0, x1, y1] -> normalized. Used for Surya/RapidOCR."""
    x0, y0, x1, y1 = (float(v) for v in box)
    return clamp_bbox((x0 / width, y0 / height, x1 / width, y1 / height))


def bbox_from_polygon(points: Sequence[Sequence[float]], width: int, height: int) -> BBox:
    """Axis-aligned hull of a 4-point pixel polygon -> normalized."""
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return bbox_from_pixels((min(xs), min(ys), max(xs), max(ys)), width, height)


def bbox_to_pixels(bbox: Sequence[float], width: int, height: int) -> tuple[int, int, int, int]:
    """Normalized -> integer pixel box, for cropping and overlay drawing."""
    x0, y0, x1, y1 = clamp_bbox(bbox)
    return (round(x0 * width), round(y0 * height), round(x1 * width), round(y1 * height))


def bbox_apply(bbox: Sequence[float], affine: Affine) -> BBox:
    """Map a normalized box through a 2x3 affine given in NORMALIZED units.

    Applied to all four corners, then re-hulled, because rotation turns a
    rectangle into a quadrilateral.
    """
    x0, y0, x1, y1 = clamp_bbox(bbox)
    (a, b, c), (d, e, f) = affine
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    xs = [a * x + b * y + c for x, y in corners]
    ys = [d * x + e * y + f for x, y in corners]
    return clamp_bbox((min(xs), min(ys), max(xs), max(ys)))


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    """Intersection over union. 0.0 when they do not overlap."""
    ax0, ay0, ax1, ay1 = clamp_bbox(a)
    bx0, by0, bx1, by1 = clamp_bbox(b)
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union > 0 else 0.0


def bbox_contains(outer: Sequence[float], inner: Sequence[float], tol: float = 0.01) -> bool:
    """Whether `inner` sits inside `outer`, with a small tolerance."""
    ox0, oy0, ox1, oy1 = clamp_bbox(outer)
    ix0, iy0, ix1, iy1 = clamp_bbox(inner)
    return ix0 >= ox0 - tol and iy0 >= oy0 - tol and ix1 <= ox1 + tol and iy1 <= oy1 + tol


# ── models ───────────────────────────────────────────────────────────────────
class PageResult(BaseModel):
    page_no: int = Field(ge=1, description="1-based, = pypdfium index + 1")
    dpi: int
    render_variant: str = "original"
    width_px: int
    height_px: int
    text: str = ""
    engine: str = "none"
    engine_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    blank: bool = False
    transform_to_original: Affine = IDENTITY


class Block(BaseModel):
    block_id: str
    page_no: int = Field(ge=1)
    text: str = ""
    bbox: BBox
    bbox_original: BBox
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: BoxSource = "none"
    script: Script = "unknown"


class FieldValue(BaseModel):
    """`value` is ALWAYS a string or None.

    Never int, never float. `parcelNo` "0021" decoding to 21 is the single most
    likely silent bug in this benchmark, so the type is pinned here and the
    Gemini response schema declares every field as string-or-null.
    """

    key: str
    value: str | None = None
    page_no: int | None = None
    bbox: BBox | None = None
    bbox_original: BBox | None = None
    block_ids: list[str] = Field(default_factory=list)
    engine: str = "none"
    model_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    validator_ok: bool | None = None
    verbatim_in_page_text: bool | None = None
    box_contains_value: bool | None = None
    provenance_level: ProvenanceLevel = "none"
    agreement_sources: list[str] = Field(default_factory=list)


class Routing(BaseModel):
    kind: str = "other"
    kind_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    kind_source: str = "none"
    page_kinds: dict[str, str] = Field(default_factory=dict)
    outcome: Literal["extracted", "manual_review", "unsupported"] = "extracted"
    reasons: list[str] = Field(default_factory=list)


class ProviderMetadata(BaseModel):
    engines: list[str] = Field(default_factory=list)
    models: dict[str, str] = Field(default_factory=dict)
    temperature: float = 0.0
    calls: int = 0
    http_attempts: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: dict[str, float] = Field(default_factory=dict)
    estimated_usd: float = 0.0
    errors: list[str] = Field(default_factory=list)


class AdapterOutput(BaseModel):
    schema_version: str = "1.0"
    run_id: str
    variant_id: str
    doc_id: str
    doc_sha256: str = ""
    pages: list[PageResult] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)
    fields: list[FieldValue] = Field(default_factory=list)
    routing: Routing = Field(default_factory=Routing)
    provider_metadata: ProviderMetadata = Field(default_factory=ProviderMetadata)

    def page_text(self, page_no: int) -> str:
        for page in self.pages:
            if page.page_no == page_no:
                return page.text
        return ""

    def all_text(self) -> str:
        return "\n".join(page.text for page in self.pages)


# ── fingerprints ─────────────────────────────────────────────────────────────
def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def dataset_fingerprint(paths: Sequence[Path]) -> str:
    """Fingerprint the corpus without embedding any of its content."""
    parts = [
        {"name": p.name, "size": p.stat().st_size, "sha256": sha256_file(p)}
        for p in sorted(paths, key=lambda p: p.name)
    ]
    return sha256_text(json.dumps(parts, sort_keys=True))
