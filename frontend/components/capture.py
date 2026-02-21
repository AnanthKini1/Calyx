"""
capture.py — Wound image acquisition panel.

Provides two mutually-exclusive input modes:
  • Camera  — live webcam via st.camera_input(); user clicks shutter button
  • Upload  — drag-and-drop / file browser via st.file_uploader()

Returns raw image bytes (JPEG/PNG) or None if no image has been provided yet.
"""

from __future__ import annotations

import streamlit as st


def render_capture_panel() -> bytes | None:
    """
    Render the camera / upload panel and return image bytes when ready.

    The camera feed is shown by default.  The user switches to file-upload
    via a tab.  Whichever tab produced the last image wins; state is kept
    across reruns via st.session_state.
    """
    # Clear button resets capture state
    if "captured_image" not in st.session_state:
        st.session_state["captured_image"] = None
    if "capture_source" not in st.session_state:
        st.session_state["capture_source"] = None

    st.markdown(
        """
        <div class="glass-card-accent" style="padding: 20px 24px 12px;">
            <div style="font-size:13px; color:#A78BFA; font-weight:600;
                        letter-spacing:0.08em; text-transform:uppercase;
                        margin-bottom:4px;">
                Image Acquisition
            </div>
            <div style="font-size:12px; color:#505050; line-height:1.5;">
                Use the live camera or upload a saved photo.
                Place a US quarter next to the wound for auto-calibration.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    camera_tab, upload_tab = st.tabs(["📷  Camera", "📁  File Upload"])

    # ── Camera tab ──────────────────────────────────────────────────────────
    with camera_tab:
        st.markdown(
            '<div style="font-size:12px; color:#505050; margin-bottom:8px;">'
            "Position the wound in frame and press the shutter button."
            "</div>",
            unsafe_allow_html=True,
        )

        camera_image = st.camera_input(
            label="Wound camera",
            label_visibility="collapsed",
            key="camera_widget",
        )

        if camera_image is not None:
            st.session_state["captured_image"] = camera_image.getvalue()
            st.session_state["capture_source"] = "camera"

        if st.session_state["capture_source"] == "camera":
            _render_capture_controls()

    # ── Upload tab ───────────────────────────────────────────────────────────
    with upload_tab:
        st.markdown(
            '<div style="font-size:12px; color:#505050; margin-bottom:8px;">'
            "Accepted formats: JPG, JPEG, PNG, WEBP."
            "</div>",
            unsafe_allow_html=True,
        )

        uploaded = st.file_uploader(
            label="Upload wound image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key="upload_widget",
        )

        if uploaded is not None:
            st.session_state["captured_image"] = uploaded.getvalue()
            st.session_state["capture_source"] = "upload"

        if st.session_state["capture_source"] == "upload":
            _render_capture_controls()

    # ── Calibration note ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex; align-items:flex-start; gap:10px;
                    background:rgba(139,92,246,0.06);
                    border:1px solid rgba(139,92,246,0.20);
                    border-radius:10px; padding:12px 14px; margin-top:4px;">
            <span style="font-size:18px; flex-shrink:0;">🪙</span>
            <div style="font-size:12px; color:#808080; line-height:1.5;">
                <b style="color:#A78BFA;">Auto-calibration:</b> Place a US quarter
                (24.26 mm) beside the wound. The CV engine will detect the coin
                edge and compute area in cm².
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return st.session_state["captured_image"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_capture_controls() -> None:
    """Show a clear/retake button under the active capture source."""
    col_a, col_b = st.columns([3, 1])
    with col_b:
        if st.button("Clear ✕", key="clear_capture_btn"):
            st.session_state["captured_image"] = None
            st.session_state["capture_source"] = None
            st.rerun()
    with col_a:
        source = st.session_state.get("capture_source", "")
        label = "📷 Camera image ready" if source == "camera" else "📁 File loaded"
        st.markdown(
            f'<div style="padding:8px 0; font-size:13px; color:#5BD97A;">'
            f"✓ {label} — analysis will run automatically."
            f"</div>",
            unsafe_allow_html=True,
        )
