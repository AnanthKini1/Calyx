"""
pages/doctor/alerts.py — Doctor alerts management panel.

All alerts raised by the doctor's patients, newest first.
Doctor can review each alert and add clinical notes.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from utils.alert_store import get_alerts_for_doctor, mark_reviewed
from utils.patient_store import get_patient
from utils.doctor_store import get_doctor
from styles.theme import PRIORITY_COLORS, COLORS


def render_alerts_page(doctor_id: str) -> None:
    doctor  = get_doctor(doctor_id)
    alerts  = get_alerts_for_doctor(doctor_id)
    unread  = sum(1 for a in alerts if not a["reviewed"])

    st.markdown(
        f"""
        <div style="margin-bottom:32px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:6px;">
                Patient Alerts
            </div>
            <div style="font-size:14px; color:#505050;">
                {len(alerts)} total · {unread} unreviewed
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not alerts:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; min-height:300px; text-align:center;
                        border:1px dashed rgba(139,92,246,0.20); border-radius:16px; padding:48px;">
                <div style="font-size:48px; opacity:0.4; margin-bottom:16px;">🔔</div>
                <div style="font-size:16px; font-weight:600; color:#505050;">No Alerts</div>
                <div style="font-size:13px; color:#404040; margin-top:8px;">
                    Alerts appear here when a patient scan hits CRITICAL or HIGH priority.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Filter ────────────────────────────────────────────────────────────────
    show_reviewed = st.checkbox("Show reviewed alerts", value=False, key="show_reviewed_chk")
    filtered = alerts if show_reviewed else [a for a in alerts if not a["reviewed"]]

    if not filtered:
        st.markdown(
            '<div style="font-size:14px; color:#505050; padding:24px 0; text-align:center;">'
            "All alerts reviewed. Toggle above to see history.</div>",
            unsafe_allow_html=True,
        )
        return

    for alert in filtered:
        _render_alert(alert)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _render_alert(alert: dict) -> None:
    priority  = alert["priority"]
    p_color   = PRIORITY_COLORS.get(priority, COLORS["grey_mid"])
    reviewed  = alert["reviewed"]
    ts        = alert["timestamp"][:16].replace("T", " ")
    alert_id  = alert["alert_id"]

    patient = get_patient(alert["patient_id"])
    pat_name = patient["name"] if patient else "Unknown Patient"

    alpha = "0.55" if reviewed else "1.0"

    # Scan data summary
    scan = alert.get("scan_data", {})
    area   = scan.get("area_cm2", 0)
    delta  = scan.get("area_delta", 0)
    ryb    = scan.get("ryb_ratios", {})
    red, yellow, black = ryb.get("red",0), ryb.get("yellow",0), ryb.get("black",0)

    trend = f"↑ +{delta:.2f}" if delta > 0.1 else (f"↓ {delta:.2f}" if delta < -0.1 else "→ stable")
    trend_color = "#FF3B30" if delta > 0.1 else ("#34C759" if delta < -0.1 else "#FFD60A")

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.025);
                    border:1px solid rgba(255,255,255,0.06);
                    border-left:4px solid {p_color}; border-radius:12px;
                    padding:18px 20px; margin-bottom:14px; opacity:{alpha};">
            <!-- Header row -->
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start; margin-bottom:12px;">
                <div>
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                        <span style="font-size:13px; font-weight:700; color:{p_color};
                                     letter-spacing:0.05em;">{priority}</span>
                        <span style="font-size:14px; font-weight:600; color:#E5E5E5;">
                            {pat_name}</span>
                        {"<span style='font-size:11px; color:#34C759;'>✓ Reviewed</span>" if reviewed else ""}
                    </div>
                    <div style="font-size:12px; color:#505050;">{ts}</div>
                </div>
                <div style="text-align:right; font-size:13px;">
                    <span style="color:#E5E5E5;">{area:.2f} cm²</span>
                    <span style="color:{trend_color}; margin-left:8px;">{trend}</span>
                </div>
            </div>
            <!-- Alert message -->
            <div style="font-size:13px; color:#C0C0C0; margin-bottom:12px;">
                {alert['message']}
            </div>
            <!-- Tissue bar -->
            <div style="height:6px; border-radius:4px; overflow:hidden; display:flex; gap:1px;
                        margin-bottom:8px;">
                <div style="flex:{red}; background:#E74C3C; border-radius:4px 0 0 4px;"></div>
                <div style="flex:{yellow}; background:#F1C40F;"></div>
                <div style="flex:{black}; background:#555; border-radius:0 4px 4px 0;"></div>
            </div>
            <div style="font-size:11px; color:#505050;">
                <span style="color:#E74C3C;">{red:.0f}% red</span> ·
                <span style="color:#F1C40F;">{yellow:.0f}% yellow</span> ·
                <span style="color:#888;">{black:.0f}% black</span>
            </div>
            {f'<div style="margin-top:10px; font-size:12px; color:#606060;"><b>Notes:</b> {alert.get("doctor_notes","")}</div>' if reviewed and alert.get("doctor_notes") else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not reviewed:
        btn_col, nav_col, notes_col = st.columns([1, 1, 2])
        with notes_col:
            notes = st.text_input(
                "Clinical notes", placeholder="Add notes before reviewing…",
                key=f"alert_notes_{alert_id}", label_visibility="collapsed",
            )
        with btn_col:
            if st.button("✓ Mark Reviewed", key=f"mark_{alert_id}", use_container_width=True):
                mark_reviewed(alert_id, notes)
                st.rerun()
        with nav_col:
            if st.button(f"View Patient →", key=f"nav_patient_{alert_id}", use_container_width=True):
                st.session_state["selected_patient_id"] = alert["patient_id"]
                st.session_state["page"] = "patient_detail"
                st.rerun()

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
