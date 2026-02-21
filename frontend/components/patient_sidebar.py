"""
components/patient_sidebar.py — Sidebar for logged-in patients.

Navigation: Scan | History | Growth | Import
Below nav: mini profile card + latest scan summary.
"""

from __future__ import annotations

import sys
import os

_COMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_COMP, "..", ".."))
sys.path.insert(0, os.path.join(_COMP, ".."))

import streamlit as st
from styles.theme import COLORS
from utils.patient_store import get_patient, compute_area_delta, get_latest_scan

_NAV = [
    ("🔬", "Scan",            "scan"),
    ("📈", "History",         "history"),
    ("🌱", "Recovery Growth", "growth"),
    ("📁", "Import History",  "import"),
]


def render_patient_sidebar(patient_id: str) -> str:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Session error.")
        return "scan"

    # Logo
    st.markdown(
        '<p class="hero-title" style="font-size:26px;">ChroniScan</p>'
        '<p class="hero-sub" style="font-size:12px; margin-bottom:0;">Patient Portal</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Nav
    current = st.session_state.get("page", "scan")
    for icon, label, key in _NAV:
        clicked = st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True)
        if clicked:
            st.session_state["page"] = key
            # Clear any captured image state when navigating away from scan
            if key != "scan":
                st.session_state.pop("captured_image", None)
                st.session_state.pop("capture_source", None)
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Mini profile
    _render_mini_profile(patient)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # Sign out
    if st.button("Sign Out", key="patient_signout", use_container_width=True):
        _clear_session()
        st.rerun()

    return current


def _render_mini_profile(patient: dict) -> None:
    latest = get_latest_scan(patient)
    delta  = compute_area_delta(patient, n_days=7) if latest else 0

    glucose  = patient["blood_glucose"]
    albumin  = patient["serum_albumin"]
    mobility = patient["mobility_score"]

    gc = COLORS["critical"] if glucose > 180 else (COLORS["medium"] if glucose > 140 else COLORS["ok"])
    ac = COLORS["critical"] if albumin < 3.0  else (COLORS["medium"] if albumin < 3.5  else COLORS["ok"])
    mc = COLORS["critical"] if mobility < 3   else (COLORS["medium"] if mobility < 6   else COLORS["ok"])

    if delta < -0.1:
        d_color, d_icon = COLORS["ok"], "↓"
    elif delta > 0.1:
        d_color, d_icon = COLORS["critical"], "↑"
    else:
        d_color, d_icon = COLORS["medium"], "→"

    area_str = f"{latest['area_cm2']:.1f} cm²" if latest else "No scans"

    def chip(label: str, val: str, color: str) -> str:
        return (
            f'<div style="background:rgba(255,255,255,0.03);'
            f'border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:8px 10px;">'
            f'<div style="font-size:9px; color:#404040; font-weight:600;'
            f'text-transform:uppercase; letter-spacing:0.07em; margin-bottom:3px;">{label}</div>'
            f'<div style="font-size:14px; font-weight:700; color:{color}; line-height:1;">{val}</div>'
            f'</div>'
        )

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
                    border-radius:12px; padding:14px;">
            <div style="font-size:14px; font-weight:600; color:#E5E5E5; margin-bottom:2px;">
                {patient['name']}</div>
            <div style="font-size:11px; color:#404040; margin-bottom:12px;">
                POD {patient['post_op_day']}</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:12px;">
                {chip("Glucose", f"{glucose:.0f}", gc)}
                {chip("Albumin", f"{albumin:.1f}", ac)}
                {chip("Mobility", f"{mobility}/10", mc)}
                <div style="background:rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:8px 10px;">
                    <div style="font-size:9px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:3px;">
                        Area</div>
                    <div style="font-size:13px; font-weight:700; color:#E5E5E5; line-height:1;">
                        {area_str}</div>
                    <div style="font-size:10px; color:{d_color};">{d_icon} 7d</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _clear_session() -> None:
    for key in ["user_id", "user_role", "page", "captured_image",
                "capture_source", "login_mode", "create_role"]:
        st.session_state.pop(key, None)
    to_remove = [k for k in st.session_state
                 if k.startswith(("analysis_", "scan_saved_", "alert_raised_",
                                  "parsed_", "applied_"))]
    for k in to_remove:
        del st.session_state[k]
