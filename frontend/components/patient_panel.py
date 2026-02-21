"""
patient_panel.py — Sidebar patient selector and health profile display.

Renders:
  1. A selectbox to choose the active patient
  2. A glass-card health profile showing vitals and comorbidities
  3. Current wound summary (area, tissue ratios from latest scan)

Returns (patient_data dict, selected_patient dict | None).
"""

from __future__ import annotations

import sys
import os

_COMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_COMP, "..", ".."))  # project root
sys.path.insert(0, os.path.join(_COMP, ".."))        # frontend root

import streamlit as st
from data.mock_patients import PATIENTS, get_latest_wound_data, compute_area_delta
from styles.theme import COLORS, PRIORITY_COLORS


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_patient_panel() -> tuple[list[dict], dict | None]:
    """
    Render the sidebar patient selector and return (all_patients, selected).
    selected is None if the user has not chosen one yet.
    """
    st.markdown('<p class="section-label">Patient</p>', unsafe_allow_html=True)

    options = {f"{p['name']}  ({p['patient_id']})": p for p in PATIENTS}
    options_list = ["— Select patient —"] + list(options.keys())

    choice = st.selectbox(
        label="Select patient",
        options=options_list,
        label_visibility="collapsed",
        key="patient_selector",
    )

    selected = options.get(choice)

    if selected:
        _render_health_profile(selected)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        _render_latest_scan_summary(selected)

    return PATIENTS, selected


# ---------------------------------------------------------------------------
# Internal renderers
# ---------------------------------------------------------------------------

def _render_health_profile(patient: dict) -> None:
    """Glass card with patient vitals and comorbidities."""
    glucose   = patient["blood_glucose"]
    albumin   = patient["serum_albumin"]
    mobility  = patient["mobility_score"]
    post_op   = patient["post_op_day"]
    age       = patient["age"]
    comorbids = patient.get("comorbidities", [])

    glucose_color  = COLORS["critical"] if glucose > 180 else (COLORS["medium"] if glucose > 140 else COLORS["ok"])
    albumin_color  = COLORS["critical"] if albumin < 3.0 else (COLORS["medium"] if albumin < 3.5 else COLORS["ok"])
    mobility_color = COLORS["critical"] if mobility < 3   else (COLORS["medium"] if mobility < 6  else COLORS["ok"])

    comorbid_html = ""
    if comorbids:
        comorbid_html = "".join(
            f'<span style="display:inline-block; background:rgba(139,92,246,0.15);'
            f'border:1px solid rgba(139,92,246,0.30); border-radius:6px;'
            f'padding:2px 8px; font-size:11px; color:#A78BFA; margin:2px 2px 2px 0;">'
            f"{c}</span>"
            for c in comorbids
        )
    else:
        comorbid_html = '<span style="font-size:12px;color:#505050;">None recorded</span>'

    st.markdown(
        f"""
        <div class="glass-card" style="margin-top:12px;">
            <div style="display:flex; justify-content:space-between; align-items:baseline;
                        margin-bottom:14px;">
                <div>
                    <div style="font-size:17px; font-weight:600; color:#E5E5E5;">
                        {patient['name']}
                    </div>
                    <div style="font-size:12px; color:#505050;">
                        Age {age} · Post-op day {post_op}
                    </div>
                </div>
                <div style="font-size:11px; color:#505050; font-family:monospace;">
                    {patient['patient_id']}
                </div>
            </div>

            <!-- Vitals grid -->
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px;">
                {_vital_tile("Glucose", f"{glucose:.0f}", "mg/dL", glucose_color)}
                {_vital_tile("Albumin", f"{albumin:.1f}", "g/dL",  albumin_color)}
                {_vital_tile("Mobility", f"{mobility}/10", "",     mobility_color)}
                {_vital_tile("POD", str(post_op), "days", COLORS['grey_mid'])}
            </div>

            <!-- Comorbidities -->
            <div style="font-size:11px; font-weight:600; letter-spacing:0.08em;
                        text-transform:uppercase; color:#505050; margin-bottom:6px;">
                Comorbidities
            </div>
            <div>{comorbid_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _vital_tile(label: str, value: str, unit: str, color: str) -> str:
    return (
        f'<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);'
        f'border-radius:10px; padding:10px 12px;">'
        f'<div style="font-size:10px; color:#505050; font-weight:600; text-transform:uppercase;'
        f'letter-spacing:0.07em; margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:18px; font-weight:700; color:{color}; line-height:1;">{value}</div>'
        f'<div style="font-size:10px; color:#404040;">{unit}</div>'
        f"</div>"
    )


def _render_latest_scan_summary(patient: dict) -> None:
    """Show area delta and tissue bars from the most recent mock scan."""
    st.markdown('<p class="section-label">Latest Scan</p>', unsafe_allow_html=True)

    latest = get_latest_wound_data(patient)
    delta  = compute_area_delta(patient, n_days=7)
    ryb    = latest["ryb_ratios"]
    area   = latest["area_cm2"]

    # Delta indicator
    if delta < -0.1:
        delta_color = COLORS["ok"]
        delta_icon  = "↓"
        delta_label = "Healing"
    elif delta > 0.1:
        delta_color = COLORS["critical"]
        delta_icon  = "↑"
        delta_label = "Stalling"
    else:
        delta_color = COLORS["medium"]
        delta_icon  = "→"
        delta_label = "Unchanged"

    st.markdown(
        f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center;
                        margin-bottom:14px;">
                <div>
                    <div style="font-size:22px; font-weight:700; color:#E5E5E5;">{area:.1f}
                        <span style="font-size:13px; font-weight:400; color:#505050;">cm²</span>
                    </div>
                    <div style="font-size:11px; color:#505050;">{latest['date']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:20px; font-weight:700; color:{delta_color};">
                        {delta_icon} {abs(delta):.2f}
                        <span style="font-size:12px; font-weight:400;">cm²</span>
                    </div>
                    <div style="font-size:11px; color:{delta_color};">{delta_label} (7d)</div>
                </div>
            </div>
            {_tissue_bars(ryb)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tissue_bars(ryb: dict) -> str:
    red    = ryb.get("red", 0)
    yellow = ryb.get("yellow", 0)
    black  = ryb.get("black", 0)

    def row(label: str, pct: float, dot_color: str, bar_color: str) -> str:
        return (
            f'<div class="ryb-row">'
            f'<div class="ryb-dot" style="background:{dot_color};"></div>'
            f'<div class="ryb-label">{label}</div>'
            f'<div class="ryb-value">{pct:.1f}%</div>'
            f"</div>"
            f'<div style="height:5px; border-radius:4px; overflow:hidden;'
            f'background:rgba(255,255,255,0.05); margin-bottom:8px;">'
            f'<div style="width:{pct}%; height:100%; background:{bar_color};'
            f'border-radius:4px;"></div>'
            f"</div>"
        )

    return (
        row("Granulation (Red)",  red,    "#E05252", "linear-gradient(90deg,#C0392B,#E74C3C)")
        + row("Slough (Yellow)",  yellow, "#D4AA3A", "linear-gradient(90deg,#D4AA3A,#F1C40F)")
        + row("Necrosis (Black)", black,  "#555555", "linear-gradient(90deg,#2C2C2C,#555)")
    )
