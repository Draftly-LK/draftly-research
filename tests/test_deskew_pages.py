"""Tests for scripts/deskew_pages.py.

Everything here runs on synthetic pages, not the 61 MB scan: the point is to
prove the harness handles each orientation, the confidence gates, the review
flags and the manifest merge, and a fixture makes those cases reachable on
demand instead of hoping the corpus contains one.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "ocr-benchmark"))

import deskew_pages as dp  # noqa: E402


def upright_page(
    width: int = 1600, height: int = 2200, band: int = 34, ascenders: bool = False
) -> Image.Image:
    """A page of ragged horizontal ink bands: text as the detector sees it.

    Deliberately not rendered text. Both the orientation and skew heuristics read
    a projection profile, whose entire model of a page is "ink bands separated by
    gutters", and PIL's default bitmap font renders crisp vertical stems that a
    real scan's blur destroys — synthetic *text* makes the column profile spikier
    than the row profile and inverts the axis decision, which is a property of the
    fixture, not of the pages this script runs on. Bands reproduce what the
    downsampled ink mask of a real scan actually looks like.

    `ascenders` adds stubs above each band, giving the page the ragged-top /
    sharp-bottom asymmetry that the 180-degree heuristic keys on. Plain bands are
    vertically symmetric, so nothing can tell them from their own flip.
    """
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    step = int(band * 1.9)
    widths = [0.95, 0.88, 0.97, 0.72, 0.93, 0.85]  # ragged right edge
    y, index = 180, 0
    while y < height - 180:
        run = int((width - 300) * widths[index % len(widths)])
        draw.rectangle([150, y, 150 + run, y + band], fill="black")
        if ascenders:
            for x in range(150, 150 + run, 90):
                draw.rectangle([x, y - band // 2, x + 12, y], fill="black")
        y += step
        index += 1
    return image


def rotated_page(degrees: int) -> Image.Image:
    """A page needing `degrees` of clockwise correction to become upright."""
    image = upright_page()
    if degrees == 0:
        return image
    # Invert the correction: rotate counter-clockwise by the same amount.
    return image.transpose(
        {
            90: Image.Transpose.ROTATE_90,
            180: Image.Transpose.ROTATE_180,
            270: Image.Transpose.ROTATE_270,
        }[degrees]
    )


def blank_page(size: tuple[int, int] = (600, 800)) -> Image.Image:
    return Image.new("RGB", size, "white")


class OrientationTests(unittest.TestCase):
    def test_axis_detected_for_all_four_orientations(self):
        """The portrait/landscape half of the decision is right for 0/90/180/270."""
        for degrees in (0, 90, 180, 270):
            with self.subTest(degrees=degrees):
                reading = dp.detect_orientation(rotated_page(degrees))
                self.assertFalse(reading.failed)
                self.assertEqual(reading.axis_degrees, degrees % 180)
                self.assertGreaterEqual(reading.axis_confidence, 0.75)

    def test_detected_degrees_is_a_legal_orientation(self):
        for degrees in (0, 90, 180, 270):
            with self.subTest(degrees=degrees):
                reading = dp.detect_orientation(rotated_page(degrees))
                self.assertIn(reading.degrees, (0, 90, 180, 270))

    def test_confidences_are_bounded_probabilities(self):
        """A threshold of 0.75 is only meaningful if confidence is a 0-1 value."""
        for degrees in (0, 90, 180, 270):
            reading = dp.detect_orientation(rotated_page(degrees))
            with self.subTest(degrees=degrees):
                self.assertGreaterEqual(reading.axis_confidence, 0.0)
                self.assertLessEqual(reading.axis_confidence, 1.0)
                self.assertGreaterEqual(reading.flip_confidence, 0.0)
                self.assertLessEqual(reading.flip_confidence, 1.0)

    def test_flip_confidence_never_exceeds_measured_accuracy(self):
        """The 180 heuristic scored 5/9; it must not present as more certain."""
        for degrees in (0, 90, 180, 270):
            reading = dp.detect_orientation(rotated_page(degrees))
            with self.subTest(degrees=degrees):
                self.assertLessEqual(reading.flip_confidence, dp.FLIP_ACCURACY + 1e-9)

    def test_blank_page_reports_detection_failure(self):
        reading = dp.detect_orientation(blank_page())
        self.assertTrue(reading.failed)


class RotationTests(unittest.TestCase):
    def test_rotation_restores_upright_size(self):
        original = upright_page()
        for degrees in (90, 270):
            with self.subTest(degrees=degrees):
                rotated, _ = dp.apply_rotation(rotated_page(degrees), degrees)
                self.assertEqual(rotated.size, original.size)

    def test_rotation_round_trips_pixels(self):
        for degrees in (0, 90, 180, 270):
            with self.subTest(degrees=degrees):
                original = upright_page()
                restored, _ = dp.apply_rotation(rotated_page(degrees), degrees)
                self.assertEqual(
                    list(restored.convert("L").getdata()),
                    list(original.convert("L").getdata()),
                )

    def test_rejects_non_quarter_turns(self):
        with self.assertRaises(ValueError):
            dp.apply_rotation(upright_page(), 45)


class SkewTests(unittest.TestCase):
    def test_measures_injected_skew(self):
        page = upright_page()
        for injected in (-3.0, -1.5, 1.5, 3.0):
            with self.subTest(injected=injected):
                tilted = page.rotate(injected, expand=False, fillcolor=(255, 255, 255))
                measured = dp.measure_skew(tilted)
                self.assertAlmostEqual(measured, -injected, delta=0.5)

    def test_applied_angle_is_reported_not_assumed(self):
        page = upright_page()
        _out, _affine, applied = dp.apply_deskew(page, 2.0)
        self.assertEqual(applied, 2.0)

    def test_deadband_reports_zero_applied(self):
        """A measured angle under the deadband is measured but not applied."""
        page = upright_page()
        out, affine, applied = dp.apply_deskew(page, 0.02)
        self.assertEqual(applied, 0.0)
        self.assertEqual(affine, dp.IDENTITY)
        self.assertIs(out, page)


class ProcessPageTests(unittest.TestCase):
    def setUp(self):
        self.dest = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))

    def test_slightly_skewed_page_is_corrected(self):
        tilted = upright_page().rotate(2.0, expand=False, fillcolor=(255, 255, 255))
        result = dp.process_page(tilted, 1, self.dest / "p.png", dry_run=True)
        self.assertAlmostEqual(result.skew_measured, -2.0, delta=0.5)
        self.assertEqual(result.skew_applied, result.skew_measured)
        self.assertNotIn(dp.REVIEW_EXCESSIVE_SKEW, result.review_reasons)

    def test_blank_page_is_left_untouched(self):
        result = dp.process_page(blank_page(), 1, self.dest / "p.png", dry_run=True)
        self.assertTrue(result.blank)
        self.assertEqual(result.rotation_applied, 0)
        self.assertEqual(result.skew_measured, 0.0)
        self.assertEqual(result.skew_applied, 0.0)
        self.assertEqual(result.transform, dp.IDENTITY)
        self.assertIn(dp.REVIEW_BLANK, result.review_reasons)

    def test_blank_page_is_still_written(self):
        dest = self.dest / "blank.png"
        dp.process_page(blank_page(), 1, dest, dry_run=False)
        self.assertTrue(dest.is_file())

    def test_low_confidence_withholds_rotation_and_flags(self):
        """An impossible threshold must flag rather than rotate."""
        result = dp.process_page(
            rotated_page(90),
            1,
            self.dest / "p.png",
            rotation_threshold=1.0,
            dry_run=True,
        )
        self.assertEqual(result.rotation_applied, 0)
        self.assertEqual(result.rotation_detected % 180, 90)
        self.assertIn(dp.REVIEW_LOW_CONFIDENCE, result.review_reasons)

    def test_confident_rotation_is_applied(self):
        upright = upright_page()
        result = dp.process_page(
            rotated_page(90),
            1,
            self.dest / "p.png",
            rotation_threshold=0.6,
            dry_run=True,
        )
        self.assertEqual(result.rotation_applied, 90)
        self.assertEqual((result.width, result.height), upright.size)

    def test_flip_is_recorded_but_not_acted_on_by_default(self):
        """A coin-toss heuristic must not rotate pages or fill the review queue."""
        flipped = upright_page(ascenders=True).transpose(Image.Transpose.ROTATE_180)
        result = dp.process_page(
            flipped, 1, self.dest / "p.png", rotation_threshold=0.0, dry_run=True
        )
        self.assertEqual(result.rotation_detected, 180)
        self.assertEqual(result.rotation_applied, 0)
        self.assertNotIn(dp.REVIEW_LOW_CONFIDENCE, result.review_reasons)

    def test_flip_is_flagged_when_requested_but_unconfident(self):
        flipped = upright_page(ascenders=True).transpose(Image.Transpose.ROTATE_180)
        result = dp.process_page(
            flipped,
            1,
            self.dest / "p.png",
            detect_flip=True,
            rotation_threshold=0.75,
            dry_run=True,
        )
        self.assertEqual(result.rotation_applied, 0)
        self.assertIn(dp.REVIEW_LOW_CONFIDENCE, result.review_reasons)

    def test_flip_is_applied_when_requested_and_threshold_lowered(self):
        flipped = upright_page(ascenders=True).transpose(Image.Transpose.ROTATE_180)
        result = dp.process_page(
            flipped,
            1,
            self.dest / "p.png",
            detect_flip=True,
            rotation_threshold=0.0,
            dry_run=True,
        )
        self.assertEqual(result.rotation_applied, 180)

    def test_combined_flip_and_axis_gives_270(self):
        """All four orientations are representable end to end, not just 0/90."""
        page = upright_page(ascenders=True).transpose(Image.Transpose.ROTATE_180)
        page = page.transpose(Image.Transpose.ROTATE_90)  # now needs 90 + 180
        result = dp.process_page(
            page, 1, self.dest / "p.png", detect_flip=True,
            rotation_threshold=0.0, dry_run=True,
        )
        self.assertEqual(result.rotation_applied, 270)

    def test_excessive_skew_is_flagged_not_corrected(self):
        tilted = upright_page().rotate(9.0, expand=False, fillcolor=(255, 255, 255))
        result = dp.process_page(
            tilted, 1, self.dest / "p.png", max_skew=5.0, dry_run=True
        )
        self.assertGreater(abs(result.skew_measured), 5.0)
        self.assertEqual(result.skew_applied, 0.0)
        self.assertIn(dp.REVIEW_EXCESSIVE_SKEW, result.review_reasons)

    def test_orientation_failure_falls_back_to_original_page(self):
        page = upright_page()

        def boom(_image):
            raise RuntimeError("synthetic orientation failure")

        original = dp.detect_orientation
        dp.detect_orientation = boom
        try:
            dest = self.dest / "p.png"
            result = dp.process_page(page, 1, dest, dry_run=False)
        finally:
            dp.detect_orientation = original

        self.assertIn(dp.REVIEW_ORIENTATION_FAILED, result.review_reasons)
        self.assertEqual(result.rotation_applied, 0)
        self.assertTrue(dest.is_file())
        # The page survived: same dimensions as the unmodified render.
        self.assertEqual(Image.open(dest).size, page.size)

    def test_deskew_failure_falls_back_to_original_page(self):
        page = upright_page()

        def boom(_image):
            raise RuntimeError("synthetic deskew failure")

        original = dp.measure_skew
        dp.measure_skew = boom
        try:
            dest = self.dest / "p.png"
            result = dp.process_page(page, 1, dest, dry_run=False)
        finally:
            dp.measure_skew = original

        self.assertIn(dp.REVIEW_DESKEW_FAILED, result.review_reasons)
        self.assertEqual(result.skew_applied, 0.0)
        self.assertTrue(dest.is_file())

    def test_affine_maps_output_back_through_rotation_and_deskew(self):
        """A marked pixel must map back to where it started in the render frame."""
        page = upright_page().rotate(3.0, expand=False, fillcolor=(255, 255, 255))
        page = page.transpose(Image.Transpose.ROTATE_90)  # needs a 90 correction
        # A block, not a pixel: cubic resampling would smear a single pixel away.
        marker = (page.width // 3, page.height // 4)
        ImageDraw.Draw(page).rectangle(
            [marker[0] - 5, marker[1] - 5, marker[0] + 5, marker[1] + 5], fill=(255, 0, 0)
        )

        result = dp.process_page(
            page, 1, self.dest / "p.png", rotation_threshold=0.6, dry_run=True
        )
        self.assertEqual(result.rotation_applied, 90)
        self.assertNotEqual(result.skew_applied, 0.0)

        # Re-run the transform to get the processed image itself.
        rotated, rot_affine = dp.apply_rotation(page, result.rotation_applied)
        straight, skew_affine, _ = dp.apply_deskew(rotated, result.skew_applied)
        affine = dp._compose_affine(skew_affine, dp._compose_affine(rot_affine, dp.IDENTITY))
        self.assertEqual(affine, result.transform)

        # Locate the marker in the processed frame, map it back, compare.
        found = np.argwhere(
            (np.asarray(straight)[:, :, 0] > 180)
            & (np.asarray(straight)[:, :, 1] < 90)
            & (np.asarray(straight)[:, :, 2] < 90)
        )
        self.assertTrue(found.size, "marker pixel not found in processed image")
        py, px = found.mean(axis=0)
        (a, b, c), (d, e, f) = affine
        back_x = (a * (px / straight.width) + b * (py / straight.height) + c) * page.width
        back_y = (d * (px / straight.width) + e * (py / straight.height) + f) * page.height
        self.assertAlmostEqual(back_x, marker[0], delta=6)
        self.assertAlmostEqual(back_y, marker[1], delta=6)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        self.path = self.dir / "manifest.csv"

    def _result(self, page_no: int, skew: float = 0.0) -> dp.PageResult:
        return dp.PageResult(
            page_no=page_no,
            filename=f"page-{page_no:03d}.jpg",
            width=100,
            height=200,
            skew_applied=skew,
        )

    def _rows(self) -> dict[int, dict[str, str]]:
        with self.path.open(newline="", encoding="utf-8") as fh:
            return {int(r["page_no"]): r for r in csv.DictReader(fh)}

    def test_partial_overwrite_keeps_other_rows(self):
        dp.write_manifest(self.path, [self._result(n) for n in range(1, 68)])
        self.assertEqual(len(self._rows()), 67)

        # Re-run pages 1-10 only, as `--pages 1-10 --overwrite` would.
        dp.write_manifest(self.path, [self._result(n, skew=1.5) for n in range(1, 11)])
        rows = self._rows()

        self.assertEqual(len(rows), 67, "rows for pages 11-67 were dropped")
        self.assertEqual(float(rows[5]["skew_applied"]), 1.5)
        self.assertEqual(float(rows[42]["skew_applied"]), 0.0)

    def test_rows_are_sorted_by_page(self):
        dp.write_manifest(self.path, [self._result(n) for n in (9, 2, 40)])
        self.assertEqual(list(self._rows()), [2, 9, 40])

    def test_legacy_skew_corrected_is_migrated(self):
        """Manifests written before the rename still describe real pages."""
        legacy = ["page_no", "filename", "skew_corrected"]
        with self.path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=legacy)
            writer.writeheader()
            writer.writerow({"page_no": "7", "filename": "page-007.jpg", "skew_corrected": "-0.6"})

        dp.write_manifest(self.path, [self._result(1)])
        rows = self._rows()
        self.assertIn(7, rows)
        self.assertEqual(float(rows[7]["skew_applied"]), -0.6)

    def test_review_fields_are_written(self):
        result = self._result(1)
        result.review_reasons.append(dp.REVIEW_BLANK)
        dp.write_manifest(self.path, [result])
        row = self._rows()[1]
        self.assertEqual(row["review_required"], "True")
        self.assertEqual(row["review_reason"], dp.REVIEW_BLANK)


class ArgValidationTests(unittest.TestCase):
    def _args(self, **overrides):
        args = dp.build_parser().parse_args([])
        for key, value in overrides.items():
            setattr(args, key, value)
        return args

    def test_defaults_are_valid(self):
        dp.validate_args(self._args())

    def test_help_renders(self):
        """argparse %-expands help text, so a literal % in it crashes --help."""
        self.assertIn("--rotation-threshold", dp.build_parser().format_help())

    def test_rejects_bad_values(self):
        for field, value in [
            ("scale", 0.0),
            ("scale", -1.0),
            ("quality", 0),
            ("quality", 101),
            ("rotation_threshold", -0.1),
            ("rotation_threshold", 1.5),
            ("max_skew", 0.0),
            ("max_skew", -2.0),
        ]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    dp.validate_args(self._args(**{field: value}))


class PageSpecTests(unittest.TestCase):
    def test_ranges_and_singletons(self):
        self.assertEqual(dp.parse_pages("1-3,7,9-", 10), [1, 2, 3, 7, 9, 10])

    def test_default_is_every_page(self):
        self.assertEqual(dp.parse_pages(None, 4), [1, 2, 3, 4])

    def test_clamps_to_document(self):
        self.assertEqual(dp.parse_pages("3-99", 5), [3, 4, 5])

    def test_rejects_inverted_range(self):
        with self.assertRaises(ValueError):
            dp.parse_pages("9-2", 10)


if __name__ == "__main__":
    unittest.main()
