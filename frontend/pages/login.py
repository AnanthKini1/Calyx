"""
login.py — Role-selection landing and sign-in gate.

Three paths:
  1. Patient Sign In  — pick name from patient list
  2. Doctor Sign In   — pick name from doctor list
  3. Create Profile   — choose role → fill form (in create_profile.py)
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, ".."))

import streamlit as st
from utils.patient_store import list_patients
from utils.doctor_store import list_doctors


def render_login_page() -> None:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 56px 0 40px;">
            <div style="font-size:12px; font-weight:600; letter-spacing:0.20em;
                        text-transform:uppercase; color:#8B5CF6; margin-bottom:16px;">
                Wound Intelligence Platform
            </div>
            <p class="hero-title" style="font-size:58px; margin-bottom:18px;">
                ChroniScan
            </p>
            <div style="font-size:16px; color:#404040; max-width:460px;
                        margin:0 auto; line-height:1.7;">
                Sub-visual wound analysis powered by computer vision
                and clinical knowledge graphs.
            </div>
        </div>
        <div class="divider" style="max-width:580px; margin:0 auto 44px;"></div>
        """,
        unsafe_allow_html=True,
    )

    # ── Three-button role selector ─────────────────────────────────────────────
    _, center, _ = st.columns([1, 2.2, 1])

    with center:
        mode = st.session_state.get("login_mode", None)

        if mode is None:
            _render_role_cards()
        elif mode == "patient":
            _render_patient_signin()
        elif mode == "doctor":
            _render_doctor_signin()
        elif mode == "create":
            st.session_state["page"] = "create_profile"
            st.rerun()

    # Footer
    st.markdown(
        '<div style="text-align:center; margin-top:52px; font-size:11px; color:#303030;">'
        "For clinical demo purposes only · Data stored locally</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Role card selector
# ---------------------------------------------------------------------------

def _render_role_cards() -> None:
    st.markdown(
        '<div style="font-size:15px; font-weight:500; color:#606060;'
        'text-align:center; margin-bottom:24px;">Who are you?</div>',
        unsafe_allow_html=True,
    )

    col_p, col_d = st.columns(2, gap="medium")

    with col_p:
        st.markdown(
            """
            <div style="background:rgba(139,92,246,0.06);
                        border:1px solid rgba(139,92,246,0.25); border-radius:16px;
                        padding:28px 20px; text-align:center; margin-bottom:12px;">
                <div style="font-size:36px; margin-bottom:10px;">🩺</div>
                <div style="font-size:15px; font-weight:600; color:#E5E5E5;
                            margin-bottom:6px;">Patient</div>
                <div style="font-size:12px; color:#606060; line-height:1.5;">
                    Scan wounds, track healing,<br>view your history
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign in as Patient", key="btn_patient", use_container_width=True):
            st.session_state["login_mode"] = "patient"
            st.rerun()

    with col_d:
        st.markdown(
            """
            <div style="background:rgba(255,255,255,0.03);
                        border:1px solid rgba(255,255,255,0.09); border-radius:16px;
                        padding:28px 20px; text-align:center; margin-bottom:12px;">
                <div style="font-size:36px; margin-bottom:10px;">👨‍⚕️</div>
                <div style="font-size:15px; font-weight:600; color:#E5E5E5;
                            margin-bottom:6px;">Doctor</div>
                <div style="font-size:12px; color:#606060; line-height:1.5;">
                    Monitor patients, review<br>alerts, track progress
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign in as Doctor", key="btn_doctor", use_container_width=True):
            st.session_state["login_mode"] = "doctor"
            st.rerun()

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align:center; color:#404040; font-size:13px; margin-bottom:8px;">'
        "— or —</div>",
        unsafe_allow_html=True,
    )

    if st.button("✨  Create New Profile", key="btn_create", use_container_width=True):
        st.session_state["login_mode"] = "create"
        st.rerun()


# ---------------------------------------------------------------------------
# Patient sign-in
# ---------------------------------------------------------------------------

def _render_patient_signin() -> None:
    _back_btn()
    st.markdown(
        '<div style="font-size:18px; font-weight:600; color:#E5E5E5; margin:16px 0 6px;">'
        "Patient Sign In</div>"
        '<div style="font-size:13px; color:#606060; margin-bottom:20px;">'
        "Select your name to access your dashboard.</div>",
        unsafe_allow_html=True,
    )

    patients = list_patients()
    if not patients:
        st.info("No patient profiles yet. Create one first.")
        return

    options = {p["name"]: p for p in patients}
    choice = st.selectbox(
        "Your name", ["— Select your name —"] + list(options.keys()),
        label_visibility="collapsed",
    )
    selected = options.get(choice)

    if selected:
        _patient_preview_card(selected)
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("Sign In →", key="patient_signin_confirm", use_container_width=True):
            _login(selected["patient_id"], "patient")

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; font-size:12px; color:#404040;">'
        "Don't have an account? "
        '<span style="color:#8B5CF6; cursor:pointer;">Create a profile</span></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Doctor sign-in
# ---------------------------------------------------------------------------

def _render_doctor_signin() -> None:
    _back_btn()
    st.markdown(
        '<div style="font-size:18px; font-weight:600; color:#E5E5E5; margin:16px 0 6px;">'
        "Doctor Sign In</div>"
        '<div style="font-size:13px; color:#606060; margin-bottom:20px;">'
        "Select your name to access the clinical dashboard.</div>",
        unsafe_allow_html=True,
    )

    doctors = list_doctors()
    if not doctors:
        st.info("No doctor profiles yet. Create one first.")
        return

    options = {d["name"]: d for d in doctors}
    choice = st.selectbox(
        "Your name", ["— Select your name —"] + list(options.keys()),
        label_visibility="collapsed",
    )
    selected = options.get(choice)

    if selected:
        _doctor_preview_card(selected)
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        if st.button("Sign In →", key="doctor_signin_confirm", use_container_width=True):
            _login(selected["doctor_id"], "doctor")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _back_btn() -> None:
    if st.button("← Back", key="back_btn"):
        st.session_state["login_mode"] = None
        st.rerun()


def _login(user_id: str, role: str) -> None:
    st.session_state["user_id"]   = user_id
    st.session_state["user_role"] = role
    st.session_state.pop("login_mode", None)
    st.session_state.pop("page", None)
    st.session_state.pop("captured_image", None)
    st.session_state.pop("capture_source", None)
    st.rerun()


def _patient_preview_card(p: dict) -> None:
    comorbids = ", ".join(p.get("comorbidities", [])) or "None"
    scans = len(p.get("wound_history", []))
    st.markdown(
        f"""
        <div style="background:rgba(139,92,246,0.06);
                    border:1px solid rgba(139,92,246,0.22);
                    border-radius:12px; padding:16px 18px; margin-top:10px;">
            <div style="font-size:15px; font-weight:600; color:#E5E5E5;
                        margin-bottom:8px;">{p['name']}</div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr;
                        gap:6px; font-size:12px;">
                <div><span style="color:#505050;">Age</span>
                     <span style="color:#E5E5E5; margin-left:5px;">{p['age']}</span></div>
                <div><span style="color:#505050;">POD</span>
                     <span style="color:#E5E5E5; margin-left:5px;">{p['post_op_day']}</span></div>
                <div><span style="color:#505050;">Scans</span>
                     <span style="color:#E5E5E5; margin-left:5px;">{scans}</span></div>
            </div>
            <div style="margin-top:8px; font-size:12px; color:#505050;">
                Conditions: <span style="color:#A78BFA;">{comorbids}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _doctor_preview_card(d: dict) -> None:
    n_patients = len(d.get("patient_ids", []))
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.10);
                    border-radius:12px; padding:16px 18px; margin-top:10px;">
            <div style="font-size:15px; font-weight:600; color:#E5E5E5;
                        margin-bottom:6px;">{d['name']}</div>
            <div style="font-size:12px; color:#606060; margin-bottom:8px;">
                {d.get('specialty', 'Medicine')}
            </div>
            <div style="font-size:12px; color:#505050;">
                Monitoring
                <span style="color:#A78BFA; font-weight:600;">{n_patients}</span>
                patient{"s" if n_patients != 1 else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
