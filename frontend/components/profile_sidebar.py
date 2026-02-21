"""
profile_sidebar.py — Sidebar content for a logged-in patient.

Shows the patient's health profile (vitals + comorbidities) and the
navigation menu. No patient-switching controls — each user only sees
their own data.
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


_NAV_ITEMS = [
    ("🔬", "Scan",    "scan"),
    ("📈", "History", "history"),
]


def render_profile_sidebar(patient_id: str) -> str:
    """
    Render the logged-in sidebar.
    Returns the currently active page key ("scan" | "history").
    """
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Session error — please sign out.")
        return "scan"

    # ── Logo ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<p class="hero-title" style="font-size:28px;">ChroniScan</p>'
        '<p class="hero-sub" style="margin-bottom:0;">Wound Intelligence</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────────────────────────
    current_page = st.session_state.get("page", "scan")

    for icon, label, key in _NAV_ITEMS:
        is_active = current_page == key
        btn_style = (
            "background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.35);"
            if is_active
            else "background: transparent; border: 1px solid transparent;"
        )
        label_color = "#A78BFA" if is_active else "#606060"

        # Render as styled button via HTML + Streamlit button trick
        clicked = st.button(
            f"{icon}  {label}",
            key=f"nav_{key}",
            use_container_width=True,
        )
        if clicked:
            st.session_state["page"] = key
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Patient profile card ──────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:11px; font-weight:600; letter-spacing:0.10em;'
        'text-transform:uppercase; color:#404040; margin-bottom:12px;">My Profile</div>',
        unsafe_allow_html=True,
    )
    _render_vitals(patient)

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    # ── Latest scan summary ───────────────────────────────────────────────────
    latest = get_latest_scan(patient)
    if latest:
        _render_latest_summary(latest, patient)

    # ── Logout ────────────────────────────────────────────────────────────────
    st.markdown('<div style="flex:1;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

    if st.button("Sign Out", key="logout_btn", use_container_width=True):
        for key in ["patient_id", "page", "captured_image", "capture_source"]:
            st.session_state.pop(key, None)
        # Clear any cached analysis results
        keys_to_remove = [k for k in st.session_state if k.startswith("analysis_") or k.startswith("scan_saved_")]
        for k in keys_to_remove:
            del st.session_state[k]
        st.rerun()

    return current_page


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _vital_chip(label: str, value: str, color: str) -> str:
    return (
        f'<div style="background:rgba(255,255,255,0.03);'
        f'border:1px solid rgba(255,255,255,0.07); border-radius:10px;'
        f'padding:10px 12px;">'
        f'<div style="font-size:10px; color:#404040; font-weight:600;'
        f'text-transform:uppercase; letter-spacing:0.07em; margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:17px; font-weight:700; color:{color}; line-height:1;">{value}</div>'
        f'</div>'
    )


def _render_vitals(patient: dict) -> None:
    glucose  = patient["blood_glucose"]
    albumin  = patient["serum_albumin"]
    mobility = patient["mobility_score"]
    pod      = patient["post_op_day"]
    comorbids = patient.get("comorbidities", [])

    gc = COLORS["critical"] if glucose > 180 else (COLORS["medium"] if glucose > 140 else COLORS["ok"])
    ac = COLORS["critical"] if albumin < 3.0  else (COLORS["medium"] if albumin < 3.5  else COLORS["ok"])
    mc = COLORS["critical"] if mobility < 3   else (COLORS["medium"] if mobility < 6   else COLORS["ok"])

    comorbid_html = "".join(
        f'<span style="display:inline-block; background:rgba(139,92,246,0.12);'
        f'border:1px solid rgba(139,92,246,0.25); border-radius:5px;'
        f'padding:2px 7px; font-size:10px; color:#A78BFA; margin:2px 2px 2px 0;">'
        f"{c}</span>"
        for c in comorbids
    ) or '<span style="font-size:11px; color:#404040;">None recorded</span>'

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; padding:16px; margin-bottom:8px;">
            <div style="font-size:15px; font-weight:600; color:#E5E5E5; margin-bottom:2px;">
                {patient['name']}
            </div>
            <div style="font-size:11px; color:#404040; margin-bottom:14px;">
                Age {patient['age']} · Post-op day {pod}
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px;">
                {_vital_chip("Glucose", f"{glucose:.0f} mg/dL", gc)}
                {_vital_chip("Albumin", f"{albumin:.1f} g/dL", ac)}
                {_vital_chip("Mobility", f"{mobility}/10", mc)}
                {_vital_chip("POD", f"{pod}d", COLORS['grey_mid'])}
            </div>
            <div style="font-size:10px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em;
                        margin-bottom:6px;">Conditions</div>
            <div>{comorbid_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_latest_summary(scan: dict, patient: dict) -> None:
    delta = compute_area_delta(patient, n_days=7)
    ryb   = scan.get("ryb_ratios", {})
    area  = scan.get("area_cm2", 0)

    if delta < -0.1:
        d_color, d_icon, d_label = COLORS["ok"],       "↓", "Healing"
    elif delta > 0.1:
        d_color, d_icon, d_label = COLORS["critical"], "↑", "Stalling"
    else:
        d_color, d_icon, d_label = COLORS["medium"],   "→", "Stable"

    red    = ryb.get("red", 0)
    yellow = ryb.get("yellow", 0)
    black  = ryb.get("black", 0)

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; padding:16px;">
            <div style="font-size:10px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em;
                        margin-bottom:10px;">Latest Scan</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                <div>
                    <div style="font-size:20px; font-weight:700; color:#E5E5E5;">
                        {area:.1f}
                        <span style="font-size:12px; font-weight:400; color:#404040;">cm²</span>
                    </div>
                    <div style="font-size:10px; color:#404040;">{scan.get('date', '')}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:17px; font-weight:700; color:{d_color};">
                        {d_icon} {abs(delta):.1f}
                    </div>
                    <div style="font-size:10px; color:{d_color};">{d_label}</div>
                </div>
            </div>
            <div style="height:6px; border-radius:4px; overflow:hidden; display:flex; gap:1px;">
                <div style="flex:{red}; background:#E74C3C; border-radius:4px 0 0 4px;"></div>
                <div style="flex:{yellow}; background:#F1C40F;"></div>
                <div style="flex:{black}; background:#555; border-radius:0 4px 4px 0;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:10px;
                        color:#404040; margin-top:5px;">
                <span style="color:#E74C3C;">{red:.0f}% red</span>
                <span style="color:#F1C40F;">{yellow:.0f}% yellow</span>
                <span style="color:#888;">{black:.0f}% black</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
