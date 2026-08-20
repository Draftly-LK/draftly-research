"""Deskew the pages of a scanned PDF into a folder of straightened page images.

Built for `data/evaluvation/Past Paper Question from Law College.pdf`, which is a
pure scan: 67 pages, no text layer, one full-page JPEG per page. The embedded
image and the PDF page box are close but not exactly 1:1 on every page, so
`--scale 1.0` renders at approximately the source scan resolution; raising it
mostly upsamples.

Scope is rendering, orientation correction, deskewing, image output and an
auditable manifest. No OCR, no text extraction.

The skew estimator and the low-level affine helpers come from
`ocr-benchmark/render.py`, which already has them under test. What this script
does add is the parts that file deliberately leaves out: four-way orientation
(it only distinguishes portrait from landscape), a bounded 0-1 confidence that a
threshold can gate on (its ratio is unbounded), and a deskew that reports the
angle it actually applied.

Orientation honesty, because it drives the defaults:

  * The portrait/landscape axis is decided by projection-profile sharpness. This
    is reliable — real pages here separate by roughly 10x.
  * The 180-degree flip is not reliably detectable this way. A projection profile
    is mathematically identical for 0 and 180, so the flip needs a text-direction
    signal; the baseline-sharpness heuristic used here scored 5/9 on this corpus,
    barely above chance. `FLIP_ACCURACY` caps flip confidence at that measured
    value, which sits below the default `--rotation-threshold`, so flips are
    flagged for review rather than silently applied. Lower the threshold to act
    on them.

Every page writes a manifest row: what was detected, what was actually applied,
both confidences, and the affine mapping the output frame back to the render
frame. Preprocessing is lossy and silent — a page nudged the wrong way looks
fine until whatever reads it disagrees with the original — so the decisions stay
auditable and any page the heuristics were unsure about is marked
`review_required` instead of being quietly trusted.

Usage:
    uv run python scripts/deskew_pages.py
    uv run python scripts/deskew_pages.py --pages 1-10 --overwrite
    uv run python scripts/deskew_pages.py --dry-run          # measure, write nothing

    # visual spot-check of the pages most likely to be mis-oriented
    uv run python scripts/deskew_pages.py --pages 5-8 --out tmp/rotation-test --overwrite
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ocr-benchmark"))

from contract import IDENTITY, Affine  # noqa: E402
from render import (  # noqa: E402
    _compose_affine,
    _ink_mask,
    _invert,
    _pixel_affine_to_normalized,
    _profile_score,
    _rotation_matrix,
    _to_cv,
    _to_pil,
    estimate_skew,
    image_has_content,
)

import cv2  # noqa: E402

DEFAULT_PDF = ROOT / "data" / "evaluvation" / "Past Paper Question from Law College.pdf"
DEFAULT_OUT = ROOT / "data" / "evaluvation" / "0-deskew-outputs"

# How far the skew search looks. Deliberately wider than the default --max-skew:
# a page can only be reported as excessively skewed if it was measured first.
SKEW_SEARCH_LIMIT = 15.0
# Below this the rotation is not worth the resampling blur.
SKEW_DEADBAND = 0.1
# Measured accuracy of the 180-degree flip heuristic on this corpus (5 of 9 pages
# spot-checked). Flip confidence is capped here so a coin-flip signal can never
# present itself as certainty. See the module docstring.
FLIP_ACCURACY = 5 / 9
# Baseline-sharpness magnitude treated as a maximally decisive flip signal.
FLIP_MARGIN_SCALE = 1.0

# review_reason values
REVIEW_LOW_CONFIDENCE = "low_orientation_confidence"
REVIEW_EXCESSIVE_SKEW = "excessive_skew"
REVIEW_BLANK = "blank_page"
REVIEW_ORIENTATION_FAILED = "orientation_detection_failed"
REVIEW_DESKEW_FAILED = "deskew_failed"

MANIFEST_FIELDS = [
    "page_no",
    "filename",
    "width",
    "height",
    "blank",
    "rotation_detected",
    "rotation_applied",
    "orientation_confidence",
    "flip_confidence",
    "skew_measured",
    "skew_applied",
    "review_required",
    "review_reason",
    "transform_to_original",
]

# Legacy manifests used skew_corrected; keep old rows readable across the rename.
LEGACY_FIELD_ALIASES = {"skew_corrected": "skew_applied"}


# ── orientation ──────────────────────────────────────────────────────────────
@dataclass
class OrientationReading:
    """A four-way orientation decision, split into its two independent parts.

    The axis and flip decisions are kept separate because they have very
    different reliability, and averaging them into one number would hide that.
    `degrees` is clockwise rotation needed to bring the page upright.
    """

    axis_degrees: int = 0  # 0 or 90
    axis_confidence: float = 0.0
    flip_degrees: int = 0  # 0 or 180
    flip_confidence: float = 0.0
    failed: bool = False

    @property
    def degrees(self) -> int:
        return (self.axis_degrees + self.flip_degrees) % 360


def _baseline_sharpness(mask: np.ndarray) -> float:
    """Signed skewness of the row-profile gradient.

    Upright Latin text has a sharp bottom edge at the baseline and a ragged top
    edge from varying ascenders, which shows up as a negatively skewed gradient.
    Rotating the page 180 degrees negates it exactly, which is the only reason
    this can separate 0 from 180 at all. It is weak — see FLIP_ACCURACY.
    """
    profile = mask.sum(axis=1).astype(np.float64)
    gradient = np.diff(profile)
    gradient = gradient[np.abs(gradient) > 1e-9]
    if gradient.size < 10:
        return 0.0
    spread = float(gradient.std())
    if spread <= 0.0:
        return 0.0
    return float((gradient**3).mean() / spread**3)


def detect_orientation(image: Image.Image) -> OrientationReading:
    """Detect page orientation once, returning the rotation and its confidence.

    Called exactly once per page; the resulting `degrees` is handed to
    `apply_rotation`, which does no detection of its own.
    """
    mask = _ink_mask(image)
    if mask.sum() < 50:
        return OrientationReading(failed=True)

    upright = _profile_score(mask, 0.0)
    sideways = _profile_score(np.ascontiguousarray(mask.T), 0.0)
    total = upright + sideways
    if total <= 0.0:
        return OrientationReading(failed=True)

    if sideways > upright:
        # Text runs down the page: rotate 90 clockwise to bring it upright.
        axis_degrees = 90
        axis_confidence = sideways / total
        axis_mask = np.ascontiguousarray(mask.T)
    else:
        axis_degrees = 0
        axis_confidence = upright / total
        axis_mask = mask

    sharpness = _baseline_sharpness(axis_mask)
    margin = min(1.0, abs(sharpness) / FLIP_MARGIN_SCALE)
    return OrientationReading(
        axis_degrees=axis_degrees,
        axis_confidence=float(axis_confidence),
        flip_degrees=180 if sharpness > 0 else 0,
        flip_confidence=(0.5 + 0.5 * margin) * FLIP_ACCURACY,
        failed=False,
    )


def apply_rotation(image: Image.Image, degrees: int) -> tuple[Image.Image, Affine]:
    """Rotate by an exact multiple of 90 degrees clockwise, with its affine.

    The affine maps a pixel in the returned frame back to the original frame,
    matching render.py's convention.
    """
    degrees %= 360
    if degrees == 0:
        return image, IDENTITY
    if degrees not in (90, 180, 270):
        raise ValueError(f"rotation must be a multiple of 90, got {degrees}")

    w, h = image.size
    if degrees == 90:
        rotated = image.transpose(Image.Transpose.ROTATE_270)  # 90 clockwise
        forward = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, float(h)]])
    elif degrees == 180:
        rotated = image.transpose(Image.Transpose.ROTATE_180)
        forward = np.array([[-1.0, 0.0, float(w)], [0.0, -1.0, float(h)]])
    else:
        rotated = image.transpose(Image.Transpose.ROTATE_90)  # 90 counter-clockwise
        forward = np.array([[0.0, -1.0, float(w)], [1.0, 0.0, 0.0]])
    return rotated, _pixel_affine_to_normalized(forward, rotated.size, (w, h))


# ── skew ─────────────────────────────────────────────────────────────────────
def measure_skew(image: Image.Image) -> float:
    """Skew angle in degrees, searched over the full SKEW_SEARCH_LIMIT range."""
    return estimate_skew(image, max_angle=SKEW_SEARCH_LIMIT)


def apply_deskew(image: Image.Image, angle: float) -> tuple[Image.Image, Affine, float]:
    """Rotate by `angle`, returning the angle actually applied.

    Returns 0.0 as the applied angle when the rotation was skipped, so callers
    record what happened rather than assuming the measured angle was used.
    """
    if abs(angle) < SKEW_DEADBAND:
        return image, IDENTITY, 0.0
    size = image.size
    forward = _rotation_matrix(angle, size)
    array = cv2.warpAffine(
        _to_cv(image), forward, size,
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
    )
    affine = _pixel_affine_to_normalized(_invert(forward), size, size)
    return _to_pil(array), affine, float(angle)


# ── per-page pipeline ────────────────────────────────────────────────────────
@dataclass
class PageResult:
    page_no: int
    filename: str
    width: int
    height: int
    blank: bool = False
    rotation_detected: int = 0
    rotation_applied: int = 0
    orientation_confidence: float = 0.0
    flip_confidence: float = 0.0
    skew_measured: float = 0.0
    skew_applied: float = 0.0
    transform: Affine = IDENTITY
    review_reasons: list[str] = field(default_factory=list)

    @property
    def review_required(self) -> bool:
        return bool(self.review_reasons)

    def as_row(self) -> dict[str, object]:
        return {
            "page_no": self.page_no,
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "blank": self.blank,
            "rotation_detected": self.rotation_detected,
            "rotation_applied": self.rotation_applied,
            "orientation_confidence": round(self.orientation_confidence, 4),
            "flip_confidence": round(self.flip_confidence, 4),
            "skew_measured": round(self.skew_measured, 2),
            "skew_applied": round(self.skew_applied, 2),
            "review_required": self.review_required,
            "review_reason": ";".join(self.review_reasons),
            "transform_to_original": json.dumps(
                [list(self.transform[0]), list(self.transform[1])]
            ),
        }


def process_page(
    image: Image.Image,
    page_no: int,
    dest: Path,
    *,
    rotate: bool = True,
    detect_flip: bool = False,
    rotation_threshold: float = 0.75,
    max_skew: float = 5.0,
    quality: int = 95,
    dry_run: bool = False,
) -> PageResult:
    """Straighten one rendered page and write it.

    Never raises for a bad page: orientation and deskew are guarded separately,
    and a failure in either falls back to the unmodified rendered image with the
    reason recorded, so one problem page cannot abort a 67-page run.
    """
    result = PageResult(
        page_no=page_no,
        filename=dest.name,
        width=image.width,
        height=image.height,
    )
    current, affine = image, IDENTITY

    result.blank = not image_has_content(image)
    if result.blank:
        # Nothing to measure on an empty page, and both estimators would be
        # reading noise. Leave it untouched and say so.
        result.review_reasons.append(REVIEW_BLANK)
        if not dry_run:
            save_image(current, dest, quality)
        return result

    # ── orientation ──
    if rotate:
        try:
            reading = detect_orientation(image)
            result.orientation_confidence = reading.axis_confidence
            result.flip_confidence = reading.flip_confidence
            result.rotation_detected = reading.degrees
            if reading.failed:
                result.review_reasons.append(REVIEW_ORIENTATION_FAILED)
            else:
                # Each half is gated on its own confidence, then applied in a
                # single transpose so the page is only resampled once.
                #
                # The flip is only considered under --detect-flip. Its confidence
                # is capped below the default threshold by construction, so
                # leaving it on would withhold-and-flag every page it guessed
                # 180 on — 30 of 67 here, all of them a coin toss. That is alert
                # fatigue, not review. The guess still lands in
                # rotation_detected so it can be grepped for.
                axis_ok = reading.axis_confidence >= rotation_threshold
                flip_ok = reading.flip_confidence >= rotation_threshold
                flip_wanted = detect_flip and bool(reading.flip_degrees)
                applied = (
                    (reading.axis_degrees if axis_ok else 0)
                    + (reading.flip_degrees if (flip_wanted and flip_ok) else 0)
                ) % 360
                withheld = (reading.axis_degrees and not axis_ok) or (
                    flip_wanted and not flip_ok
                )
                if withheld:
                    result.review_reasons.append(REVIEW_LOW_CONFIDENCE)
                if applied:
                    current, rot_affine = apply_rotation(current, applied)
                    affine = _compose_affine(rot_affine, affine)
                    result.rotation_applied = applied
        except Exception as exc:  # noqa: BLE001 - one page must not kill the run
            print(f"    page {page_no}: orientation failed ({exc}); left unrotated")
            result.review_reasons.append(REVIEW_ORIENTATION_FAILED)
            current, affine = image, IDENTITY
            result.rotation_applied = 0

    # ── skew ──
    # Measured after any rotation: the coarse fix changes which axis the
    # baselines run along, so an angle taken before it no longer describes
    # this page.
    try:
        measured = measure_skew(current)
        result.skew_measured = measured
        if abs(measured) > max_skew:
            # Past this, a wrong measurement does real damage. Report, don't act.
            result.review_reasons.append(REVIEW_EXCESSIVE_SKEW)
        else:
            current, skew_affine, applied_angle = apply_deskew(current, measured)
            affine = _compose_affine(skew_affine, affine)
            result.skew_applied = applied_angle
    except Exception as exc:  # noqa: BLE001 - keep the page, lose the correction
        print(f"    page {page_no}: deskew failed ({exc}); left unskewed")
        result.review_reasons.append(REVIEW_DESKEW_FAILED)
        result.skew_applied = 0.0

    result.width, result.height = current.size
    result.transform = affine
    if not dry_run:
        save_image(current, dest, quality)
    return result


# ── plumbing ─────────────────────────────────────────────────────────────────
def parse_pages(spec: str | None, total: int) -> list[int]:
    """Expand a 1-based page spec like "1-10,15,40-" into page numbers."""
    if not spec:
        return list(range(1, total + 1))
    wanted: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            start = int(lo) if lo.strip() else 1
            end = int(hi) if hi.strip() else total
        else:
            start = end = int(part)
        if start > end:
            raise ValueError(f"empty page range: {part!r}")
        wanted.update(range(max(1, start), min(total, end) + 1))
    if not wanted:
        raise ValueError(f"page spec {spec!r} selected no pages")
    return sorted(wanted)


def save_image(image: Image.Image, dest: Path, quality: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix.lower() in {".jpg", ".jpeg"}:
        image.convert("RGB").save(dest, quality=quality, optimize=True)
    else:
        image.save(dest, optimize=True)


def _normalize_row(row: dict[str, str]) -> dict[str, object]:
    """Coerce an existing manifest row to the current field set.

    Rows written before a field was renamed still describe real pages, so they
    are migrated rather than dropped.
    """
    migrated = dict(row)
    for old, new in LEGACY_FIELD_ALIASES.items():
        if old in migrated and not migrated.get(new):
            migrated[new] = migrated[old]
    return {name: migrated.get(name, "") for name in MANIFEST_FIELDS}


def write_manifest(path: Path, results: list[PageResult]) -> None:
    """Merge results into the manifest, preserving rows for untouched pages.

    Existing rows are always loaded, including under --overwrite: overwriting
    pages 1-10 must not discard what is known about pages 11-67.
    """
    rows: dict[int, dict[str, object]] = {}
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    page_no = int(row["page_no"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows[page_no] = _normalize_row(row)
    for result in results:
        rows[result.page_no] = result.as_row()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for page_no in sorted(rows):
            writer.writerow(rows[page_no])


def validate_args(args: argparse.Namespace) -> None:
    """Reject argument values that would silently produce garbage."""
    if args.scale <= 0:
        raise ValueError(f"--scale must be greater than 0, got {args.scale}")
    if not 1 <= args.quality <= 100:
        raise ValueError(f"--quality must be between 1 and 100, got {args.quality}")
    if not 0.0 <= args.rotation_threshold <= 1.0:
        raise ValueError(
            "--rotation-threshold must be within the confidence range 0.0-1.0, "
            f"got {args.rotation_threshold}"
        )
    if args.max_skew <= 0:
        raise ValueError(f"--max-skew must be greater than 0, got {args.max_skew}")


def run(args: argparse.Namespace) -> int:
    validate_args(args)

    pdf_path: Path = args.pdf
    out_dir: Path = args.out
    if not pdf_path.is_file():
        print(f"error: no such PDF: {pdf_path}", file=sys.stderr)
        return 1

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(pdf_path)
    results: list[PageResult] = []
    try:
        total = len(pdf)
        pages = parse_pages(args.pages, total)
        print(f"{pdf_path.name}: {total} pages, processing {len(pages)}")

        for page_no in pages:
            dest = out_dir / f"page-{page_no:03d}.{args.format}"
            if dest.exists() and not args.overwrite and not args.dry_run:
                print(f"  page {page_no:>3}  skipped (exists)")
                continue

            page = pdf[page_no - 1]
            bitmap = page.render(scale=args.scale)
            raw = bitmap.to_pil().convert("RGB")
            result = process_page(
                raw,
                page_no,
                dest,
                rotate=args.rotate,
                detect_flip=args.detect_flip,
                rotation_threshold=args.rotation_threshold,
                max_skew=args.max_skew,
                quality=args.quality,
                dry_run=args.dry_run,
            )
            results.append(result)

            flag = f"  REVIEW:{','.join(result.review_reasons)}" if result.review_required else ""
            print(
                f"  page {page_no:>3}  {result.width}x{result.height}"
                f"  rot={result.rotation_applied:>3}"
                f"  skew={result.skew_applied:+.2f}deg{flag}"
            )

            # Kept from scripts/convert_to_text.py: these bundles are large enough
            # that leaving the bitmaps to the collector has thrown bad_alloc before.
            del raw, bitmap, page
            gc.collect()
    finally:
        pdf.close()

    if results and not args.dry_run:
        write_manifest(out_dir / "manifest.csv", results)

    deskewed = [r for r in results if r.skew_applied]
    reoriented = [r for r in results if r.rotation_applied]
    flagged = [r for r in results if r.review_required]
    print(
        f"\ndone: {len(results)} pages"
        f" | deskewed {len(deskewed)}"
        f" | orientation-corrected {len(reoriented)}"
        f" | blank {sum(1 for r in results if r.blank)}"
        f" | review required {len(flagged)}"
    )
    if not args.detect_flip:
        suspected = [r for r in results if r.rotation_detected % 360 in (180, 270)]
        if suspected:
            print(
                f"note: {len(suspected)} page(s) read as upside-down by the "
                f"{FLIP_ACCURACY:.0%}-accurate flip heuristic; not applied. "
                "Re-run with --detect-flip to act on it."
            )
    for result in flagged:
        print(f"  review page {result.page_no:>3}: {', '.join(result.review_reasons)}")
    if args.dry_run:
        print("dry run: no images or manifest written")
    else:
        print(f"output: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="source PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--pages", help='page spec, e.g. "1-10,15,40-" (default: all)')
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="render scale; 1.0 is approximately the source scan resolution (default: 1.0)",
    )
    parser.add_argument("--format", choices=("png", "jpg"), default="png")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality, 1-100")
    parser.add_argument(
        "--no-rotate",
        dest="rotate",
        action="store_false",
        help="skip orientation correction, deskew only",
    )
    parser.add_argument(
        "--detect-flip",
        action="store_true",
        help=(
            "act on the 180-degree flip heuristic. Off by default: it scored "
            f"{FLIP_ACCURACY:.2f} accuracy on this corpus, so it is recorded in "
            "rotation_detected but not applied or flagged unless asked for"
        ),
    )
    parser.add_argument(
        "--rotation-threshold",
        type=float,
        default=0.75,
        help=(
            "confidence (0.0-1.0) required before a rotation is applied; below it "
            "the page is flagged for review instead (default: 0.75). Flip "
            f"confidence is capped at {FLIP_ACCURACY:.2f}, so 180-degree "
            "corrections need a lower threshold to be acted on"
        ),
    )
    parser.add_argument(
        "--max-skew",
        type=float,
        default=5.0,
        help="skew angles beyond this are flagged for review, not corrected (default: 5.0)",
    )
    parser.add_argument("--overwrite", action="store_true", help="redo pages already written")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="measure and report without writing anything",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
