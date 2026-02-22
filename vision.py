"""
vision.py — ChroniScan Computer Vision Pipeline

Workflow (real mode):
  1. detect_coin()       → calibration reference (pixel → cm scale)
  2. detect_wound_mask() → isolate wound region via red HSV masking
  3. compute_wound_area()→ area in cm² via contour + scale factor
  4. ryb_segment()       → K-Means tissue classification (Red / Yellow / Black)
  5. draw_overlay()      → annotated BGR numpy array for Streamlit

Demo mode (no image):
  - Uses latest scan from mock_patients.py directly
  - Generates a synthetic coloured ellipse image matching mock RYB ratios
  - Streamlit-ready: `from vision import analyze_patient`
"""

from __future__ import annotations

import sys
import warnings
warnings.filterwarnings("ignore", category=UserWarning)   # suppress scipy/sklearn noise

import cv2
import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, ".")
from data.mock_patients import PATIENTS, get_patient_by_id, get_latest_wound_data, compute_area_delta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COIN_REAL_DIAM_CM: float = 2.426   # US quarter diameter in cm

# RYB overlay colours (BGR)
_COLOUR_RED    = (60,  80, 220)    # granulation tissue
_COLOUR_YELLOW = (0,  210, 240)    # slough
_COLOUR_BLACK  = (35,  35,  35)    # necrosis / eschar

# ---------------------------------------------------------------------------
# Layer 1 — Low-level CV primitives
# ---------------------------------------------------------------------------

def detect_coin(img: np.ndarray) -> tuple | None:
    """
    Detect a circular coin in the image using HoughCircles.

    Returns (cx, cy, radius_px) of the most prominent circle,
    or None if no reliable circle is found.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=60,
        param2=35,
        minRadius=15,
        maxRadius=int(min(img.shape[:2]) // 4),
    )
    if circles is None:
        return None

    # Pick the circle with the highest accumulator score (first returned)
    c = np.round(circles[0, 0]).astype(int)
    return int(c[0]), int(c[1]), int(c[2])   # cx, cy, radius_px


def compute_scale(radius_px: float, real_diam_cm: float = COIN_REAL_DIAM_CM) -> float:
    """Return cm-per-pixel conversion factor from coin radius in pixels."""
    return real_diam_cm / (2.0 * radius_px)


def detect_wound_mask(img: np.ndarray) -> np.ndarray:
    """
    Isolate the wound region by masking wound-coloured pixels in HSV space.

    Captures three tissue colour ranges:
      - Red (granulation): H ∈ [0, 10] or H ∈ [160, 180], S ≥ 120
        S threshold raised to 120 (from 100) to exclude typical skin tones
        (fair/medium skin sits at S ≈ 80-110, well below true wound tissue).
      - Yellow (slough): H ∈ [15, 38], S ≥ 100, V ≥ 100
        Slough was entirely invisible to the old red-only mask.

    Returns a cleaned binary uint8 mask (255 = wound, 0 = background).
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Red — granulation / necrosis borders (wraps around hue wheel)
    # S ≥ 120 keeps us away from skin-tone saturation range (~80-110)
    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0,   120, 80]),  np.array([10,  255, 255])),
        cv2.inRange(hsv, np.array([160, 120, 80]),  np.array([180, 255, 255])),
    )

    # Yellow — slough (fibrinous coating over wound bed)
    # S ≥ 100 excludes pale/washed-out skin tones
    yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([38, 255, 255]))

    mask = cv2.bitwise_or(red_mask, yellow_mask)

    # Morphological cleanup: close small gaps, remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
    return mask


