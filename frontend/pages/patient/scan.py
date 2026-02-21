"""
pages/patient/scan.py — Patient wound scan page.

After each scan:
  • Saves result to patient history
  • If KG priority is CRITICAL or HIGH → raises an alert to the patient's doctor
"""

from __future__ import annotations

import sys
import os
from datetime import date

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from components.capture import render_capture_panel
from components.results_panel import render_results_panel
from utils.patient_store import get_patient, add_wound_scan
from utils.alert_store import raise_alert, alert_already_raised, ALERT_PRIORITIES


def render_scan_page(patient_id: str) -> None:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found.")
        return

    n_scans = len(patient.get("wound_history", []))

    st.markdown(
        f"""
        <div style="margin-bottom:32px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:6px;">Wound Scan</div>
            <div style="font-size:14px; color:#505050;">
                {patient['name']} · Post-op day {patient['post_op_day']} ·
                {n_scans} scan{"s" if n_scans != 1 else ""} on record
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        _label("Capture")
        image_bytes = render_capture_panel()

    with right_col:
        if image_bytes is not None:
            _label("Analysis")
            result = render_results_panel(image_bytes, patient)
            if result is not None:
                _persist_and_alert(patient, result)
        else:
            _empty_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(text: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        f'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">{text}</div>',
        unsafe_allow_html=True,
    )


def _empty_state() -> None:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; align-items:center;
                    justify-content:center; min-height:380px; text-align:center;
                    border:1px dashed rgba(139,92,246,0.20); border-radius:16px;
                    padding:48px 32px; margin-top:36px;">
            <div style="font-size:52px; margin-bottom:20px; opacity:0.5;">🔬</div>
            <div style="font-size:18px; font-weight:600; color:#E5E5E5;
                        margin-bottom:10px;">Ready to Scan</div>
            <div style="font-size:14px; color:#505050; line-height:1.7;
                        max-width:280px;">
                Use the camera on the left to capture a wound photo,
                or upload an existing image to begin.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _persist_and_alert(patient: dict, result: dict) -> None:
    pid   = patient["patient_id"]
    today = date.today().isoformat()

    # Save scan (once per image per session)
    save_key = f"scan_saved_{pid}_{hash(str(result['cv'].get('area_cm2')))}"
    if save_key not in st.session_state:
        try:
            add_wound_scan(pid, {
                "date":       today,
                "area_cm2":   result["cv"]["area_cm2"],
                "ryb_ratios": result["cv"]["ryb_ratios"],
            })
            st.session_state[save_key] = True
        except Exception:
            pass

    # Raise alert if warranted
    priority = result["kg"].get("priority", "OK")
    if priority in ALERT_PRIORITIES:
        doctor_id = patient.get("doctor_id")
        alert_key = f"alert_raised_{pid}_{today}_{priority}"
        if alert_key not in st.session_state:
            if not alert_already_raised(pid, today, priority):
                message = result["kg"].get("alerts", ["Alert triggered"])[0]
                try:
                    raise_alert(
                        patient_id=pid,
                        doctor_id=doctor_id,
                        priority=priority,
                        message=message,
                        scan_data={
                            "area_cm2":   result["cv"]["area_cm2"],
                            "ryb_ratios": result["cv"]["ryb_ratios"],
                            "area_delta": result["area_delta"],
                        },
                    )
                    st.session_state[alert_key] = True
                    _show_alert_sent_banner(priority, doctor_id)
                except Exception:
                    pass
            else:
                st.session_state[alert_key] = True


def _show_alert_sent_banner(priority: str, doctor_id: str | None) -> None:
    color = "#FF3B30" if priority == "CRITICAL" else "#FF9500"
    label = "CRITICAL" if priority == "CRITICAL" else "HIGH PRIORITY"
    doc_note = "Your doctor has been notified." if doctor_id else "No doctor linked — alert stored."
    st.markdown(
        f"""
        <div style="background:rgba(255,59,48,0.10); border:1px solid {color};
                    border-radius:12px; padding:14px 18px; margin-top:12px;">
            <div style="font-size:13px; font-weight:700; color:{color};
                        margin-bottom:4px;">🚨 {label} Alert Raised</div>
            <div style="font-size:12px; color:#A0A0A0;">{doc_note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
