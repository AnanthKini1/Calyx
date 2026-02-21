"""
create_profile.py — Unified profile creation for patients and doctors.

Role is chosen first, then the appropriate form is shown.
On success, logs the new user in immediately.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, ".."))

import streamlit as st
from utils.patient_store import create_patient, list_patients
from utils.doctor_store import create_doctor, list_doctors, doctor_exists

_COMORBIDITY_OPTIONS = [
    "Type 2 Diabetes",
    "Obesity",
    "Hypertension",
    "Peripheral Artery Disease",
    "Malnutrition",
]

_SPECIALTIES = [
    "Wound Care & Surgery",
    "General Surgery",
    "Plastic Surgery",
    "Vascular Surgery",
    "Internal Medicine",
    "Endocrinology",
    "Orthopedics",
    "Other",
]


def render_create_profile_page() -> None:
    # Back button
    if st.button("← Back to Login", key="create_back"):
        st.session_state["page"] = None
        st.session_state.pop("login_mode", None)
        st.rerun()

    st.markdown(
        """
        <div style="margin: 20px 0 32px; text-align:center;">
            <div style="font-size:24px; font-weight:700; color:#E5E5E5;
                        margin-bottom:8px;">Create Your Profile</div>
            <div style="font-size:14px; color:#505050;">
                Basic information to get you started. You can add more details later.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2.2, 1])

    with center:
        role = st.session_state.get("create_role", None)

        if role is None:
            _render_role_picker()
        elif role == "patient":
            _render_patient_form()
        elif role == "doctor":
            _render_doctor_form()


# ---------------------------------------------------------------------------
# Role picker
# ---------------------------------------------------------------------------

def _render_role_picker() -> None:
    st.markdown(
        '<div style="font-size:14px; color:#606060; text-align:center; margin-bottom:20px;">'
        "I am a…</div>",
        unsafe_allow_html=True,
    )
    col_p, col_d = st.columns(2, gap="medium")
    with col_p:
        if st.button("🩺  Patient", key="pick_patient", use_container_width=True):
            st.session_state["create_role"] = "patient"
            st.rerun()
    with col_d:
        if st.button("👨‍⚕️  Doctor", key="pick_doctor", use_container_width=True):
            st.session_state["create_role"] = "doctor"
            st.rerun()


# ---------------------------------------------------------------------------
# Patient form
# ---------------------------------------------------------------------------

def _render_patient_form() -> None:
    if st.button("← Change Role", key="patient_back_role"):
        st.session_state.pop("create_role", None)
        st.rerun()

    st.markdown(
        '<div style="font-size:12px; color:#8B5CF6; font-weight:600;'
        'letter-spacing:0.10em; text-transform:uppercase; margin:16px 0 20px;">'
        "Patient Profile</div>",
        unsafe_allow_html=True,
    )

    with st.form("patient_create_form"):
        # Personal
        _section_label("Personal")
        col_n, col_a = st.columns([2, 1])
        with col_n:
            name = st.text_input("Full name", placeholder="Your full name")
        with col_a:
            age = st.number_input("Age", min_value=1, max_value=120, value=45, step=1)

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        # Clinical
        _section_label("Clinical (optional — import later)")
        col_g, col_al = st.columns(2)
        with col_g:
            blood_glucose = st.number_input("Blood Glucose (mg/dL)",
                min_value=50.0, max_value=600.0, value=110.0, step=1.0)
        with col_al:
            serum_albumin = st.number_input("Serum Albumin (g/dL)",
                min_value=1.0, max_value=6.0, value=3.8, step=0.1)

        col_m, col_p = st.columns(2)
        with col_m:
            mobility_score = st.slider("Mobility (0 = bedbound, 10 = active)",
                min_value=0, max_value=10, value=7)
        with col_p:
            post_op_day = st.number_input("Days Since Surgery",
                min_value=0, max_value=365, value=7, step=1)

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        # Comorbidities
        _section_label("Conditions (optional)")
        comorbidities = st.multiselect(
            "Select all that apply", _COMORBIDITY_OPTIONS,
            label_visibility="collapsed",
        )

        # Doctor selection
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        _section_label("Your Doctor (optional)")
        doctors = list_doctors()
        doc_options = {d["name"]: d["doctor_id"] for d in doctors}
        doc_choice = st.selectbox(
            "Select doctor", ["— None —"] + list(doc_options.keys()),
            label_visibility="collapsed",
        )
        doctor_id = doc_options.get(doc_choice)

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Create Patient Profile →", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Please enter your full name.")
            return
        try:
            patient = create_patient(
                name=name, age=int(age),
                comorbidities=comorbidities,
                blood_glucose=float(blood_glucose),
                serum_albumin=float(serum_albumin),
                mobility_score=int(mobility_score),
                post_op_day=int(post_op_day),
                doctor_id=doctor_id,
            )
            st.success(f"Welcome, {patient['name']}! Signing you in…")
            _finish_create(patient["patient_id"], "patient")
        except ValueError as e:
            st.error(str(e))


# ---------------------------------------------------------------------------
# Doctor form
# ---------------------------------------------------------------------------

def _render_doctor_form() -> None:
    if st.button("← Change Role", key="doctor_back_role"):
        st.session_state.pop("create_role", None)
        st.rerun()

    st.markdown(
        '<div style="font-size:12px; color:#8B5CF6; font-weight:600;'
        'letter-spacing:0.10em; text-transform:uppercase; margin:16px 0 20px;">'
        "Doctor Profile</div>",
        unsafe_allow_html=True,
    )

    with st.form("doctor_create_form"):
        _section_label("Professional")
        col_n, col_s = st.columns([1, 1])
        with col_n:
            name = st.text_input("Full name (include Dr.)", placeholder="Dr. Jane Smith")
        with col_s:
            specialty = st.selectbox("Specialty", _SPECIALTIES)

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        # Patient selection
        _section_label("Patients You Manage")
        patients = list_patients()
        pat_options = {p["name"]: p["patient_id"] for p in patients}
        selected_patients = st.multiselect(
            "Select your current patients (you can add more later)",
            options=list(pat_options.keys()),
            label_visibility="collapsed",
        )

        st.markdown(
            '<div style="font-size:12px; color:#505050; margin-top:8px; line-height:1.5;">'
            "Don't see your patient? They can select you when creating their profile, "
            "or you can link them later.</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Create Doctor Profile →", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Please enter your full name.")
            return
        patient_ids = [pat_options[n] for n in selected_patients if n in pat_options]
        try:
            doctor = create_doctor(
                name=name, specialty=specialty, patient_ids=patient_ids,
            )
            st.success(f"Welcome, {doctor['name']}!")
            _finish_create(doctor["doctor_id"], "doctor")
        except ValueError as e:
            st.error(str(e))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _section_label(text: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.10em;'
        f'text-transform:uppercase; color:#505050; margin-bottom:10px;">{text}</div>',
        unsafe_allow_html=True,
    )


def _finish_create(user_id: str, role: str) -> None:
    st.session_state["user_id"]   = user_id
    st.session_state["user_role"] = role
    st.session_state.pop("create_role", None)
    st.session_state.pop("page", None)
    st.session_state.pop("login_mode", None)
    st.rerun()