def is_wound_present(mask: np.ndarray, img_shape: tuple, min_pixels: int = 500) -> bool:
    """
    Heuristic guard: return True only when the mask looks like a real wound.

    Two failure modes are rejected:
      - Too few pixels  (<min_pixels) — noise or artefact, not a wound.
      - Too much coverage (>40% of image) — the detector grabbed the whole
        hand or background instead of an isolated wound region.

    min_pixels default of 500 corresponds to roughly a 22×22 px square,
    which at 0.026 cm/px (smartphone fallback) is about 0.34 cm² — well
    below any clinically relevant wound, so genuine wounds are never excluded.
    """
    wound_px = int(np.sum(mask == 255))
    if wound_px < min_pixels:
        return False
    total_px = img_shape[0] * img_shape[1]
    if wound_px / total_px > 0.40:
        return False
    return True


def compute_wound_area(
    mask: np.ndarray, cm_per_px: float
) -> tuple[float, np.ndarray | None]:
    """
    Calculate wound surface area in cm² from a binary mask.

    Finds all external contours, takes the largest by pixel area,
    and converts using cm_per_px² scale factor.

    Returns (area_cm2, largest_contour). contour is None if nothing found.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, None

    largest = max(contours, key=cv2.contourArea)
    area_px2 = cv2.contourArea(largest)
    area_cm2 = area_px2 * (cm_per_px ** 2)
    return round(area_cm2, 2), largest


# ---------------------------------------------------------------------------
# Layer 2 — RYB tissue segmentation via K-Means
# ---------------------------------------------------------------------------

def _classify_cluster_hsv(hsv_centroid: np.ndarray) -> str:
    """
    Map a single K-Means centroid (in HSV [0-180, 0-255, 0-255]) to a
    clinical tissue label: 'red', 'yellow', or 'black'.

    Hue rules (OpenCV halves hue, so 0-180):
      Black  : V < 60
      Red    : H ∈ [0-15] or H ∈ [155-180], S > 60
      Yellow : H ∈ [18-38], S > 60
      Default: closest hue wins
    """
    h, s, v = float(hsv_centroid[0]), float(hsv_centroid[1]), float(hsv_centroid[2])

    if v < 60:
        return "black"
    if s < 60:
        # Low saturation — treat as black tissue (pale/necrotic)
        return "black"
    if h <= 15 or h >= 155:
        return "red"
    if 18 <= h <= 38:
        return "yellow"

    # Fallback: find nearest landmark hue
    dist_red    = min(abs(h - 0), abs(h - 180))
    dist_yellow = abs(h - 28)
    if dist_red <= dist_yellow:
        return "red"
    return "yellow"


def ryb_segment(img: np.ndarray, wound_mask: np.ndarray) -> dict[str, float]:
    """
    Run K-Means (k=3) on wound pixels to separate tissue into
    Granulation (red), Slough (yellow), and Necrosis (black).

    Returns percentages summing to 100.0:
      {"red": float, "yellow": float, "black": float}
    """
    if img.shape[:2] != wound_mask.shape:
        raise ValueError(
            f"ryb_segment: img shape {img.shape[:2]} != mask shape {wound_mask.shape}"
        )

    wound_pixels = img[wound_mask == 255]

    if len(wound_pixels) < 30:
        # Not enough data — return safe defaults
        return {"red": 0.0, "yellow": 0.0, "black": 0.0}

    # Convert wound pixels to HSV for perceptually meaningful clustering
    wound_bgr = wound_pixels.reshape(-1, 1, 3).astype(np.uint8)
    wound_hsv = cv2.cvtColor(wound_bgr, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
    labels = kmeans.fit_predict(wound_hsv.astype(np.float32))
    centroids = kmeans.cluster_centers_

    # Classify each centroid then tally pixel counts per tissue label
    cluster_labels = [_classify_cluster_hsv(c) for c in centroids]
    counts: dict[str, int] = {"red": 0, "yellow": 0, "black": 0}
    for cluster_id in labels:
        counts[cluster_labels[cluster_id]] += 1

    total = len(labels)
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


# ---------------------------------------------------------------------------
# Layer 3 — Overlay rendering
# ---------------------------------------------------------------------------

def draw_overlay(
    img: np.ndarray,
    wound_mask: np.ndarray,
    ryb_pixel_labels: np.ndarray | None,
    coin_info: tuple | None,
    scan_result: dict,
    patient_name: str = "",
) -> np.ndarray:
    """
    Paint the wound pixels with clinical colours and annotate the image.

    ryb_pixel_labels: per-pixel label array ('red'/'yellow'/'black') aligned
                      with wound_mask pixels. Pass None to colour by ratio blocks.

    Returns an annotated BGR numpy array — use cv2.cvtColor(..., COLOR_BGR2RGB)
    before passing to Streamlit's st.image().
    """
    out = img.copy()

    # --- Colour the wound area ---
    if ryb_pixel_labels is not None:
        # Pixel-accurate colouring
        wound_coords = np.where(wound_mask == 255)
        for y, x, label in zip(wound_coords[0], wound_coords[1], ryb_pixel_labels):
            colour = {"red": _COLOUR_RED, "yellow": _COLOUR_YELLOW, "black": _COLOUR_BLACK}[label]
            out[y, x] = colour
    else:
        # Fallback: fill entire wound mask with a blended colour
        out[wound_mask == 255] = _COLOUR_RED

    # --- Draw coin circle ---
    if coin_info is not None:
        cx, cy, r = coin_info
        cv2.circle(out, (cx, cy), r, (0, 255, 80), 2)
        cv2.putText(out, "REF", (cx - 15, cy - r - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 80), 1, cv2.LINE_AA)

    # --- Annotation panel (top-left) ---
    ryb = scan_result.get("ryb_ratios", {})
    lines = [
        patient_name,
        f"Area: {scan_result.get('area_cm2', 0):.2f} cm2",
        f"Red (Granulation): {ryb.get('red', 0):.1f}%",
        f"Yellow (Slough):   {ryb.get('yellow', 0):.1f}%",
        f"Black (Necrosis):  {ryb.get('black', 0):.1f}%",
    ]
    y0, dy = 24, 20
    for i, line in enumerate(lines):
        if not line:
            continue
        y = y0 + i * dy
        cv2.putText(out, line, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(out, line, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (20,  20,  20),  1, cv2.LINE_AA)

    return out


def _make_no_wound_overlay(img: np.ndarray) -> np.ndarray:
    """
    Return an annotated copy of *img* indicating no wound was found.

    Used when is_wound_present() rejects the mask so Streamlit always has
    a displayable image rather than a raw uninformative frame.
    """
    out = img.copy()
    w = out.shape[1]
    # Semi-transparent dark bar at top
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, 46), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.65, out, 0.35, 0, out)

    msg = "No wound detected"
    cv2.putText(out, msg, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(out, msg, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (60, 220, 60),  1, cv2.LINE_AA)
    return out


def _make_demo_overlay(scan: dict, patient: dict) -> np.ndarray:
    """
    Generate a synthetic wound image from mock data when no real photo exists.

    Creates a 420×420 dark canvas with:
      - A coloured ellipse whose axes scale to area_cm2
      - Sub-regions painted Red / Yellow / Black by mock RYB ratios
      - A white coin circle for calibration reference
    """
    canvas = np.full((420, 420, 3), 25, dtype=np.uint8)  # dark grey background
    cx, cy = 210, 210

    area = scan["area_cm2"]
    # Map area to pixel radius: 1 cm² ≈ 30 px radius for demo scale
    r_major = int(np.sqrt(area / np.pi) * 30) + 8
    r_minor = max(int(r_major * 0.75), 5)

    ryb = scan["ryb_ratios"]
    r_pct = ryb.get("red", 60) / 100.0
    y_pct = ryb.get("yellow", 30) / 100.0
    b_pct = ryb.get("black", 10) / 100.0

    # Draw three stacked ellipse bands: red (base), yellow, black
    cv2.ellipse(canvas, (cx, cy), (r_major, r_minor), 0, 0, 360, _COLOUR_RED, -1)
    # Yellow crescent at bottom
    y_extent = int(360 * (y_pct + b_pct))
    if y_extent > 0:
        cv2.ellipse(canvas, (cx, cy), (r_major, r_minor), 0, 180, 180 + y_extent, _COLOUR_YELLOW, -1)
    # Black sub-region at far bottom
    b_extent = int(360 * b_pct)
    if b_extent > 0:
        cv2.ellipse(canvas, (cx, cy), (r_major, r_minor), 0, 200, 200 + b_extent, _COLOUR_BLACK, -1)

    # Coin circle (top-right area)
    coin_r = 22
    cv2.circle(canvas, (360, 60), coin_r, (200, 200, 200), 2)
    cv2.putText(canvas, "25c", (347, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    # Annotations
    name = patient.get("name", "")
    lines = [
        name,
        f"Area: {area:.2f} cm2",
        f"Red (Granulation): {ryb.get('red', 0):.1f}%",
        f"Yellow (Slough):   {ryb.get('yellow', 0):.1f}%",
        f"Black (Necrosis):  {ryb.get('black', 0):.1f}%",
        "[DEMO MODE]",
    ]
    y0, dy = 24, 20
    for i, line in enumerate(lines):
        if not line:
            continue
        y = y0 + i * dy
        cv2.putText(canvas, line, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, line, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20,  20,  20),  1, cv2.LINE_AA)

    return canvas


# ---------------------------------------------------------------------------
# Layer 4 — Public API
# ---------------------------------------------------------------------------

def analyze_image(
    image_path: str,
    coin_diam_cm: float = COIN_REAL_DIAM_CM,
) -> dict:
    """
    Full computer vision pipeline on a real wound photo.

    Returns:
      {
        "area_cm2"       : float,
        "ryb_ratios"     : {"red": %, "yellow": %, "black": %},
        "annotated_image": np.ndarray (BGR),
        "coin_found"     : bool,
        "scale_cm_per_px": float | None,
      }
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    # --- Calibration ---
    coin = detect_coin(img)
    if coin is not None:
        cm_per_px = compute_scale(coin[2], coin_diam_cm)
    else:
        # Fallback: assume 1 px ≈ 0.026 cm (roughly 38 px/cm on a typical smartphone)
        cm_per_px = 0.026

    # --- Wound segmentation ---
    mask = detect_wound_mask(img)

    # --- Guard: reject bare skin and noise ---
    if not is_wound_present(mask, img.shape):
        return {
            "area_cm2":        0.0,
            "ryb_ratios":      {"red": 0.0, "yellow": 0.0, "black": 0.0},
            "annotated_image": _make_no_wound_overlay(img),
            "coin_found":      coin is not None,
            "scale_cm_per_px": cm_per_px,
            "wound_detected":  False,
            "message":         "No wound detected",
        }

    area_cm2, contour = compute_wound_area(mask, cm_per_px)

    # --- RYB tissue analysis ---
    ryb = ryb_segment(img, mask)

    # --- Per-pixel labels for overlay ---
    pixel_labels = None
    wound_coords = np.where(mask == 255)
    if len(wound_coords[0]) > 0:
        wound_pixels = img[wound_coords].reshape(-1, 1, 3).astype(np.uint8)
        wound_hsv = cv2.cvtColor(wound_pixels, cv2.COLOR_BGR2HSV).reshape(-1, 3)
        km = KMeans(n_clusters=3, n_init=10, random_state=42)
        cluster_ids = km.fit_predict(wound_hsv.astype(np.float32))
        cluster_tissue = [_classify_cluster_hsv(c) for c in km.cluster_centers_]
        pixel_labels = np.array([cluster_tissue[cid] for cid in cluster_ids])

    scan_result = {"area_cm2": area_cm2, "ryb_ratios": ryb}
    annotated = draw_overlay(img, mask, pixel_labels, coin, scan_result)

    return {
        "area_cm2":        area_cm2,
        "ryb_ratios":      ryb,
        "annotated_image": annotated,
        "coin_found":      coin is not None,
        "scale_cm_per_px": cm_per_px,
        "wound_detected":  True,
        "message":         "Wound detected",
    }


