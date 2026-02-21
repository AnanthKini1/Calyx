"""
pages/doctor/patient_detail.py — Doctor view of a single patient.

Shows full profile, wound history trend, scan log, and any alerts.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from components.trend_chart import render_trend_chart
from utils.patient_store import get_patient, compute_area_delta, get_latest_scan
from utils.alert_store import get_alerts_for_patient, mark_reviewed
from styles.theme import PRIORITY_COLORS, COLORS, PRIORITY_ICONS


def render_patient_detail_page(patient_id: str) -> None:
    if st.button("← Back to Dashboard", key="detail_back"):
        st.session_state.pop("selected_patient_id", None)
        st.session_state["page"] = "overview"
        st.rerun()

    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found.")
        return

    alerts  = get_alerts_for_patient(patient_id)
    delta   = compute_area_delta(patient, n_days=7)
    latest  = get_latest_scan(patient)
    history = patient.get("wound_history", [])

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="margin-bottom:28px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:4px;">
                {patient['name']}
            </div>
            <div style="font-size:13px; color:#505050;">
                Age {patient['age']} · Post-op day {patient['post_op_day']} ·
                {len(history)} scan{"s" if len(history) != 1 else ""} recorded
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.1, 1], gap="large")

    # ── Left: vitals + comorbidities ─────────────────────────────────────────
    with left:
        _section("Clinical Profile")
        _render_vitals(patient)

        if latest:
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            _section("Latest Scan")
            _render_latest(latest, delta)

    # ── Right: alerts ─────────────────────────────────────────────────────────
    with right:
        unread = sum(1 for a in alerts if not a["reviewed"])
        _section(f"Alerts ({len(alerts)}" + (f" · {unread} unreviewed" if unread else "") + ")")

        if not alerts:
            st.markdown(
                '<div style="font-size:13px; color:#404040; padding:16px 0;">'
                "No alerts raised for this patient.</div>",
                unsafe_allow_html=True,
            )
        else:
            for alert in alerts[:10]:
                _render_alert_card(alert)

    # ── Trend chart ───────────────────────────────────────────────────────────
    if len(history) >= 2:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        _section("Healing Trajectory")
        render_trend_chart(patient)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _render_vitals(patient: dict) -> None:
    glucose  = patient["blood_glucose"]
    albumin  = patient["serum_albumin"]
    mobility = patient["mobility_score"]
    pod      = patient["post_op_day"]
    comorbids = patient.get("comorbidities", [])

    gc = COLORS["critical"] if glucose > 180 else (COLORS["medium"] if glucose > 140 else COLORS["ok"])
    ac = COLORS["critical"] if albumin < 3.0  else (COLORS["medium"] if albumin < 3.5  else COLORS["ok"])
    mc = COLORS["critical"] if mobility < 3   else (COLORS["medium"] if mobility < 6   else COLORS["ok"])

    def chip(label: str, val: str, color: str) -> str:
        return (
            f'<div style="background:rgba(255,255,255,0.03);'
            f'border:1px solid rgba(255,255,255,0.07); border-radius:10px;'
            f'padding:10px 12px;">'
            f'<div style="font-size:10px; color:#404040; font-weight:600;'
            f'text-transform:uppercase; letter-spacing:0.07em; margin-bottom:4px;">{label}</div>'
            f'<div style="font-size:18px; font-weight:700; color:{color}; line-height:1;">{val}</div>'
            f'</div>'
        )

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
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:14px;">
                {chip("Glucose", f"{glucose:.0f} mg/dL", gc)}
                {chip("Albumin", f"{albumin:.1f} g/dL", ac)}
                {chip("Mobility", f"{mobility}/10", mc)}
                {chip("POD", f"{pod}d", COLORS['grey_mid'])}
            </div>
            <div style="font-size:10px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:6px;">
                Comorbidities</div>
            <div>{comorbid_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_latest(scan: dict, delta: float) -> None:
    ryb   = scan.get("ryb_ratios", {})
    red, yellow, black = ryb.get("red", 0), ryb.get("yellow", 0), ryb.get("black", 0)
    area  = scan.get("area_cm2", 0)

    if delta < -0.1:
        dc, di = COLORS["ok"], "↓"
    elif delta > 0.1:
        dc, di = COLORS["critical"], "↑"
    else:
        dc, di = COLORS["medium"], "→"

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; padding:16px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                <div>
                    <div style="font-size:22px; font-weight:700; color:#E5E5E5;">
                        {area:.2f}<span style="font-size:13px; color:#505050;"> cm²</span></div>
                    <div style="font-size:11px; color:#505050;">{scan.get('date','')}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:18px; font-weight:700; color:{dc};">
                        {di} {abs(delta):.2f}</div>
                    <div style="font-size:10px; color:{dc};">7-day trend</div>
                </div>
            </div>
            <div style="height:6px; border-radius:4px; overflow:hidden; display:flex; gap:1px;">
                <div style="flex:{red}; background:#E74C3C; border-radius:4px 0 0 4px;"></div>
                <div style="flex:{yellow}; background:#F1C40F;"></div>
                <div style="flex:{black}; background:#555; border-radius:0 4px 4px 0;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px;
                        color:#505050; margin-top:5px;">
                <span style="color:#E74C3C;">{red:.0f}% red</span>
                <span style="color:#F1C40F;">{yellow:.0f}% yellow</span>
                <span style="color:#888;">{black:.0f}% black</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_alert_card(alert: dict) -> None:
    priority  = alert["priority"]
    p_color   = PRIORITY_COLORS.get(priority, COLORS["grey_mid"])
    reviewed  = alert["reviewed"]
    alpha     = "0.5" if reviewed else "1.0"
    ts        = alert["timestamp"][:16].replace("T", " ")
    alert_id  = alert["alert_id"]

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.06);
                    border-left:3px solid {p_color}; border-radius:10px;
                    padding:14px 16px; margin-bottom:10px; opacity:{alpha};">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <div style="font-size:12px; font-weight:700; color:{p_color};">{priority}</div>
                <div style="font-size:11px; color:#404040;">{ts}</div>
            </div>
            <div style="font-size:13px; color:#C0C0C0; margin-bottom:{"10px" if not reviewed else "0"};">
                {alert['message']}
            </div>
            {"<div style='font-size:11px; color:#505050; margin-top:6px;'>✓ Reviewed · " + (alert.get('doctor_notes') or "no notes") + "</div>" if reviewed else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not reviewed:
        col_notes, col_btn = st.columns([3, 1])
        with col_notes:
            notes = st.text_input(
                "Notes", placeholder="Add clinical notes…",
                key=f"notes_{alert_id}", label_visibility="collapsed",
            )
        with col_btn:
            if st.button("Mark Reviewed", key=f"review_{alert_id}", use_container_width=True):
                mark_reviewed(alert_id, notes)
                st.rerun()

    st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)


def _section(label: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        f'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">{label}</div>',
        unsafe_allow_html=True,
    )
