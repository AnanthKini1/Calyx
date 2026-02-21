"""
patient_form.py — New patient registration form.

Renders a styled form collecting all required health fields.
On submit, calls patient_store.create_patient() and returns the new patient dict,
or None if the form hasn't been submitted yet.
"""

from __future__ import annotations

import sys
import os

_COMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_COMP, "..", ".."))
sys.path.insert(0, os.path.join(_COMP, ".."))

import streamlit as st
from utils.patient_store import create_patient

_COMORBIDITY_OPTIONS = [
    "Type 2 Diabetes",
    "Obesity",
    "Hypertension",
    "Peripheral Artery Disease",
    "Malnutrition",
]


def render_patient_form() -> dict | None:
    """
    Render the new-patient form inside a glass card.
    Returns the created patient dict on success, None otherwise.
    """
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <div style="font-size: 22px; font-weight: 700; color: #E5E5E5;
                        margin-bottom: 6px;">Create Your Profile</div>
            <div style="font-size: 14px; color: #606060; line-height: 1.5;">
                Your health data helps our AI understand your wound healing context.
                All information is stored locally on this device.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("new_patient_form", clear_on_submit=False):
        # ── Personal ────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:11px; font-weight:600; letter-spacing:0.10em;'
            'text-transform:uppercase; color:#8B5CF6; margin-bottom:10px;">Personal</div>',
            unsafe_allow_html=True,
        )
        col_name, col_age = st.columns([2, 1])
        with col_name:
            name = st.text_input("Full name", placeholder="e.g. Jane Smith")
        with col_age:
            age = st.number_input("Age", min_value=1, max_value=120, value=50, step=1)

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        # ── Clinical ─────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:11px; font-weight:600; letter-spacing:0.10em;'
            'text-transform:uppercase; color:#8B5CF6; margin-bottom:10px; margin-top:4px;">'
            'Clinical</div>',
            unsafe_allow_html=True,
        )
        col_glucose, col_albumin = st.columns(2)
        with col_glucose:
            blood_glucose = st.number_input(
                "Blood Glucose (mg/dL)",
                min_value=50.0, max_value=600.0, value=110.0, step=1.0,
                help="Your most recent blood glucose reading.",
            )
        with col_albumin:
            serum_albumin = st.number_input(
                "Serum Albumin (g/dL)",
                min_value=1.0, max_value=6.0, value=3.8, step=0.1,
                help="From recent lab work. Normal range: 3.5 – 5.0 g/dL.",
            )

        col_mobility, col_pod = st.columns(2)
        with col_mobility:
            mobility_score = st.slider(
                "Mobility Score (0 = bedbound, 10 = fully active)",
                min_value=0, max_value=10, value=7,
            )
        with col_pod:
            post_op_day = st.number_input(
                "Days Since Surgery (Post-Op Day)",
                min_value=0, max_value=365, value=7, step=1,
            )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        # ── Comorbidities ────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:11px; font-weight:600; letter-spacing:0.10em;'
            'text-transform:uppercase; color:#8B5CF6; margin-bottom:10px; margin-top:4px;">'
            'Comorbidities</div>',
            unsafe_allow_html=True,
        )
        comorbidities = st.multiselect(
            label="Select all that apply",
            options=_COMORBIDITY_OPTIONS,
            label_visibility="collapsed",
        )

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("Create Profile →", use_container_width=True)

    if submitted:
        if not name or not name.strip():
            st.error("Please enter your full name.")
            return None
        try:
            patient = create_patient(
                name=name,
                age=int(age),
                comorbidities=comorbidities,
                blood_glucose=float(blood_glucose),
                serum_albumin=float(serum_albumin),
                mobility_score=int(mobility_score),
                post_op_day=int(post_op_day),
            )
            return patient
        except ValueError as e:
            st.error(str(e))
            return None

    return None