def analyze_frame(
    frame: np.ndarray,
    coin_diam_cm: float = COIN_REAL_DIAM_CM,
) -> dict:
    """
    Real-time variant of analyze_image() that accepts a BGR numpy array directly.

    Designed for webcam / live-stream use — call with each decoded video frame.
    Returns the same dict as analyze_image() (including wound_detected).

    Streamlit webcam example:
        frame_bgr = cv2.cvtColor(webcam_frame_rgb, cv2.COLOR_RGB2BGR)
        result = analyze_frame(frame_bgr)
        st.image(cv2.cvtColor(result["annotated_image"], cv2.COLOR_BGR2RGB))
    """
    if frame is None or frame.size == 0:
        raise ValueError("analyze_frame: received empty frame")

    coin = detect_coin(frame)
    cm_per_px = compute_scale(coin[2], coin_diam_cm) if coin is not None else 0.026

    mask = detect_wound_mask(frame)

    if not is_wound_present(mask, frame.shape):
        return {
            "area_cm2":        0.0,
            "ryb_ratios":      {"red": 0.0, "yellow": 0.0, "black": 0.0},
            "annotated_image": _make_no_wound_overlay(frame),
            "coin_found":      coin is not None,
            "scale_cm_per_px": cm_per_px,
            "wound_detected":  False,
            "message":         "No wound detected",
        }

    area_cm2, _ = compute_wound_area(mask, cm_per_px)
    ryb = ryb_segment(frame, mask)

    wound_coords = np.where(mask == 255)
    pixel_labels = None
    if len(wound_coords[0]) > 0:
        wound_pixels = frame[wound_coords].reshape(-1, 1, 3).astype(np.uint8)
        wound_hsv = cv2.cvtColor(wound_pixels, cv2.COLOR_BGR2HSV).reshape(-1, 3)
        km = KMeans(n_clusters=3, n_init=10, random_state=42)
        cluster_ids = km.fit_predict(wound_hsv.astype(np.float32))
        cluster_tissue = [_classify_cluster_hsv(c) for c in km.cluster_centers_]
        pixel_labels = np.array([cluster_tissue[cid] for cid in cluster_ids])

    scan_result = {"area_cm2": area_cm2, "ryb_ratios": ryb}
    annotated = draw_overlay(frame, mask, pixel_labels, coin, scan_result)

    return {
        "area_cm2":        area_cm2,
        "ryb_ratios":      ryb,
        "annotated_image": annotated,
        "coin_found":      coin is not None,
        "scale_cm_per_px": cm_per_px,
        "wound_detected":  True,
        "message":         "Wound detected",
    }


