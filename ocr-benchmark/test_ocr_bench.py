"""Offline tests for the benchmark harness. No API key, no spend, no client data.

    uv run python -m pytest ocr-benchmark/test_ocr_bench.py -q

The point of these is that the measurement chain is provably correct before any
model result is believed. The synthetic fixture has perfect ground truth, so a
clean read must score 100% and 0.00 CER; if it does not, the harness is wrong.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contract  # noqa: E402
import engines  # noqa: E402
import normalize  # noqa: E402
import render  # noqa: E402
import score  # noqa: E402

PLATFORM_EVAL = (
    Path(__file__).resolve().parents[2]
    / "draftly-platform"
    / "backend"
    / "scripts"
    / "eval_extraction.py"
)


# ── normalization parity with the platform ───────────────────────────────────
def _platform_norm_from_source():
    """Extract and compile the platform's own _norm, so drift fails a test.

    Imported by source rather than by module because eval_extraction.py pulls in
    the whole FastAPI backend at import time.
    """
    source = PLATFORM_EVAL.read_text(encoding="utf-8")
    match = re.search(r"def _norm\(value: str\) -> str:.*?(?=\n\n(?:async )?def )", source, re.S)
    assert match, "could not locate _norm in the platform scorer"
    namespace: dict[str, object] = {}
    exec("import unicodedata\n" + match.group(0), namespace)  # noqa: S102
    return namespace["_norm"]


@pytest.mark.skipif(not PLATFORM_EVAL.is_file(), reason="platform repo not present")
@pytest.mark.parametrize(
    "value",
    [
        "Rs. 4,819,500/=",
        "4819500",
        "00030085091",
        "  Colombo  .  ",
        "0.0153 ha",
        "199012345678",
        "HIMATH   nimpura",
        "පරාක්‍රම",
        "12/34-56",
        "",
    ],
)
def test_platform_norm_is_byte_identical(value):
    """If this fails, the headline number is no longer comparable to production."""
    assert normalize.platform_norm(value) == _platform_norm_from_source()(value)


def test_platform_norm_does_not_strip_currency_prefix():
    """Documents the platform's real behaviour: 'Rs.' survives normalization.

    So an expectation of "Rs.4,819,500/=" does NOT match a prediction of
    "4819500". That is the platform's semantics, kept deliberately rather than
    silently improved, because diverging would make the numbers incomparable.
    """
    assert normalize.platform_norm("Rs.4,819,500/=") == "rs.4819500"
    assert normalize.platform_norm("4819500") == "4819500"


# ── leading zeros ────────────────────────────────────────────────────────────
def test_leading_zeros_survive_json_and_csv():
    value = "0021"
    assert json.loads(json.dumps({"v": value}))["v"] == value
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["v"])
    writer.writeheader()
    writer.writerow({"v": value})
    buffer.seek(0)
    assert next(csv.DictReader(buffer))["v"] == value
    assert normalize.platform_norm(value) == "0021"
    assert normalize.strict_norm(value) == "0021"


def test_numeric_prediction_is_an_error_not_a_value():
    """A JSON number has already lost its leading zeros; never score it correct."""
    outcome, flags = score.classify_outcome("0021", 21)
    assert outcome == "wrong"
    assert flags["type_error"] is True


def test_near_miss_identifier_is_wrong():
    """The case the benchmark exists to catch: one digit out, legally wrong."""
    outcome, _ = score.classify_outcome("00030085091", "00030085090")
    assert outcome == "wrong"


def test_exact_identifier_is_correct():
    outcome, flags = score.classify_outcome("00030085091", "00030085091")
    assert outcome == "correct"
    assert flags["platform"] and flags["strict"]


def test_null_tokens_count_as_missing_not_wrong():
    for token in ("N/A", "unknown", "undetected", "", "null"):
        outcome, _ = score.classify_outcome("0021", token)
        assert outcome == "missing", token


def test_no_expectation_is_no_label_never_wrong():
    assert score.classify_outcome(None, None)[0] == "no_label"
    assert score.classify_outcome(None, "something")[0] == "unlabelled_extra"


def test_ambiguous_is_excluded():
    assert score.classify_outcome("0021", "0021", ambiguous=True)[0] == "ambiguous"


# ── edit distance ────────────────────────────────────────────────────────────
def test_levenshtein_hand_computed():
    assert normalize.levenshtein("kitten", "sitting") == 3
    assert normalize.levenshtein("", "abc") == 3
    assert normalize.levenshtein("abc", "abc") == 0


def test_cer_and_wer_hand_computed():
    assert normalize.cer("abcdef", "abcdef") == 0.0
    assert normalize.cer("abcdef", "abXdef") == pytest.approx(1 / 6)
    assert normalize.wer("the cat sat", "the dog sat") == pytest.approx(1 / 3)


def test_cer_undefined_on_empty_reference():
    assert normalize.cer("", "anything") is None
    assert normalize.wer("", "anything") is None


def test_cer_does_not_casefold_the_reference():
    """Casefolding a CER reference would understate real recognition errors."""
    assert normalize.cer("ABC", "abc") == pytest.approx(1.0)


# ── script detection ─────────────────────────────────────────────────────────
def test_script_detection():
    assert normalize.script_of("හිමිකම් සහතිකය") == "sinhala"
    assert normalize.script_of("Title Certificate") == "latin"
    assert normalize.script_of("உரிமைச் சான்றிதழ்") == "tamil"
    assert normalize.script_of("හිමිකම් Certificate Number") == "mixed"
    assert normalize.script_of("   ") == "unknown"


# ── bbox geometry ────────────────────────────────────────────────────────────
def test_gemini_bbox_is_transposed_and_scaled():
    # [ymin, xmin, ymax, xmax] 0-1000 -> [x0, y0, x1, y1] 0-1
    assert contract.bbox_from_gemini([100, 200, 300, 400]) == (0.2, 0.1, 0.4, 0.3)


def test_bbox_pixel_round_trip():
    bbox = (0.25, 0.5, 0.75, 0.625)
    pixels = contract.bbox_to_pixels(bbox, 1000, 800)
    assert pixels == (250, 400, 750, 500)
    assert contract.bbox_from_pixels(pixels, 1000, 800) == pytest.approx(bbox)


def test_clamp_orders_and_clips():
    assert contract.clamp_bbox((0.8, 0.9, 0.2, 0.1)) == (0.2, 0.1, 0.8, 0.9)
    assert contract.clamp_bbox((-1.0, -1.0, 2.0, 2.0)) == (0.0, 0.0, 1.0, 1.0)


def test_iou_and_contains():
    a = (0.0, 0.0, 0.5, 0.5)
    assert contract.iou(a, a) == pytest.approx(1.0)
    assert contract.iou(a, (0.6, 0.6, 0.9, 0.9)) == 0.0
    assert contract.bbox_contains((0.0, 0.0, 1.0, 1.0), (0.2, 0.2, 0.3, 0.3))
    assert not contract.bbox_contains((0.0, 0.0, 0.2, 0.2), (0.5, 0.5, 0.9, 0.9))


def test_identity_affine_is_a_no_op():
    bbox = (0.1, 0.2, 0.3, 0.4)
    assert contract.bbox_apply(bbox, contract.IDENTITY) == pytest.approx(bbox)


def test_deskew_affine_maps_a_box_back_to_the_original_frame():
    """Without this, a preprocessed run's boxes are not comparable with run A."""
    image, truth = render.synthetic_page()
    rotated = image.rotate(-6, resample=Image.BICUBIC, fillcolor="white")
    deskewed, affine = render.deskew(rotated)
    assert affine != contract.IDENTITY, "a 6 degree skew should have been corrected"
    # A box in the deskewed frame, mapped back, must land inside the page and
    # move in the direction the rotation went.
    box = truth[0]["bbox"]
    mapped = contract.bbox_apply(box, affine)
    assert all(0.0 <= v <= 1.0 for v in mapped)
    assert mapped != pytest.approx(box)


