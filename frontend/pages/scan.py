"""
scan.py — Main wound scan page.

Two-column layout:
  Left  — Image acquisition (camera / upload)
  Right — CV + KG analysis results (appears after image is captured)

Also persists new scan results to patient_store so they appear in history.
"""

from __future__ import annotations

import sys
import os
from datetime import date

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, ".."))

import streamlit as st
from components.capture import render_capture_panel
from components.results_panel import render_results_panel
from utils.patient_store import get_patient, add_wound_scan


def render_scan_page(patient_id: str) -> None:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found. Please sign out and sign in again.")
        return

    # ── Page header ───────────────────────────────────────────────────────────
    history_count = len(patient.get("wound_history", []))
    st.markdown(
        f"""
        <div style="margin-bottom: 32px;">
            <div style="font-size: 26px; font-weight: 700; color: #E5E5E5;
                        letter-spacing: -0.02em; margin-bottom: 6px;">
                Wound Scan
            </div>
            <div style="font-size: 14px; color: #505050;">
                {patient['name']} · Post-op day {patient['post_op_day']} ·
                {history_count} scan{"s" if history_count != 1 else ""} on record
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        st.markdown(
            '<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
            'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">Capture</div>',
            unsafe_allow_html=True,
        )
        image_bytes = render_capture_panel()

    with right_col:
        if image_bytes is not None:
            st.markdown(
                '<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
                'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">Analysis</div>',
                unsafe_allow_html=True,
            )
            result = render_results_panel(image_bytes, patient)

            # Persist scan result to patient history if new
            if result is not None:
                _maybe_save_scan(patient_id, result)
        else:
            _render_empty_state()


def _render_empty_state() -> None:
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center;
                    justify-content: center; min-height: 380px; text-align: center;
                    border: 1px dashed rgba(139,92,246,0.20); border-radius: 16px;
                    padding: 48px 32px; margin-top: 36px;">
            <div style="font-size: 52px; margin-bottom: 20px; opacity: 0.6;">🔬</div>
            <div style="font-size: 18px; font-weight: 600; color: #E5E5E5;
                        margin-bottom: 10px;">Ready to Scan</div>
            <div style="font-size: 14px; color: #505050; line-height: 1.7;
                        max-width: 280px;">
                Use the camera on the left to capture a wound photo,
                or upload an existing image.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _maybe_save_scan(patient_id: str, result: dict) -> None:
    """Save the scan to patient history if it hasn't been saved yet this session."""
    save_key = f"scan_saved_{patient_id}_{hash(str(result.get('cv', {}).get('area_cm2')))}"
    if save_key in st.session_state:
        return

    try:
        scan_entry = {
            "date":       date.today().isoformat(),
            "area_cm2":   result["cv"]["area_cm2"],
            "ryb_ratios": result["cv"]["ryb_ratios"],
        }
        add_wound_scan(patient_id, scan_entry)
        st.session_state[save_key] = True
    except Exception:
        pass  # Non-critical — don't surface save errors to the user