def analyze_patient(
    patient_id: str,
    image_path: str | None = None,
    patient_data: dict | None = None,
) -> dict:
    """
    Return a full clinical dict fusing CV scan results with patient data.

    If image_path is None → demo mode: uses latest wound scan from history.
    If image_path is provided → runs the real CV pipeline on that photo.

    patient_data can be supplied directly (e.g. from the JSON store) to avoid
    requiring the patient to exist in the mock PATIENTS list.

    Returns:
      {
        "patient"       : {id, name, age, comorbidities, blood_glucose,
                           serum_albumin, mobility_score, post_op_day},
        "scan"          : {area_cm2, ryb_ratios, annotated_image (BGR ndarray)},
        "area_delta_7d" : float,   # negative = healing, positive = stalling
        "wound_history" : list[dict],
        "demo_mode"     : bool,
      }
    """
    patient = patient_data if patient_data is not None else get_patient_by_id(patient_id)
    if patient is None:
        raise ValueError(f"Unknown patient_id: {patient_id!r}")

    demo_mode = image_path is None

    if demo_mode:
        latest = get_latest_wound_data(patient)
        scan = {
            "area_cm2":       latest["area_cm2"],
            "ryb_ratios":     latest["ryb_ratios"],
            "annotated_image": _make_demo_overlay(latest, patient),
            "wound_detected": True,
        }
    else:
        cv_result = analyze_image(image_path)
        scan = {
            "area_cm2":       cv_result["area_cm2"],
            "ryb_ratios":     cv_result["ryb_ratios"],
            "annotated_image": cv_result["annotated_image"],
            "wound_detected": cv_result["wound_detected"],
        }

    return {
        "patient": {
            "patient_id":     patient["patient_id"],
            "name":           patient["name"],
            "age":            patient["age"],
            "comorbidities":  patient["comorbidities"],
            "blood_glucose":  patient["blood_glucose"],
            "serum_albumin":  patient["serum_albumin"],
            "mobility_score": patient["mobility_score"],
            "post_op_day":    patient["post_op_day"],
        },
        "scan":           scan,
        "area_delta_7d":  compute_area_delta(patient, n_days=7),
        "wound_history":  patient["wound_history"],
        "demo_mode":      demo_mode,
    }


