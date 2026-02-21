"""
app.py — ChroniScan Streamlit frontend entry point.

Routing:
  • No patient_id in session → login/register page (full screen)
  • patient_id set, page == "scan"    → scan page (camera + results)
  • patient_id set, page == "history" → history page (chart + table)

Run with:
    streamlit run frontend/app.py
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))  # project root
sys.path.insert(0, _HERE)                       # frontend root

import streamlit as st

from styles.theme import inject_css
from pages.login import render_login_page
from pages.scan import render_scan_page
from pages.history import render_history_page
from components.profile_sidebar import render_profile_sidebar

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------

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

patient_id = st.session_state.get("patient_id")

if not patient_id:
    # ── Unauthenticated — full-screen login ───────────────────────────────────
    # Hide sidebar entirely on login screen
    st.markdown(
        "<style>[data-testid='stSidebar'] { display: none; }</style>",
        unsafe_allow_html=True,
    )
    render_login_page()

else:
    # ── Authenticated — sidebar + page router ─────────────────────────────────
    with st.sidebar:
        current_page = render_profile_sidebar(patient_id)

    st.session_state["page"] = current_page

    if current_page == "scan":
        render_scan_page(patient_id)
    elif current_page == "history":
        render_history_page(patient_id)
    else:
        render_scan_page(patient_id)
