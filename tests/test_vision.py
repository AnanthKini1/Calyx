"""
tests/test_vision.py — ChroniScan vision pipeline test suite.

All tests use synthetically generated BGR numpy arrays so the suite runs
without any real wound photographs.  The images are constructed to have
known, deterministic HSV properties that the pipeline should classify
correctly.

Test categories
---------------
1. detect_wound_mask   — red granulation, yellow slough, bare skin, mixed
2. is_wound_present    — too-small mask, full-coverage mask, valid wound
3. analyze_image       — no-wound guard, red wound, yellow wound, mixed
4. analyze_frame       — same scenarios via numpy array path (real-time)
5. ryb_segment         — tissue ratios for pure-red, pure-yellow, mixed
6. _derive_alert       — triage rules for all 4 alert levels
7. demo mode           — analyze_patient without image_path
"""

from __future__ import annotations

import sys
import os

import numpy as np
import cv2
import pytest

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root or from tests/ directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import vision  # noqa: E402 — must come after sys.path manipulation
from vision import (
    detect_wound_mask,
    is_wound_present,
    analyze_image,
    analyze_frame,
    ryb_segment,
    _derive_alert,
    analyze_patient,
    _classify_cluster_hsv,
    COIN_REAL_DIAM_CM,
)


# ===========================================================================
# Synthetic image factories
# ===========================================================================

def _dark_canvas(h: int = 400, w: int = 400) -> np.ndarray:
    """Near-black background (avoids any wound-colour spillover)."""
    return np.full((h, w, 3), 15, dtype=np.uint8)


