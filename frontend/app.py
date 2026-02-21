"""
app.py — ChroniScan Streamlit frontend entry point.

Run with:
    streamlit run frontend/app.py
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
# Project root → vision, knowledge_graph, data packages
sys.path.insert(0, os.path.join(_HERE, ".."))
# Frontend root → styles, components, utils packages
sys.path.insert(0, _HERE)

import streamlit as st

from styles.theme import inject_css
from components.capture import render_capture_panel
from components.patient_panel import render_patient_panel
from components.results_panel import render_results_panel
from components.trend_chart import render_trend_chart

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
# Sidebar — patient selector + health profile
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<p class="hero-title">ChroniScan</p>'
        '<p class="hero-sub">Wound Intelligence Platform</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    patient_data, selected_patient = render_patient_panel()

# ---------------------------------------------------------------------------
# Main area — two-column layout
# ---------------------------------------------------------------------------

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    st.markdown('<p class="section-label">Wound Capture</p>', unsafe_allow_html=True)
    image_bytes = render_capture_panel()

with right_col:
    if image_bytes is not None and selected_patient is not None:
        st.markdown('<p class="section-label">Analysis Results</p>', unsafe_allow_html=True)
        render_results_panel(image_bytes, selected_patient)
    elif image_bytes is not None:
        st.info("Select a patient from the sidebar to run analysis.")
    else:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; padding: 48px 24px;">
                <div style="font-size:48px; margin-bottom:16px;">🔬</div>
                <div style="font-size:18px; font-weight:600; color:#E5E5E5; margin-bottom:8px;">
                    Ready to Scan
                </div>
                <div style="font-size:14px; color:#606060; line-height:1.6;">
                    Capture a wound photo using the camera<br>
                    or upload an existing image to begin analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Bottom — healing trend chart (full width)
# ---------------------------------------------------------------------------

if selected_patient is not None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Healing Trajectory</p>', unsafe_allow_html=True)
    render_trend_chart(selected_patient)
