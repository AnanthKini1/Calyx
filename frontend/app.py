"""
app.py — ChroniScan entry point and role-based router.

Session state keys:
  user_id   — patient_id or doctor_id of the logged-in user
  user_role — "patient" | "doctor"
  page      — active page key (role-specific)

Run with:
    streamlit run frontend/app.py
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))   # project root
sys.path.insert(0, _HERE)                        # frontend root

import streamlit as st
from styles.theme import inject_css

st.set_page_config(
    page_title="ChroniScan",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

user_id   = st.session_state.get("user_id")
user_role = st.session_state.get("user_role")

# ── Unauthenticated ───────────────────────────────────────────────────────────
if not user_id:
    st.markdown(
        "<style>[data-testid='stSidebar'] { display: none; }</style>",
        unsafe_allow_html=True,
    )
    page = st.session_state.get("page")
    if page == "create_profile":
        from pages.create_profile import render_create_profile_page
        render_create_profile_page()
    else:
        from pages.login import render_login_page
        render_login_page()

# ── Patient ───────────────────────────────────────────────────────────────────
elif user_role == "patient":
    from components.patient_sidebar import render_patient_sidebar
    from pages.patient.scan import render_scan_page
    from pages.patient.history import render_history_page
    from pages.patient.growth import render_growth_page
    from pages.patient.import_history import render_import_page

    with st.sidebar:
        current = render_patient_sidebar(user_id)
    st.session_state["page"] = current

    if current == "scan":
        render_scan_page(user_id)
    elif current == "history":
        render_history_page(user_id)
    elif current == "growth":
        render_growth_page(user_id)
    elif current == "import":
        render_import_page(user_id)
    else:
        render_scan_page(user_id)

# ── Doctor ────────────────────────────────────────────────────────────────────
elif user_role == "doctor":
    from components.doctor_sidebar import render_doctor_sidebar
    from pages.doctor.overview import render_overview_page
    from pages.doctor.alerts import render_alerts_page
    from pages.doctor.patient_detail import render_patient_detail_page

    with st.sidebar:
        current = render_doctor_sidebar(user_id)
    st.session_state["page"] = current

    selected_pid = st.session_state.get("selected_patient_id")

    if current == "patient_detail" and selected_pid:
        render_patient_detail_page(selected_pid)
    elif current == "alerts":
        render_alerts_page(user_id)
    else:
        render_overview_page(user_id)

# ── Bad state — clear and restart ─────────────────────────────────────────────
else:
    st.session_state.clear()
    st.rerun()
