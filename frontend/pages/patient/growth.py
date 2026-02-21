"""
pages/patient/growth.py — Recovery growth visualization for patients.

Shows:
  • % area reduction from baseline
  • Granulation tissue growth trend
  • Linear-regression projection of wound closure date
  • Motivational progress ring
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from utils.patient_store import get_patient

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


def render_growth_page(patient_id: str) -> None:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found.")
        return

    history = patient.get("wound_history", [])

    st.markdown(
        f"""
        <div style="margin-bottom:32px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:6px;">Recovery Growth</div>
            <div style="font-size:14px; color:#505050;">
                Your healing progress at a glance, {patient['name'].split()[0]}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if len(history) < 2:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; min-height:300px; text-align:center;
                        border:1px dashed rgba(139,92,246,0.20); border-radius:16px; padding:48px;">
                <div style="font-size:48px; opacity:0.4; margin-bottom:16px;">🌱</div>
                <div style="font-size:16px; font-weight:600; color:#505050; margin-bottom:8px;">
                    Not Enough Data Yet</div>
                <div style="font-size:13px; color:#404040;">
                    Complete at least 2 scans to see your recovery growth.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    baseline = history[0]
    latest   = history[-1]

    baseline_area  = baseline["area_cm2"]
    current_area   = latest["area_cm2"]
    area_pct       = ((baseline_area - current_area) / baseline_area * 100) if baseline_area else 0
    area_pct       = max(0.0, area_pct)

    baseline_red   = baseline["ryb_ratios"].get("red", 0)
    current_red    = latest["ryb_ratios"].get("red", 0)
    granulation_delta = current_red - baseline_red

    # ── Summary KPI row ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        _kpi_card(
            "Area Reduced",
            f"{area_pct:.1f}%",
            f"From {baseline_area:.1f} → {current_area:.1f} cm²",
            "#34C759" if area_pct >= 0 else "#FF3B30",
        )

    with col2:
        sign = "+" if granulation_delta >= 0 else ""
        _kpi_card(
            "Granulation Growth",
            f"{sign}{granulation_delta:.1f}%",
            "Red (healthy) tissue change",
            "#34C759" if granulation_delta >= 0 else "#FF9500",
        )

    with col3:
        closure_days = _estimate_closure(history)
        if closure_days is not None and closure_days > 0:
            closure_text = f"~{closure_days}d"
            closure_sub  = "Projected days to closure"
            closure_color = "#A78BFA"
        elif closure_days == 0:
            closure_text = "Closed"
            closure_sub  = "Wound appears healed"
            closure_color = "#34C759"
        else:
            closure_text = "N/A"
            closure_sub  = "Wound not shrinking"
            closure_color = "#FF9500"
        _kpi_card("Est. Closure", closure_text, closure_sub, closure_color)

    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

    if not _PLOTLY:
        st.info("Install plotly for interactive charts.")
        return

    # ── Progress gauge ────────────────────────────────────────────────────────
    _section("Healing Progress")
    col_g, col_r = st.columns([1, 1])

    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(area_pct, 100),
            number={"suffix": "%", "font": {"color": "#E5E5E5", "size": 36}},
            title={"text": "Area Reduction", "font": {"color": "#808080", "size": 13}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#404040",
                         "tickfont": {"color": "#505050"}},
                "bar":  {"color": "#8B5CF6"},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0,  40],  "color": "rgba(255,59,48,0.10)"},
                    {"range": [40, 70],  "color": "rgba(255,149,0,0.10)"},
                    {"range": [70, 100], "color": "rgba(52,199,89,0.10)"},
                ],
                "threshold": {
                    "line": {"color": "#34C759", "width": 2},
                    "thickness": 0.75, "value": 80,
                },
            },
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#808080"},
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
            height=240,
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    with col_r:
        # Granulation growth bar
        fig_bar = go.Figure(go.Bar(
            x=["Baseline", "Current"],
            y=[baseline_red, current_red],
            marker_color=["rgba(231,76,60,0.5)", "#E74C3C"],
            text=[f"{baseline_red:.1f}%", f"{current_red:.1f}%"],
            textposition="outside",
            textfont={"color": "#E5E5E5"},
        ))
        fig_bar.update_layout(
            title={"text": "Granulation Tissue (Red %)",
                   "font": {"color": "#808080", "size": 13}},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#808080"},
            yaxis={"gridcolor": "rgba(255,255,255,0.05)", "range": [0, 100],
                   "tickfont": {"color": "#505050"}},
            xaxis={"tickfont": {"color": "#505050"}},
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
            height=240,
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # ── Scan-by-scan area timeline ─────────────────────────────────────────────
    if len(history) >= 3:
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        _section("Area Over Time")
        dates = [h["date"] for h in history]
        areas = [h["area_cm2"] for h in history]

        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=dates, y=areas, mode="lines+markers",
            line={"color": "#8B5CF6", "width": 2},
            marker={"size": 7, "color": "#8B5CF6",
                    "line": {"color": "#fff", "width": 1.5}},
            fill="tozeroy", fillcolor="rgba(139,92,246,0.10)",
            name="Area cm²",
        ))
        # Add projection if available
        proj = _get_projection(history)
        if proj:
            fig_area.add_trace(go.Scatter(
                x=proj["dates"], y=proj["areas"],
                mode="lines",
                line={"color": "#34C759", "width": 1.5, "dash": "dot"},
                name="Projected",
            ))
        fig_area.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#808080"},
            yaxis={"gridcolor": "rgba(255,255,255,0.05)",
                   "tickfont": {"color": "#505050"}},
            xaxis={"tickfont": {"color": "#505050"}},
            legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#808080"}},
            margin={"l": 8, "r": 8, "t": 16, "b": 8},
            height=220,
            hovermode="x unified",
        )
        st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kpi_card(title: str, value: str, subtitle: str, color: str) -> None:
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; padding:20px; text-align:center; height:120px;
                    display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:11px; color:#505050; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">
                {title}</div>
            <div style="font-size:28px; font-weight:700; color:{color}; line-height:1;
                        margin-bottom:6px;">{value}</div>
            <div style="font-size:11px; color:#404040;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(label: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        f'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">{label}</div>',
        unsafe_allow_html=True,
    )