def run_demo() -> list[dict]:
    """
    Run analyze_patient() for all mock patients and print clinical summaries.
    Returns all result dicts (Streamlit can call this too).
    """
    results = []
    sep = "─" * 56

    for patient in PATIENTS:
        pid = patient["patient_id"]
        result = analyze_patient(pid)
        p = result["patient"]
        s = result["scan"]
        delta = result["area_delta_7d"]
        ryb = s["ryb_ratios"]

        # --- Derive a simple alert level ---
        alert = _derive_alert(delta, ryb, p)

        print(sep)
        print(f"  {p['name']}  ({pid})  |  Age {p['age']}  |  POD {p['post_op_day']}")
        print(f"  Comorbidities : {', '.join(p['comorbidities']) or 'None'}")
        print(f"  Glucose       : {p['blood_glucose']} mg/dL   "
              f"Albumin: {p['serum_albumin']} g/dL   "
              f"Mobility: {p['mobility_score']}/10")
        print(f"  Area          : {s['area_cm2']:.2f} cm²   "
              f"Δ7d: {delta:+.2f} cm²")
        print(f"  RYB Tissue    : Red {ryb['red']}%  |  "
              f"Yellow {ryb['yellow']}%  |  Black {ryb['black']}%")
        print(f"  ► {alert}")
        results.append(result)

    print(sep)
    return results