def test_skew_estimation_recovers_a_known_angle():
    image, _ = render.synthetic_page()
    for applied in (-6.0, 3.0):
        rotated = image.rotate(applied, resample=Image.BICUBIC, fillcolor="white")
        assert render.estimate_skew(rotated) == pytest.approx(-applied, abs=1.0)


def test_orientation_leaves_an_upright_portrait_page_alone():
    """Wrongly rotating a correct page corrupts every downstream run."""
    image, _ = render.synthetic_page()
    degrees, _ratio = render.detect_orientation(image)
    assert degrees == 0
    assert render.apply_variant(image, "full")[0].size == image.size


def test_variants_preserve_page_size():
    image, _ = render.synthetic_page()
    for variant in render.VARIANTS:
        assert render.apply_variant(image, variant)[0].size == image.size


def test_unknown_variant_raises():
    image, _ = render.synthetic_page()
    with pytest.raises(KeyError):
        render.apply_variant(image, "nope")


def test_crop_pads_and_never_returns_an_empty_image():
    image, truth = render.synthetic_page()
    patch = render.crop(image, truth[0]["bbox"], pad=0.02)
    assert patch.size[0] > 0 and patch.size[1] > 0
    # A zero-area box is rescued by the padding rather than producing an empty
    # crop; a genuinely unpaddable box falls back to the whole page.
    padded = render.crop(image, (0.5, 0.5, 0.5, 0.5), pad=0.02)
    assert padded.size[0] > 0 and padded.size[1] > 0
    assert render.crop(image, (0.5, 0.5, 0.5, 0.5), pad=0.0).size == image.size


