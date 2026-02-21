"""
pages/patient/import_history.py — Medical history file import.

Accepts PDF, CSV, or JSON. Extracted fields are previewed before
the patient confirms applying them to their profile.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from utils.patient_store import get_patient, update_patient_fields
from utils.medical_importer import parse_file

_FIELD_LABELS = {
    "blood_glucose":  ("Blood Glucose",   "mg/dL"),
    "serum_albumin":  ("Serum Albumin",   "g/dL"),
    "mobility_score": ("Mobility Score",  "/10"),
    "post_op_day":    ("Post-Op Day",     "days"),
    "age":            ("Age",             "yrs"),
    "comorbidities":  ("Comorbidities",   ""),
}


def render_import_page(patient_id: str) -> None:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found.")
        return

    st.markdown(
        """
        <div style="margin-bottom:32px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:6px;">Import Medical History</div>
            <div style="font-size:14px; color:#505050;">
                Upload a file from your hospital or clinic. We'll extract your
                clinical data and update your profile automatically.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Format guide ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:rgba(139,92,246,0.06); border:1px solid rgba(139,92,246,0.20);
                    border-radius:14px; padding:18px 20px; margin-bottom:28px;">
            <div style="font-size:12px; font-weight:600; color:#A78BFA;
                        letter-spacing:0.08em; text-transform:uppercase; margin-bottom:10px;">
                Accepted Formats</div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;
                        font-size:13px; color:#808080;">
                <div>
                    <div style="font-weight:600; color:#E5E5E5; margin-bottom:4px;">📄 PDF</div>
                    Discharge summaries, lab reports, clinic notes
                </div>
                <div>
                    <div style="font-weight:600; color:#E5E5E5; margin-bottom:4px;">📊 CSV</div>
                    Lab result exports, health app exports
                </div>
                <div>
                    <div style="font-weight:600; color:#E5E5E5; margin-bottom:4px;">🗂 JSON</div>
                    EHR exports, Apple Health, structured records
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── File uploader ─────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload your medical history file",
        type=["pdf", "csv", "json"],
        label_visibility="collapsed",
        key="medical_history_upload",
    )

    if uploaded is None:
        return

    # ── Parse ─────────────────────────────────────────────────────────────────
    parse_key = f"parsed_{patient_id}_{uploaded.name}_{uploaded.size}"
    if parse_key not in st.session_state:
        with st.spinner("Parsing your file…"):
            result = parse_file(uploaded.getvalue(), uploaded.name)
        st.session_state[parse_key] = result
    else:
        result = st.session_state[parse_key]

    extracted = result["extracted"]
    warnings  = result["warnings"]

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── Warnings ──────────────────────────────────────────────────────────────
    if warnings:
        for w in warnings:
            st.markdown(
                f'<div style="background:rgba(255,149,0,0.10); border:1px solid rgba(255,149,0,0.30);'
                f'border-radius:8px; padding:10px 14px; font-size:13px; color:#FFAD33;'
                f'margin-bottom:8px;">⚠ {w}</div>',
                unsafe_allow_html=True,
            )

    if not extracted:
        st.error("No recognisable clinical fields found in this file. Try a different format or enter your data manually on the Profile page.")
        return

    # ── Preview ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">Extracted Data</div>',
        unsafe_allow_html=True,
    )

    rows_html = ""
    for field, value in extracted.items():
        label, unit = _FIELD_LABELS.get(field, (field.replace("_", " ").title(), ""))
        current_val = patient.get(field, "—")
        if isinstance(value, list):
            val_str = ", ".join(value) or "None"
            cur_str = ", ".join(current_val) if isinstance(current_val, list) else str(current_val)
        else:
            val_str = f"{value} {unit}".strip()
            cur_str = f"{current_val} {unit}".strip() if current_val != "—" else "—"

        changed = str(value) != str(current_val)
        badge = (
            '<span style="font-size:10px; background:rgba(52,199,89,0.15);'
            'border:1px solid rgba(52,199,89,0.3); border-radius:4px; padding:1px 6px;'
            'color:#34C759; margin-left:6px;">NEW</span>'
            if changed else ""
        )
        rows_html += f"""
        <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="padding:12px 14px; color:#A0A0A0; font-size:13px;">{label}</td>
            <td style="padding:12px 14px; color:#505050; font-size:12px;">{cur_str}</td>
            <td style="padding:12px 14px; color:#E5E5E5; font-size:13px;
                       font-weight:600;">{val_str}{badge}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; overflow:hidden; margin-bottom:20px;">
            <table style="width:100%; border-collapse:collapse;">
                <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
                    <th style="padding:12px 14px; text-align:left; color:#404040; font-size:11px;
                               font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">Field</th>
                    <th style="padding:12px 14px; text-align:left; color:#404040; font-size:11px;
                               font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">Current</th>
                    <th style="padding:12px 14px; text-align:left; color:#404040; font-size:11px;
                               font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">From File</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Apply button ──────────────────────────────────────────────────────────
    apply_key = f"applied_{parse_key}"
    if apply_key in st.session_state:
        st.success("✓ Profile updated from imported file.")
        return

    if st.button("Apply to My Profile →", use_container_width=True, key="apply_import_btn"):
        patch = {k: v for k, v in extracted.items() if k != "comorbidities"}
        if "comorbidities" in extracted:
            existing = set(patient.get("comorbidities", []))
            merged = list(existing | set(extracted["comorbidities"]))
            patch["comorbidities"] = merged
        patch["imported_history"] = {"source": uploaded.name, "fields": list(extracted.keys())}
        try:
            update_patient_fields(patient_id, patch)
            st.session_state[apply_key] = True
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update profile: {e}")