def _derive_alert(delta: float, ryb: dict, patient: dict) -> str:
    """
    Simple rule-based alert for the terminal demo summary.
    The Knowledge Graph module (graph.py) will handle the full reasoning.
    """
    black_pct   = ryb.get("black", 0)
    yellow_pct  = ryb.get("yellow", 0)
    glucose     = patient.get("blood_glucose", 0)
    albumin     = patient.get("serum_albumin", 4.0)
    mobility    = patient.get("mobility_score", 10)

    red_pct    = ryb.get("red", 100)
    post_op    = patient.get("post_op_day", 0)

    if black_pct >= 15:
        return ("CRITICAL: Necrosis >15%. "
                "Immediate surgical review required.")
    if delta > 0 and yellow_pct > 20 and glucose > 180:
        return ("HIGH PRIORITY: Wound growing + high slough + hyperglycemia. "
                "Notify surgical team — dressing change + glucose management.")
    if delta >= 0 and yellow_pct > 10:
        return ("STALL ALERT: No area reduction. "
                "Slough present — evaluate debridement and nutrition.")
    if post_op > 14 and red_pct < 60:
        return ("LOW PRIORITY: Delayed granulation — Red tissue <60% at POD "
                f"{post_op}. Review nutrition and offloading.")
    if albumin < 3.0 and mobility <= 3:
        return ("LOW PRIORITY: Slow healing trajectory. "
                "Low albumin + poor mobility — increase protein intake and repositioning.")
    return "ON TRACK: Healing progressing normally."


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_demo()