def test_blank_detection():
    assert not render.image_has_content(Image.new("RGB", (400, 400), "white"))
    page, _ = render.synthetic_page()
    assert render.image_has_content(page)


# ── the stub engine: the keystone ────────────────────────────────────────────
def _stub_page(noise: float, seed: int = 0):
    image, truth = render.synthetic_page()
    page = render.RenderedPage(1, image, 200, "original", contract.IDENTITY, False)
    return truth, engines.stub_read_page(page, truth, noise=noise, seed=seed)


def test_clean_stub_is_a_perfect_reader():
    truth, reading = _stub_page(0.0)
    reference = "\n".join(str(row["text"]) for row in truth)
    assert normalize.cer(reference, reading.text) == 0.0
    assert normalize.wer(reference, reading.text) == 0.0
    for field, row in zip(reading.fields, truth):
        assert field.value == row["verbatimValue"]
        outcome, _ = score.classify_outcome(str(row["verbatimValue"]), field.value)
        assert outcome == "correct"


def test_clean_stub_values_are_all_grounded():
    _truth, reading = _stub_page(0.0)
    assert all(field.verbatim_in_page_text for field in reading.fields)


def test_noise_degrades_accuracy_and_raises_cer():
    """Proves the metrics actually move, rather than always reporting success."""
    truth, clean = _stub_page(0.0)
    _t, noisy = _stub_page(0.25, seed=11)
    reference = "\n".join(str(row["text"]) for row in truth)
    assert normalize.cer(reference, noisy.text) > normalize.cer(reference, clean.text)
    exact = sum(
        field.value == row["verbatimValue"] for field, row in zip(noisy.fields, truth)
    )
    assert exact < len(truth)


def test_stub_is_deterministic():
    a = engines.stub_read_page(*_stub_args(0.2), noise=0.2, seed=5)
    b = engines.stub_read_page(*_stub_args(0.2), noise=0.2, seed=5)
    assert a.text == b.text


def _stub_args(_noise: float):
    image, truth = render.synthetic_page()
    return render.RenderedPage(1, image, 200, "original", contract.IDENTITY, False), truth


# ── invented values ──────────────────────────────────────────────────────────
def test_value_in_text_is_not_fuzzy():
    text = "consideration of Rs.4819500 paid in full"
    assert normalize.value_in_text("4,819,500", text)
    assert not normalize.value_in_text("4819501", text)
    assert not normalize.value_in_text("9999999", text)


# ── privacy guard ────────────────────────────────────────────────────────────
def test_guard_blocks_values_in_tracked_reports():
    with pytest.raises(ValueError):
        normalize.assert_no_raw_values(
            Path("ocr-benchmark/reports/findings.csv"), ["variant_id", "expected"]
        )


def test_guard_allows_values_under_runs_and_aggregates_in_reports():
    normalize.assert_no_raw_values(
        Path("ocr-benchmark/runs/A/predictions.csv"), ["expected", "predicted"]
    )
    normalize.assert_no_raw_values(
        Path("ocr-benchmark/reports/metrics.csv"), ["variant_id", "accuracy"]
    )


# ── wilson interval ──────────────────────────────────────────────────────────
def test_wilson_brackets_the_estimate():
    low, high = normalize.wilson_interval(30, 37)
    assert low < 30 / 37 < high
    assert normalize.wilson_interval(0, 0) == (0.0, 0.0)


# ── registry vocabulary ──────────────────────────────────────────────────────
def test_synthetic_fixture_contains_no_real_client_values():
    """The fixture is tracked in git, so it must not carry values from the corpus.

    Regression guard: an earlier version copied real numbers out of a case
    manifest to look realistic, which put client data into a committed file.
    """
    import config

    real: set[str] = set()
    for case in config.case_dirs():
        path = config.expected_fields_path(case)
        if not path.is_file():
            continue
        for payload in json.loads(path.read_text(encoding="utf-8")).values():
            real.update(str(v).strip() for v in (payload.get("fields") or {}).values())

    if not real:
        pytest.skip("no labelled corpus present to check against")

    collisions = [f"{k}={v}" for k, v in render.SYNTHETIC_LINES if v.strip() in real]
    assert not collisions, f"synthetic fixture leaks real client values: {collisions}"


def test_criticality_overlay_covers_every_registry_key():
    """A new registry field must be classified, not silently treated as non-critical."""
    import config

    registry = json.loads(
        (config.SCHEMAS / "registry-fields.json").read_text(encoding="utf-8")
    )["kinds"]
    keys = {f["key"] for fields in registry.values() for f in fields}
    overlay = json.loads(
        (config.SCHEMAS / "critical-fields.json").read_text(encoding="utf-8")
    )
    declared = set(overlay["critical"]) | set(overlay["non_critical"])
    assert keys == declared
