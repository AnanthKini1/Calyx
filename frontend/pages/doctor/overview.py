"""
pages/doctor/overview.py — Doctor dashboard home.

Shows:
  • Unreviewed alert count badge
  • Patient roster with latest scan status and priority chip
  • Click a patient row to drill into their detail view
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from utils.doctor_store import get_doctor
from utils.patient_store import list_patients_for_doctor, get_latest_scan, compute_area_delta
from utils.alert_store import get_unreviewed_count, get_alerts_for_patient
from styles.theme import PRIORITY_COLORS, PRIORITY_ICONS, COLORS
from knowledge_graph.reasoning import evaluate_healing


def render_overview_page(doctor_id: str) -> None:
    doctor = get_doctor(doctor_id)
    if doctor is None:
        st.error("Doctor profile not found.")
        return

    patients = list_patients_for_doctor(doctor_id)
    unread   = get_unreviewed_count(doctor_id)

    # ── Page header ───────────────────────────────────────────────────────────
    col_h, col_b = st.columns([3, 1])
    with col_h:
        st.markdown(
            f"""
            <div style="margin-bottom:32px;">
                <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                            letter-spacing:-0.02em; margin-bottom:6px;">
                    Dashboard
                </div>
                <div style="font-size:14px; color:#505050;">
                    {doctor['name']} · {doctor.get('specialty','')} ·
                    {len(patients)} patient{"s" if len(patients) != 1 else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        if unread > 0:
            if st.button(f"🔔 {unread} Alert{'s' if unread != 1 else ''}",
                         key="goto_alerts", use_container_width=True):
                st.session_state["page"] = "alerts"
                st.rerun()

    if not patients:
        st.info("No patients linked to your account yet. "
                "Patients can select you when creating their profile.")
        return

    # ── Patient cards ─────────────────────────────────────────────────────────
    _section("Patient Roster")

    for patient in patients:
        _render_patient_row(patient, doctor_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_patient_row(patient: dict, doctor_id: str) -> None:
    pid      = patient["patient_id"]
    latest   = get_latest_scan(patient)
    delta    = compute_area_delta(patient, n_days=7)
    alerts   = get_alerts_for_patient(pid)
    unread_p = sum(1 for a in alerts if not a["reviewed"])

    # Determine priority from latest scan
    if latest:
        from knowledge_graph.reasoning import evaluate_healing
        kg = evaluate_healing(delta, latest["ryb_ratios"], patient)
        priority = kg["priority"]
    else:
        priority = "OK"

    p_color = PRIORITY_COLORS.get(priority, COLORS["grey_mid"])
    p_icon  = PRIORITY_ICONS.get(priority, "")

    # Area trend
    if delta < -0.1:
        trend_html = f'<span style="color:#34C759;">↓ {abs(delta):.2f} cm²</span>'
    elif delta > 0.1:
        trend_html = f'<span style="color:#FF3B30;">↑ {delta:.2f} cm²</span>'
    else:
        trend_html = '<span style="color:#FFD60A;">→ stable</span>'

    area_str = f"{latest['area_cm2']:.1f} cm²" if latest else "No scans"
    last_date = latest["date"] if latest else "—"

    alert_badge = ""
    if unread_p > 0:
        alert_badge = (
            f'<span style="background:#FF3B30; color:#fff; border-radius:10px;'
            f'padding:2px 8px; font-size:11px; font-weight:700; margin-left:8px;">'
            f'{unread_p}</span>'
        )

    comorbid_tags = "".join(
        f'<span style="background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.25);'
        f'border-radius:5px; padding:2px 7px; font-size:10px; color:#A78BFA; margin-right:4px;">'
        f'{c}</span>'
        for c in patient.get("comorbidities", [])
    )

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; padding:18px 20px; margin-bottom:12px;
                    transition:border-color 0.2s;" onmouseover="this.style.borderColor='rgba(139,92,246,0.3)'"
                    onmouseout="this.style.borderColor='rgba(255,255,255,0.07)'">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;
                        margin-bottom:12px;">
                <div>
                    <div style="font-size:16px; font-weight:600; color:#E5E5E5; margin-bottom:3px;">
                        {patient['name']}{alert_badge}
                    </div>
                    <div style="font-size:12px; color:#505050;">
                        Age {patient['age']} · POD {patient['post_op_day']} · {last_date}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:14px; font-weight:700; color:{p_color};">
                        {p_icon} {priority}
                    </div>
                    <div style="font-size:13px; color:#E5E5E5;">{area_str}</div>
                    <div style="font-size:12px;">{trend_html}</div>
                </div>
            </div>
            <div>{comorbid_tags}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(f"View {patient['name'].split()[0]} →", key=f"view_patient_{pid}",
                 use_container_width=False):
        st.session_state["selected_patient_id"] = pid
        st.session_state["page"] = "patient_detail"
        st.rerun()

    st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)


def _section(label: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        f'text-transform:uppercase; color:#8B5CF6; margin-bottom:16px;">{label}</div>',
        unsafe_allow_html=True,
    )
