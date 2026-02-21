"""
components/doctor_sidebar.py — Sidebar for logged-in doctors.

Navigation: Dashboard | Alerts | (patient detail injected dynamically)
Below nav: doctor mini-profile + unread alert badge.
"""

from __future__ import annotations

import sys
import os

_COMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_COMP, "..", ".."))
sys.path.insert(0, os.path.join(_COMP, ".."))

import streamlit as st
from utils.doctor_store import get_doctor
from utils.patient_store import list_patients_for_doctor
from utils.alert_store import get_unreviewed_count

_NAV = [
    ("🏥", "Dashboard", "overview"),
    ("🔔", "Alerts",    "alerts"),
]


def render_doctor_sidebar(doctor_id: str) -> str:
    doctor = get_doctor(doctor_id)
    if doctor is None:
        st.error("Session error.")
        return "overview"

    unread = get_unreviewed_count(doctor_id)

    # Logo
    st.markdown(
        '<p class="hero-title" style="font-size:26px;">ChroniScan</p>'
        '<p class="hero-sub" style="font-size:12px; margin-bottom:0;">Clinical Dashboard</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Nav
    current = st.session_state.get("page", "overview")
    for icon, label, key in _NAV:
        badge = f"  🔴 {unread}" if key == "alerts" and unread > 0 else ""
        clicked = st.button(f"{icon}  {label}{badge}", key=f"nav_{key}", use_container_width=True)
        if clicked:
            st.session_state["page"] = key
            st.session_state.pop("selected_patient_id", None)
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Doctor mini card
    _render_doctor_card(doctor, unread)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # Sign out
    if st.button("Sign Out", key="doctor_signout", use_container_width=True):
        _clear_session()
        st.rerun()

    return current


def _render_doctor_card(doctor: dict, unread: int) -> None:
    patients = list_patients_for_doctor(doctor["doctor_id"])
    n = len(patients)

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
                    border-radius:12px; padding:14px;">
            <div style="font-size:14px; font-weight:600; color:#E5E5E5; margin-bottom:2px;">
                {doctor['name']}</div>
            <div style="font-size:11px; color:#404040; margin-bottom:12px;">
                {doctor.get('specialty','Medicine')}</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                <div style="background:rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:8px 10px;">
                    <div style="font-size:9px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:3px;">
                        Patients</div>
                    <div style="font-size:20px; font-weight:700; color:#A78BFA;">{n}</div>
                </div>
                <div style="background:{"rgba(255,59,48,0.10)" if unread > 0 else "rgba(255,255,255,0.03)"};
                    border:1px solid {"rgba(255,59,48,0.30)" if unread > 0 else "rgba(255,255,255,0.06)"};
                    border-radius:8px; padding:8px 10px;">
                    <div style="font-size:9px; color:#404040; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:3px;">
                        Alerts</div>
                    <div style="font-size:20px; font-weight:700;
                        color:{"#FF6B63" if unread > 0 else "#505050"};">{unread}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _clear_session() -> None:
    for key in ["user_id", "user_role", "page", "selected_patient_id",
                "login_mode", "create_role"]:
        st.session_state.pop(key, None)
