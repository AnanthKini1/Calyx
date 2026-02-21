"""
analysis_bridge.py — Glue between the Streamlit UI and the CV / KG backends.

Takes raw image bytes + a patient dict, runs the full pipeline, and returns
a single unified result dict ready for the results panel to consume.
"""

from __future__ import annotations

import os
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision import analyze_image
from knowledge_graph.reasoning import evaluate_healing
from data.mock_patients import compute_area_delta


def run_analysis(image_bytes: bytes, patient: dict) -> dict:
    """
    Full ChroniScan pipeline for a real captured / uploaded image.

    Parameters
    ----------
    image_bytes : bytes
        Raw JPEG/PNG bytes from camera or file upload.
    patient : dict
        Patient profile dict from mock_patients.PATIENTS.

    Returns
    -------
    dict with keys:
        "cv"        : dict  — vision output (area_cm2, ryb_ratios,
                              annotated_image BGR ndarray, coin_found)
        "kg"        : dict  — reasoning output (priority, alerts,
                              reasoning, active_risk_factors,
                              recommended_action)
        "area_delta": float — 7-day area delta from mock history
        "patient"   : dict  — echo of the patient profile
    """
    # Write bytes to a temp file so OpenCV imread can load it
    suffix = ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        cv_result = analyze_image(tmp_path)
    finally:
        os.unlink(tmp_path)

    area_delta = compute_area_delta(patient, n_days=7)

    kg_result = evaluate_healing(
        area_delta=area_delta,
        tissue_ratios=cv_result["ryb_ratios"],
        health_data=patient,
    )

    return {
        "cv":         cv_result,
        "kg":         kg_result,
        "area_delta": area_delta,
        "patient":    patient,
    }