def _make_red_wound_img(h: int = 400, w: int = 400, radius: int = 80) -> np.ndarray:
    """
    Bright red circle on a dark background.
    BGR (0, 50, 210): H≈7, S≈255, V≈210 — well inside red HSV range (S≥120).
    """
    img = _dark_canvas(h, w)
    cv2.circle(img, (w // 2, h // 2), radius, (0, 50, 210), -1)
    return img


def _make_yellow_wound_img(h: int = 400, w: int = 400, radius: int = 80) -> np.ndarray:
    """
    Yellow circle on a dark background.
    BGR (0, 210, 230): H≈25, S≈255, V≈230 — inside yellow slough range.
    """
    img = _dark_canvas(h, w)
    cv2.circle(img, (w // 2, h // 2), radius, (0, 210, 230), -1)
    return img


def _make_mixed_wound_img(h: int = 400, w: int = 400, radius: int = 90) -> np.ndarray:
    """
    Red circle with a yellow crescent painted over the lower half.
    Simulates a wound with both granulation tissue and slough.
    """
    img = _dark_canvas(h, w)
    cx, cy = w // 2, h // 2
    # Full red disc first
    cv2.circle(img, (cx, cy), radius, (0, 50, 210), -1)
    # Yellow ellipse covering the lower ~40% of the wound
    cv2.ellipse(img, (cx, cy + radius // 3), (radius, radius // 2),
                0, 0, 180, (0, 210, 230), -1)
    return img


def _make_skin_img(h: int = 400, w: int = 400) -> np.ndarray:
    """
    Uniform skin-tone fill covering the entire canvas.
    BGR ≈ (110, 130, 180): H≈18, S≈90, V≈180 — skin-like, S < 120 for red
    and S < 100 in the yellow range, so both masks should stay quiet.
    """
    img = np.full((h, w, 3), 0, dtype=np.uint8)
    img[:, :, 0] = 110   # B
    img[:, :, 1] = 130   # G
    img[:, :, 2] = 180   # R
    return img


def _make_tiny_wound_img(h: int = 400, w: int = 400) -> np.ndarray:
    """5-pixel red dot — too small to be a wound (< min_pixels threshold)."""
    img = _dark_canvas(h, w)
    cv2.circle(img, (w // 2, h // 2), 5, (0, 50, 210), -1)
    return img


def _save_tmp(img: np.ndarray, name: str, tmp_path) -> str:
    """Write img to a temp file and return its path string."""
    p = tmp_path / name
    cv2.imwrite(str(p), img)
    return str(p)


# ===========================================================================
# 1. detect_wound_mask
# ===========================================================================

class TestDetectWoundMask:
    def test_red_wound_produces_mask(self):
        img = _make_red_wound_img()
        mask = detect_wound_mask(img)
        wound_px = int(np.sum(mask == 255))
        assert wound_px > 500, f"Red wound should produce >500 mask pixels, got {wound_px}"

    def test_yellow_wound_produces_mask(self):
        """
        Regression: old mask missed yellow slough entirely.
        Now yellow (H≈25, S≈255) must be captured.
        """
        img = _make_yellow_wound_img()
        mask = detect_wound_mask(img)
        wound_px = int(np.sum(mask == 255))
        assert wound_px > 500, (
            f"Yellow slough should produce >500 mask pixels, got {wound_px}. "
            "Check that the yellow HSV range [15-38] is included in detect_wound_mask."
        )

    def test_mixed_wound_produces_mask(self):
        img = _make_mixed_wound_img()
        mask = detect_wound_mask(img)
        wound_px = int(np.sum(mask == 255))
        assert wound_px > 800, f"Mixed wound should produce >800 mask pixels, got {wound_px}"

    def test_skin_produces_small_mask(self):
        """
        Bare skin (S≈90) should NOT produce a large wound mask.
        The raised S threshold (120 for red, 100 for yellow) should reject it.
        """
        img = _make_skin_img()
        mask = detect_wound_mask(img)
        wound_px = int(np.sum(mask == 255))
        # Skin may produce a few stray pixels but not a real wound region
        # is_wound_present() will also guard this, but the mask itself should be small
        total_px = img.shape[0] * img.shape[1]
        coverage = wound_px / total_px
        assert coverage < 0.40, (
            f"Skin image produced {coverage:.1%} wound coverage — should be < 40%. "
            "Saturation thresholds may be too low."
        )

    def test_dark_background_produces_no_mask(self):
        img = _dark_canvas()
        mask = detect_wound_mask(img)
        wound_px = int(np.sum(mask == 255))
        assert wound_px == 0, f"Dark canvas should produce zero mask pixels, got {wound_px}"

    def test_mask_is_binary_uint8(self):
        img = _make_red_wound_img()
        mask = detect_wound_mask(img)
        assert mask.dtype == np.uint8
        unique = set(np.unique(mask))
        assert unique.issubset({0, 255}), f"Mask contains non-binary values: {unique}"

    def test_mask_shape_matches_image(self):
        img = _make_red_wound_img(300, 500)
        mask = detect_wound_mask(img)
        assert mask.shape == (300, 500), f"Mask shape {mask.shape} != image shape (300, 500)"


# ===========================================================================
# 2. is_wound_present
# ===========================================================================

class TestIsWoundPresent:
    def _mask_with_pixels(self, n_pixels: int, h: int = 400, w: int = 400) -> np.ndarray:
        mask = np.zeros((h, w), dtype=np.uint8)
        mask.flat[:n_pixels] = 255
        return mask

    def test_too_few_pixels_returns_false(self):
        mask = self._mask_with_pixels(400)  # below min_pixels=500
        assert is_wound_present(mask, (400, 400, 3)) is False

    def test_minimum_pixels_returns_true(self):
        mask = self._mask_with_pixels(600)
        assert is_wound_present(mask, (400, 400, 3)) is True

    def test_full_coverage_returns_false(self):
        """Wound covering >40% of image is likely bare skin / background."""
        mask = np.full((400, 400), 255, dtype=np.uint8)  # 100% coverage
        assert is_wound_present(mask, (400, 400, 3)) is False

    def test_40_percent_coverage_returns_false(self):
        h, w = 400, 400
        total = h * w   # 160 000
        wound_px = int(total * 0.41)  # just over threshold
        mask = self._mask_with_pixels(wound_px, h, w)
        assert is_wound_present(mask, (h, w, 3)) is False

    def test_30_percent_coverage_returns_true(self):
        h, w = 400, 400
        total = h * w
        wound_px = int(total * 0.30)
        mask = self._mask_with_pixels(wound_px, h, w)
        assert is_wound_present(mask, (h, w, 3)) is True

    def test_custom_min_pixels(self):
        mask = self._mask_with_pixels(200)
        assert is_wound_present(mask, (400, 400, 3), min_pixels=100) is True
        assert is_wound_present(mask, (400, 400, 3), min_pixels=500) is False


# ===========================================================================
# 3. analyze_image (file-path API)
# ===========================================================================

class TestAnalyzeImage:
    def test_no_wound_bare_skin(self, tmp_path):
        img = _make_skin_img()
        path = _save_tmp(img, "skin.png", tmp_path)
        result = analyze_image(path)
        assert result["wound_detected"] is False
        assert result["area_cm2"] == 0.0
        assert result["message"] == "No wound detected"

    def test_no_wound_dark_background(self, tmp_path):
        img = _dark_canvas()
        path = _save_tmp(img, "dark.png", tmp_path)
        result = analyze_image(path)
        assert result["wound_detected"] is False

    def test_red_wound_detected(self, tmp_path):
        img = _make_red_wound_img()
        path = _save_tmp(img, "red_wound.png", tmp_path)
        result = analyze_image(path)
        assert result["wound_detected"] is True
        assert result["area_cm2"] > 0.0
        assert result["ryb_ratios"]["red"] > 0.0

    def test_yellow_wound_detected(self, tmp_path):
        """
        Regression: yellow slough must now be detected by analyze_image.
        """
        img = _make_yellow_wound_img()
        path = _save_tmp(img, "yellow_wound.png", tmp_path)
        result = analyze_image(path)
        assert result["wound_detected"] is True, (
            "Yellow-only wound not detected — check detect_wound_mask yellow range."
        )
        assert result["area_cm2"] > 0.0
        assert result["ryb_ratios"]["yellow"] > 0.0, (
            f"Yellow tissue % should be > 0, got {result['ryb_ratios']}"
        )

    def test_mixed_wound_detects_both_tissues(self, tmp_path):
        img = _make_mixed_wound_img()
        path = _save_tmp(img, "mixed_wound.png", tmp_path)
        result = analyze_image(path)
        assert result["wound_detected"] is True
        ryb = result["ryb_ratios"]
        assert ryb["red"] > 0.0,    f"Red should be >0 in mixed wound, got {ryb}"
        assert ryb["yellow"] > 0.0, f"Yellow should be >0 in mixed wound, got {ryb}"

    def test_return_keys_present(self, tmp_path):
        img = _make_red_wound_img()
        path = _save_tmp(img, "keys_test.png", tmp_path)
        result = analyze_image(path)
        for key in ("area_cm2", "ryb_ratios", "annotated_image",
                    "coin_found", "scale_cm_per_px", "wound_detected", "message"):
            assert key in result, f"Missing key: {key}"

    def test_annotated_image_is_ndarray(self, tmp_path):
        img = _make_red_wound_img()
        path = _save_tmp(img, "arr_test.png", tmp_path)
        result = analyze_image(path)
        assert isinstance(result["annotated_image"], np.ndarray)
        assert result["annotated_image"].ndim == 3

    def test_no_wound_annotated_image_has_text(self, tmp_path):
        """No-wound overlay should differ from the raw input (text was drawn)."""
        img = _make_skin_img()
        path = _save_tmp(img, "skin_overlay.png", tmp_path)
        result = analyze_image(path)
        assert not np.array_equal(result["annotated_image"], img), (
            "No-wound overlay should be different from raw input image."
        )

    def test_ryb_ratios_sum_near_100_when_wound(self, tmp_path):
        img = _make_red_wound_img()
        path = _save_tmp(img, "sum_test.png", tmp_path)
        result = analyze_image(path)
        ryb = result["ryb_ratios"]
        total = sum(ryb.values())
        assert abs(total - 100.0) < 1.0, f"RYB ratios should sum to ~100, got {total}"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            analyze_image(str(tmp_path / "nonexistent.png"))


# ===========================================================================
# 4. analyze_frame (real-time numpy array API)
# ===========================================================================

class TestAnalyzeFrame:
    def test_no_wound_bare_skin(self):
        frame = _make_skin_img()
        result = analyze_frame(frame)
        assert result["wound_detected"] is False
        assert result["area_cm2"] == 0.0

    def test_red_wound_detected(self):
        frame = _make_red_wound_img()
        result = analyze_frame(frame)
        assert result["wound_detected"] is True
        assert result["area_cm2"] > 0.0

    def test_yellow_wound_detected(self):
        """Regression: yellow slough must be detected in real-time mode too."""
        frame = _make_yellow_wound_img()
        result = analyze_frame(frame)
        assert result["wound_detected"] is True, (
            "Yellow wound not detected by analyze_frame — check yellow mask range."
        )
        assert result["ryb_ratios"]["yellow"] > 0.0

    def test_mixed_wound_both_tissues(self):
        frame = _make_mixed_wound_img()
        result = analyze_frame(frame)
        assert result["wound_detected"] is True
        ryb = result["ryb_ratios"]
        assert ryb["red"] > 0.0
        assert ryb["yellow"] > 0.0

    def test_no_wound_dark_frame(self):
        frame = _dark_canvas()
        result = analyze_frame(frame)
        assert result["wound_detected"] is False

    def test_return_keys_present(self):
        frame = _make_red_wound_img()
        result = analyze_frame(frame)
        for key in ("area_cm2", "ryb_ratios", "annotated_image",
                    "coin_found", "scale_cm_per_px", "wound_detected", "message"):
            assert key in result, f"Missing key in analyze_frame result: {key}"

    def test_empty_frame_raises(self):
        with pytest.raises(ValueError):
            analyze_frame(np.array([]))

    def test_annotated_image_same_shape_as_input(self):
        frame = _make_red_wound_img(300, 500)
        result = analyze_frame(frame)
        assert result["annotated_image"].shape == frame.shape


# ===========================================================================
# 5. ryb_segment
# ===========================================================================

class TestRybSegment:
    def test_red_dominant_wound(self):
        img = _make_red_wound_img()
        mask = detect_wound_mask(img)
        ratios = ryb_segment(img, mask)
        assert ratios["red"] > 50.0, (
            f"Pure red wound should have red > 50%, got {ratios}"
        )

    def test_yellow_dominant_wound(self):
        """Regression: yellow slough should dominate when the wound is yellow."""
        img = _make_yellow_wound_img()
        mask = detect_wound_mask(img)
        assert int(np.sum(mask == 255)) > 0, "Mask is empty — yellow range not captured"
        ratios = ryb_segment(img, mask)
        assert ratios["yellow"] > 50.0, (
            f"Pure yellow wound should have yellow > 50%, got {ratios}"
        )

    def test_mixed_wound_has_both(self):
        img = _make_mixed_wound_img()
        mask = detect_wound_mask(img)
        ratios = ryb_segment(img, mask)
        assert ratios["red"] > 0.0 and ratios["yellow"] > 0.0, (
            f"Mixed wound should have both red and yellow, got {ratios}"
        )

    def test_ratios_sum_to_100(self):
        img = _make_red_wound_img()
        mask = detect_wound_mask(img)
        ratios = ryb_segment(img, mask)
        total = sum(ratios.values())
        assert abs(total - 100.0) < 1.0, f"RYB ratios should sum to ~100, got {total}"

    def test_too_few_pixels_returns_zeros(self):
        img = _dark_canvas()
        # Tiny mask — fewer than 30 pixels
        mask = np.zeros((400, 400), dtype=np.uint8)
        mask[200, 200] = 255
        ratios = ryb_segment(img, mask)
        assert ratios == {"red": 0.0, "yellow": 0.0, "black": 0.0}

    def test_shape_mismatch_raises(self):
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError, match="img shape"):
            ryb_segment(img, mask)


# ===========================================================================
# 6. _classify_cluster_hsv
# ===========================================================================

class TestClassifyClusterHsv:
    def test_low_value_is_black(self):
        assert _classify_cluster_hsv(np.array([10, 200, 50])) == "black"

    def test_low_saturation_is_black(self):
        assert _classify_cluster_hsv(np.array([10, 40, 180])) == "black"

    def test_red_low_hue(self):
        assert _classify_cluster_hsv(np.array([5, 200, 180])) == "red"

    def test_red_high_hue(self):
        assert _classify_cluster_hsv(np.array([170, 200, 180])) == "red"

    def test_yellow_hue(self):
        assert _classify_cluster_hsv(np.array([28, 200, 200])) == "yellow"

    def test_mid_hue_fallback_yellow(self):
        # H=80 is far from red (≈0 or 180) and closer to yellow (28)
        # fallback: dist_red = min(80, 100)=80, dist_yellow = |80-28|=52 → yellow
        result = _classify_cluster_hsv(np.array([80, 150, 180]))
        assert result == "yellow"


# ===========================================================================
# 7. _derive_alert
# ===========================================================================

class TestDeriveAlert:
    def _patient(self, glucose=120, albumin=3.8, mobility=7, post_op=7):
        return {
            "blood_glucose":  glucose,
            "serum_albumin":  albumin,
            "mobility_score": mobility,
            "post_op_day":    post_op,
        }

    def test_critical_necrosis(self):
        ryb = {"red": 40.0, "yellow": 30.0, "black": 30.0}
        alert = _derive_alert(0.0, ryb, self._patient())
        assert "CRITICAL" in alert

    def test_high_priority_growing_wound(self):
        ryb = {"red": 30.0, "yellow": 50.0, "black": 5.0}  # yellow > 20%
        patient = self._patient(glucose=220)                 # hyperglycemic
        alert = _derive_alert(1.5, ryb, patient)             # delta > 0
        assert "HIGH PRIORITY" in alert

    def test_stall_alert(self):
        ryb = {"red": 60.0, "yellow": 25.0, "black": 5.0}  # yellow > 10%
        alert = _derive_alert(0.0, ryb, self._patient())    # delta == 0
        assert "STALL" in alert

    def test_low_priority_delayed_granulation(self):
        ryb = {"red": 50.0, "yellow": 30.0, "black": 5.0}  # red < 60%
        patient = self._patient(post_op=16)                  # POD > 14
        alert = _derive_alert(-0.5, ryb, patient)            # healing but slow
        assert "LOW PRIORITY" in alert

    def test_on_track_healthy_healing(self):
        ryb = {"red": 75.0, "yellow": 20.0, "black": 5.0}
        alert = _derive_alert(-1.0, ryb, self._patient())
        assert "ON TRACK" in alert


# ===========================================================================
# 8. Demo mode (analyze_patient without image)
# ===========================================================================

class TestDemoMode:
    @pytest.mark.parametrize("pid", ["P001", "P002", "P003", "P004"])
    def test_demo_mode_returns_expected_keys(self, pid):
        result = analyze_patient(pid)
        assert result["demo_mode"] is True
        for key in ("patient", "scan", "area_delta_7d", "wound_history"):
            assert key in result, f"Missing key {key!r} for {pid}"

    def test_demo_mode_scan_has_annotated_image(self):
        result = analyze_patient("P001")
        assert isinstance(result["scan"]["annotated_image"], np.ndarray)
        assert result["scan"]["annotated_image"].ndim == 3

    def test_demo_mode_wound_always_detected(self):
        """Mock patients have real wound data, so wound_detected must be True."""
        for pid in ("P001", "P002", "P003", "P004"):
            result = analyze_patient(pid)
            assert result["scan"]["wound_detected"] is True, (
                f"Demo mode should always report wound_detected=True for {pid}"
            )

    def test_unknown_patient_raises(self):
        with pytest.raises(ValueError, match="Unknown patient_id"):
            analyze_patient("P999")

    def test_p001_healing_trajectory(self):
        """P001 (Maria Santos) should have a negative 7-day area delta."""
        result = analyze_patient("P001")
        assert result["area_delta_7d"] < 0, (
            f"P001 should be healing (negative delta), got {result['area_delta_7d']}"
        )

    def test_p002_stalling_trajectory(self):
        """P002 (James Okafor) should have a positive or zero delta."""
        result = analyze_patient("P002")
        assert result["area_delta_7d"] >= 0, (
            f"P002 should be stalling/growing (non-negative delta), got {result['area_delta_7d']}"
        )
