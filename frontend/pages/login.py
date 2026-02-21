"""
login.py — Patient identity gate.

Shown when no patient is logged in. Lets the user either:
  A) Select themselves from the existing patient list (demo patients included)
  B) Create a brand-new patient profile via the registration form

On success, sets st.session_state["patient_id"] and triggers a rerun
so app.py can route to the main scan view.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, ".."))

import streamlit as st
from utils.patient_store import list_patients
from components.patient_form import render_patient_form


def render_login_page() -> None:
    """Full-screen login / registration view."""

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align: center; padding: 48px 0 36px;">
            <div style="font-size: 13px; font-weight: 600; letter-spacing: 0.18em;
                        text-transform: uppercase; color: #8B5CF6; margin-bottom: 14px;">
                Wound Intelligence Platform
            </div>
            <p class="hero-title" style="font-size: 52px; line-height: 1.08;
               margin-bottom: 16px;">ChroniScan</p>
            <div style="font-size: 16px; color: #505050; max-width: 480px;
                        margin: 0 auto; line-height: 1.6;">
                Remote early-warning for post-operative and chronic wound care.
                Powered by computer vision and clinical knowledge graphs.
            </div>
        </div>
        <div class="divider" style="max-width: 560px; margin: 0 auto 40px;"></div>
        """,
        unsafe_allow_html=True,
    )

    # ── Centered container ────────────────────────────────────────────────────
    _, center, _ = st.columns([1, 2, 1])

    with center:
        tab_select, tab_create = st.tabs(["👤  Sign In", "✨  New Patient"])

        # ── Sign In ───────────────────────────────────────────────────────────
        with tab_select:
            st.markdown(
                '<div style="font-size:14px; color:#606060; margin: 16px 0 20px;">'
                "Select your name to access your wound tracking dashboard."
                "</div>",
                unsafe_allow_html=True,
            )

            patients = list_patients()
            if not patients:
                st.info("No patients yet — create your profile in the New Patient tab.")
            else:
                options = {f"{p['name']}": p for p in patients}
                choice = st.selectbox(
                    label="Your name",
                    options=["— Select your name —"] + list(options.keys()),
                    label_visibility="collapsed",
                )

                selected = options.get(choice)
                if selected:
                    _render_patient_preview(selected)

                    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
                    if st.button("Sign In →", use_container_width=True, key="signin_btn"):
                        _login(selected["patient_id"])

        # ── New Patient ───────────────────────────────────────────────────────
        with tab_create:
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
            new_patient = render_patient_form()
            if new_patient is not None:
                st.success(f"Profile created! Welcome, {new_patient['name']}.")
                _login(new_patient["patient_id"])

    # ── Footer note ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; margin-top: 48px; font-size: 12px; color: #303030;">
            For clinical demo purposes only · Data stored locally
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(patient_id: str) -> None:
    st.session_state["patient_id"] = patient_id
    st.session_state.pop("page", None)          # reset to default scan page
    st.session_state.pop("captured_image", None)
    st.session_state.pop("capture_source", None)
    st.rerun()


def _render_patient_preview(patient: dict) -> None:
    """Small info card shown when a name is selected."""
    comorbids = ", ".join(patient.get("comorbidities", [])) or "None"
    st.markdown(
        f"""
        <div style="background: rgba(139,92,246,0.06);
                    border: 1px solid rgba(139,92,246,0.22);
                    border-radius: 12px; padding: 16px 18px; margin-top: 12px;">
            <div style="display: flex; justify-content: space-between;
                        align-items: baseline; margin-bottom: 10px;">
                <div style="font-size: 16px; font-weight: 600; color: #E5E5E5;">
                    {patient['name']}
                </div>
                <div style="font-size: 11px; color: #505050; font-family: monospace;">
                    {patient['patient_id']}
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr;
                        gap: 8px; font-size: 12px;">
                <div><span style="color:#606060;">Age</span>
                     <span style="color:#E5E5E5; margin-left:6px; font-weight:600;">
                     {patient['age']}</span></div>
                <div><span style="color:#606060;">POD</span>
                     <span style="color:#E5E5E5; margin-left:6px; font-weight:600;">
                     {patient['post_op_day']}</span></div>
                <div><span style="color:#606060;">Scans</span>
                     <span style="color:#E5E5E5; margin-left:6px; font-weight:600;">
                     {len(patient.get('wound_history', []))}</span></div>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #606060;">
                Conditions: <span style="color: #A78BFA;">{comorbids}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
