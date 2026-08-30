"""Tests for rotation detection, on synthetic polygons only.

    uv run python -m pytest ocr-benchmark/test_final_rotation.py -q

No API, no client data. Every polygon here is constructed, so the expected
orientation is known exactly rather than assumed.

Vision emits a word's vertices starting at the text's own top-left and going
clockwise in reading order. The helper below builds that vertex order for a word
box at a chosen rotation, which is what makes these cases meaningful: an
axis-aligned rectangle carries no rotation, the VERTEX ORDER does.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import final_rotation as fr


def word_polygon(cx: float, cy: float, w: float, h: float, orientation_cw: int):
    """Vertices for a word rotated `orientation_cw` degrees clockwise.

    Corner order follows Vision: text top-left first, then clockwise around the
    glyph box in the text's own frame.
    """
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    theta = math.radians(orientation_cw)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    out = []
    for dx, dy in corners:
        # Clockwise rotation in image coordinates (y grows downward).
        rx = dx * cos_t - dy * sin_t
        ry = dx * sin_t + dy * cos_t
        out.append([cx + rx, cy + ry])
    return out


def make_words(orientation_cw: int, count: int = 20, confidence: float = 0.95):
    return [
        {"confidence": confidence,
         "original_polygon": word_polygon(0.5, 0.05 + i * 0.04, 0.20, 0.02, orientation_cw)}
        for i in range(count)
    ]


# ── the four clean cases ─────────────────────────────────────────────────────
def test_upright_page():
    result = fr.detect_orientation(make_words(0))
    assert result["detected_orientation_degrees"] == 0
    assert result["status"] == "upright"
    assert result["correction_degrees"] == 0
    assert result["vote_share"] == pytest.approx(1.0)
    assert result["usable_word_count"] == 20


def test_clockwise_90():
    """Text rotated 90 deg clockwise must be corrected by rotating the page 270 deg CW."""
    result = fr.detect_orientation(make_words(90))
    assert result["detected_orientation_degrees"] == 90
    assert result["status"] == "rotate"
    assert result["correction_degrees"] == 270


def test_counter_clockwise_90():
    """CCW 90 is the same as CW 270."""
    result = fr.detect_orientation(make_words(270))
    assert result["detected_orientation_degrees"] == 270
    assert result["status"] == "rotate"
    assert result["correction_degrees"] == 90


def test_upside_down_180():
    result = fr.detect_orientation(make_words(180))
    assert result["detected_orientation_degrees"] == 180
    assert result["status"] == "rotate"
    assert result["correction_degrees"] == 180


# ── uncertainty, which must never resolve to a guess ─────────────────────────
def test_mixed_orientation_is_uncertain():
    """A 50/50 split cannot reach the 70% share, so it must abstain."""
    words = make_words(0, count=10) + make_words(90, count=10)
    result = fr.detect_orientation(words)
    assert result["status"] == "uncertain"
    assert result["detected_orientation_degrees"] is None
    assert result["correction_degrees"] == 0
    assert result["vote_share"] < fr.MIN_VOTE_SHARE


def test_too_few_words_is_uncertain():
    result = fr.detect_orientation(make_words(90, count=fr.MIN_USABLE_WORDS - 1))
    assert result["status"] == "uncertain"
    assert result["usable_word_count"] == fr.MIN_USABLE_WORDS - 1


def test_low_confidence_words_are_not_counted():
    """Below the confidence floor a word contributes nothing, even in bulk."""
    words = make_words(90, count=40, confidence=0.10)
    result = fr.detect_orientation(words)
    assert result["usable_word_count"] == 0
    assert result["status"] == "uncertain"


def test_just_over_threshold_resolves():
    """80/20 split clears 70% and must produce a decision, not an abstention."""
    words = make_words(90, count=40) + make_words(0, count=10)
    result = fr.detect_orientation(words)
    assert result["status"] == "rotate"
    assert result["detected_orientation_degrees"] == 90
    assert result["vote_share"] >= fr.MIN_VOTE_SHARE


def test_longer_words_carry_more_weight():
    """Weighting is confidence x top-edge length, so one long word can outvote
    several short ones. Verifies the weighting is actually applied."""
    short = [{"confidence": 0.95,
              "original_polygon": word_polygon(0.5, 0.1 + i * 0.03, 0.02, 0.02, 0)}
             for i in range(12)]
    long_words = [{"confidence": 0.95,
                   "original_polygon": word_polygon(0.5, 0.6 + i * 0.03, 0.60, 0.02, 90)}
                  for i in range(12)]
    result = fr.detect_orientation(short + long_words)
    assert result["detected_orientation_degrees"] == 90


def test_degenerate_polygons_are_skipped():
    words = [{"confidence": 0.99, "original_polygon": [[0.5, 0.5]] * 4} for _ in range(20)]
    result = fr.detect_orientation(words)
    assert result["usable_word_count"] == 0
    assert result["status"] == "uncertain"


def test_empty_input_is_uncertain():
    result = fr.detect_orientation([])
    assert result["status"] == "uncertain"
    assert result["usable_word_count"] == 0


# ── coordinate transform ─────────────────────────────────────────────────────
def test_rotate_point_corners():
    assert fr.rotate_point(0.0, 0.0, 0) == (0.0, 0.0)
    # 90 CW sends the top-left corner to the top-right.
    assert fr.rotate_point(0.0, 0.0, 90) == (1.0, 0.0)
    assert fr.rotate_point(0.0, 0.0, 180) == (1.0, 1.0)
    assert fr.rotate_point(0.0, 0.0, 270) == (0.0, 1.0)


def test_rotation_is_cyclic():
    """Four 90-degree turns return to the start; no drift."""
    x, y = 0.23, 0.71
    px, py = x, y
    for _ in range(4):
        px, py = fr.rotate_point(px, py, 90)
    assert (px, py) == pytest.approx((x, y))


def test_correction_makes_text_upright():
    """The end-to-end property: applying the correction leaves text at 0 degrees."""
    for orientation in (0, 90, 180, 270):
        words = make_words(orientation)
        result = fr.detect_orientation(words)
        correction = result["correction_degrees"]
        rotated = [
            {"confidence": w["confidence"],
             "original_polygon": fr.rotate_polygon(w["original_polygon"], correction)}
            for w in words
        ]
        after = fr.detect_orientation(rotated)
        assert after["detected_orientation_degrees"] == 0, f"failed for {orientation}"
        assert after["status"] == "upright"


def test_unsupported_rotation_raises():
    with pytest.raises(ValueError):
        fr.rotate_point(0.1, 0.2, 45)


def test_reading_order_is_top_left_first():
    top_left = [[0.1, 0.1], [0.2, 0.1], [0.2, 0.12], [0.1, 0.12]]
    top_right = [[0.7, 0.1], [0.8, 0.1], [0.8, 0.12], [0.7, 0.12]]
    lower = [[0.1, 0.5], [0.2, 0.5], [0.2, 0.52], [0.1, 0.52]]
    keys = [fr.reading_order_key(p) for p in (lower, top_right, top_left)]
    assert sorted(range(3), key=lambda i: keys[i]) == [2, 1, 0]


def test_snap_orientation_rounds_small_skew():
    """A few degrees of scan skew must snap to 0, not to 90."""
    assert fr.snap_orientation(1.0, 0.05) == 0
    assert fr.snap_orientation(1.0, -0.05) == 0
    assert fr.snap_orientation(0.05, 1.0) == 90
