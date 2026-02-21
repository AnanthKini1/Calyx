"""
results_panel.py — Analysis results display.

Shows:
  • Annotated wound image (CV overlay)
  • RYB tissue composition with animated bars
  • Area measurement + coin calibration status
  • Knowledge Graph clinical reasoning block
  • Alert list with priority-coloured banners
  • Active risk factors from the graph traversal
"""

from __future__ import annotations

import sys
import os

_COMP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_COMP, "..", ".."))  # project root
sys.path.insert(0, os.path.join(_COMP, ".."))        # frontend root

import cv2
import streamlit as st

from styles.theme import PRIORITY_COLORS, PRIORITY_ICONS, COLORS
from utils.analysis_bridge import run_analysis


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_results_panel(image_bytes: bytes, patient: dict) -> dict | None:
    """
    Run the full pipeline and render results for the given image + patient.
    Returns the result dict so callers can persist the scan, or None on error.
    """
    cache_key = f"analysis_{patient['patient_id']}_{hash(image_bytes)}"

    if cache_key not in st.session_state:
        with st.spinner("Analysing wound…"):
            try:
                result = run_analysis(image_bytes, patient)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return None
        st.session_state[cache_key] = result
    else:
        result = st.session_state[cache_key]

    cv_out = result["cv"]
    kg_out = result["kg"]

    # ── Annotated image ──────────────────────────────────────────────────────
    annotated_bgr = cv_out["annotated_image"]
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    st.image(annotated_rgb, use_container_width=True)

    # ── Coin calibration status ──────────────────────────────────────────────
    if cv_out.get("coin_found"):
        scale = cv_out.get("scale_cm_per_px", 0)
        st.markdown(
            f'<div style="font-size:12px; color:#5BD97A; margin-top:4px; margin-bottom:12px;">'
            f"🪙 Coin detected — scale: {scale:.4f} cm/px"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:12px; color:#FF9500; margin-top:4px; margin-bottom:12px;">'
            "⚠ No coin detected — using default scale (place a quarter for precision)"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Tissue composition ───────────────────────────────────────────────────
    _render_tissue_section(cv_out["ryb_ratios"], cv_out["area_cm2"], result["area_delta"])

    # ── Knowledge graph reasoning ────────────────────────────────────────────
    _render_reasoning_section(kg_out)

    return result


# ---------------------------------------------------------------------------
# Internal section renderers
# ---------------------------------------------------------------------------

def _render_tissue_section(ryb: dict, area: float, delta: float) -> None:
    red    = ryb.get("red", 0)
    yellow = ryb.get("yellow", 0)
    black  = ryb.get("black", 0)

    delta_str   = f"{delta:+.2f} cm²"
    delta_color = COLORS["ok"] if delta < -0.1 else (COLORS["critical"] if delta > 0.1 else COLORS["medium"])

    bar_html = (
        f'<div style="display:flex; height:12px; border-radius:8px; overflow:hidden;'
        f'margin-bottom:16px; gap:2px;">'
        f'<div style="flex:{red}; background:linear-gradient(90deg,#C0392B,#E74C3C);'
        f'border-radius:8px 0 0 8px;" title="Granulation {red:.1f}%"></div>'
        f'<div style="flex:{yellow}; background:linear-gradient(90deg,#D4AA3A,#F1C40F);"'
        f'title="Slough {yellow:.1f}%"></div>'
        f'<div style="flex:{black}; background:linear-gradient(90deg,#2C2C2C,#555);'
        f'border-radius:0 8px 8px 0;" title="Necrosis {black:.1f}%"></div>'
        f"</div>"
    )

    def stat_row(label: str, pct: float, color: str) -> str:
        return (
            f'<div style="display:flex; justify-content:space-between;'
            f'align-items:center; margin-bottom:6px;">'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<div style="width:8px; height:8px; border-radius:50%; background:{color};"></div>'
            f'<div style="font-size:13px; color:#A0A0A0;">{label}</div>'
            f"</div>"
            f'<div style="font-size:14px; font-weight:600; color:#E5E5E5;">{pct:.1f}%</div>'
            f"</div>"
        )

    st.markdown(
        f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:14px;">
                <div>
                    <div style="font-size:24px; font-weight:700; color:#E5E5E5;">
                        {area:.2f}
                        <span style="font-size:14px; font-weight:400; color:#505050;">cm²</span>
                    </div>
                    <div style="font-size:11px; color:#505050;">Wound area</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:20px; font-weight:700; color:{delta_color};">
                        {delta_str}
                    </div>
                    <div style="font-size:11px; color:{delta_color};">7-day trend</div>
                </div>
            </div>
            {bar_html}
            {stat_row("Granulation (Red)", red, "#E74C3C")}
            {stat_row("Slough (Yellow)", yellow, "#F1C40F")}
            {stat_row("Necrosis (Black)", black, "#555555")}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_reasoning_section(kg: dict) -> None:
    priority = kg.get("priority", "OK")
    alerts   = kg.get("alerts", [])
    reasoning   = kg.get("reasoning", "")
    risk_factors = kg.get("active_risk_factors", [])
    action       = kg.get("recommended_action", "")

    p_color = PRIORITY_COLORS.get(priority, COLORS["grey_mid"])
    p_icon  = PRIORITY_ICONS.get(priority, "")
    p_cls   = priority.lower()

    # Priority header
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
            <div style="font-size:28px;">{p_icon}</div>
            <div>
                <div style="font-size:11px; font-weight:600; letter-spacing:0.10em;
                            text-transform:uppercase; color:{p_color}; margin-bottom:2px;">
                    {priority} PRIORITY
                </div>
                <div style="font-size:13px; color:#808080;">Clinical Assessment</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Alert banners
    for alert in alerts:
        level = _alert_level(alert)
        st.markdown(
            f'<div class="alert-banner alert-{level}">{alert}</div>',
            unsafe_allow_html=True,
        )

    # Recommended action
    if action:
        st.markdown(
            f"""
            <div style="background:rgba(139,92,246,0.08);
                        border:1px solid rgba(139,92,246,0.25);
                        border-radius:10px; padding:12px 14px; margin:12px 0;">
                <div style="font-size:11px; color:#8B5CF6; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.08em;
                            margin-bottom:4px;">Recommended Action</div>
                <div style="font-size:13px; color:#C0A8F8; line-height:1.5;">
                    {action}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Clinical reasoning paragraph
    if reasoning:
        st.markdown(
            f"""
            <div class="glass-card" style="margin-top:0;">
                <div style="font-size:11px; color:#505050; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.08em;
                            margin-bottom:8px;">Clinical Reasoning</div>
                <div style="font-size:13px; color:#A0A0A0; line-height:1.7;">
                    {reasoning}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Active risk factors from KG traversal
    if risk_factors:
        tags_html = "".join(
            f'<span style="display:inline-block; background:rgba(255,59,48,0.10);'
            f'border:1px solid rgba(255,59,48,0.25); border-radius:6px;'
            f'padding:3px 9px; font-size:11px; color:#FF6B63;'
            f'margin:2px 2px 2px 0;">'
            f"{rf.replace('_', ' ')}</span>"
            for rf in risk_factors
        )
        st.markdown(
            f"""
            <div style="margin-top:4px;">
                <div style="font-size:11px; color:#505050; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.08em;
                            margin-bottom:6px;">Knowledge Graph — Active Risks</div>
                <div>{tags_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _alert_level(alert_text: str) -> str:
    """Map alert text to CSS class suffix."""
    t = alert_text.lower()
    if "critical" in t:
        return "critical"
    if "high" in t:
        return "high"
    if "medium" in t or "nutritional" in t or "mobility" in t:
        return "medium"
    if "low" in t or "delayed" in t:
        return "low"
    return "ok"