def _estimate_closure(history: list[dict]) -> int | None:
    """Linear regression to estimate days until area reaches 0. Returns None if not shrinking."""
    if len(history) < 2:
        return None
    areas = [h["area_cm2"] for h in history]
    # Simple slope: average daily reduction
    from datetime import date
    try:
        dates = [date.fromisoformat(h["date"]) for h in history]
        days = [(d - dates[0]).days for d in dates]
        if days[-1] == 0:
            return None
        slope = (areas[-1] - areas[0]) / days[-1]  # cm² / day (negative = healing)
        if slope >= 0:
            return None
        return max(0, int(areas[-1] / abs(slope)))
    except Exception:
        return None


def _get_projection(history: list[dict]) -> dict | None:
    """Generate projection points for the area chart."""
    from datetime import date, timedelta
    try:
        dates = [date.fromisoformat(h["date"]) for h in history]
        areas = [h["area_cm2"] for h in history]
        days_elapsed = (dates[-1] - dates[0]).days
        if days_elapsed == 0:
            return None
        slope = (areas[-1] - areas[0]) / days_elapsed
        if slope >= 0:
            return None
        proj_dates, proj_areas = [], []
        current_area = areas[-1]
        current_date = dates[-1]
        step = max(1, days_elapsed // len(history))
        for _ in range(10):
            current_date += timedelta(days=step)
            current_area += slope * step
            if current_area <= 0:
                proj_dates.append(current_date.isoformat())
                proj_areas.append(0.0)
                break
            proj_dates.append(current_date.isoformat())
            proj_areas.append(round(current_area, 2))
        return {"dates": proj_dates, "areas": proj_areas} if proj_dates else None
    except Exception:
        return None
