"""
trend_chart.py — Healing trajectory visualisation.

Renders a Plotly figure with:
  • Primary line: wound area over time (cm²)
  • Stacked area bands: RYB tissue composition over time
  • Styled to match the dark purple ChroniScan theme
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


_TRANSPARENT = "rgba(0,0,0,0)"
_BG          = "#0d0d0d"
_GRID        = "rgba(255,255,255,0.05)"
_TEXT        = "#808080"
_PURPLE      = "#8B5CF6"
_PURPLE_FILL = "rgba(139,92,246,0.12)"
_RED_LINE    = "#E74C3C"
_RED_FILL    = "rgba(231,76,60,0.15)"
_YELLOW_LINE = "#F1C40F"
_YELLOW_FILL = "rgba(241,196,15,0.15)"
_BLACK_LINE  = "#888888"
_BLACK_FILL  = "rgba(80,80,80,0.15)"


def render_trend_chart(patient: dict) -> None:
    """Render the healing trend chart for the given patient."""
    history = patient.get("wound_history", [])

    if len(history) < 2:
        st.markdown(
            '<div class="glass-card" style="text-align:center; color:#505050;'
            'padding:32px;">Not enough scan history to plot a trend.</div>',
            unsafe_allow_html=True,
        )
        return

    if not _PLOTLY:
        _render_fallback_table(history)
        return

    dates  = [h["date"] for h in history]
    areas  = [h["area_cm2"] for h in history]
    reds   = [h["ryb_ratios"].get("red", 0)    for h in history]
    yellows= [h["ryb_ratios"].get("yellow", 0) for h in history]
    blacks = [h["ryb_ratios"].get("black", 0)  for h in history]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.45],
        vertical_spacing=0.06,
        subplot_titles=["Wound Area (cm²)", "Tissue Composition (%)"],
    )

    # ── Row 1: Area line ──────────────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates, y=areas,
            mode="lines+markers",
            name="Area cm²",
            line=dict(color=_PURPLE, width=2.5),
            marker=dict(size=7, color=_PURPLE,
                        line=dict(color="#FFFFFF", width=1.5)),
            fill="tozeroy",
            fillcolor=_PURPLE_FILL,
            hovertemplate="%{x}<br>Area: %{y:.2f} cm²<extra></extra>",
        ),
        row=1, col=1,
    )

    # ── Row 2: Tissue stacked area ────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=dates, y=blacks,
            name="Necrosis (Black)",
            mode="lines",
            stackgroup="tissue",
            line=dict(color=_BLACK_LINE, width=1),
            fillcolor=_BLACK_FILL,
            hovertemplate="%{x}<br>Necrosis: %{y:.1f}%<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=dates, y=yellows,
            name="Slough (Yellow)",
            mode="lines",
            stackgroup="tissue",
            line=dict(color=_YELLOW_LINE, width=1),
            fillcolor=_YELLOW_FILL,
            hovertemplate="%{x}<br>Slough: %{y:.1f}%<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=dates, y=reds,
            name="Granulation (Red)",
            mode="lines",
            stackgroup="tissue",
            line=dict(color=_RED_LINE, width=1),
            fillcolor=_RED_FILL,
            hovertemplate="%{x}<br>Granulation: %{y:.1f}%<extra></extra>",
        ),
        row=2, col=1,
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    _apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _apply_theme(fig: "go.Figure") -> None:
    axis_common = dict(
        gridcolor=_GRID,
        zerolinecolor=_GRID,
        tickfont=dict(color=_TEXT, size=11),
        title_font=dict(color=_TEXT, size=11),
        showline=False,
    )
    fig.update_layout(
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        font=dict(family="Inter, -apple-system, sans-serif", color=_TEXT),
        margin=dict(l=8, r=8, t=32, b=8),
        height=390,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=_TEXT, size=11),
            orientation="h",
            x=0, y=-0.05,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1a1a",
            bordercolor=_PURPLE,
            font=dict(color="#E5E5E5", size=12),
        ),
    )
    fig.update_annotations(font=dict(color=_TEXT, size=11))
    fig.update_xaxes(**axis_common)
    fig.update_yaxes(**axis_common)


def _render_fallback_table(history: list[dict]) -> None:
    """Plain table fallback when Plotly is not installed."""
    st.markdown(
        '<div style="font-size:12px; color:#FF9500; margin-bottom:8px;">'
        "Install plotly for interactive charts: pip install plotly"
        "</div>",
        unsafe_allow_html=True,
    )
    rows = ""
    for h in history:
        ryb = h["ryb_ratios"]
        rows += (
            f"<tr>"
            f"<td style='padding:6px 10px; color:#A0A0A0;'>{h['date']}</td>"
            f"<td style='padding:6px 10px; color:#E5E5E5;'>{h['area_cm2']:.2f}</td>"
            f"<td style='padding:6px 10px; color:#E74C3C;'>{ryb.get('red',0):.1f}%</td>"
            f"<td style='padding:6px 10px; color:#F1C40F;'>{ryb.get('yellow',0):.1f}%</td>"
            f"<td style='padding:6px 10px; color:#888;'>{ryb.get('black',0):.1f}%</td>"
            f"</tr>"
        )
    st.markdown(
        f"""
        <div class="glass-card">
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
            <thead>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
                    <th style="padding:6px 10px; text-align:left; color:#505050;">Date</th>
                    <th style="padding:6px 10px; text-align:left; color:#505050;">Area cm²</th>
                    <th style="padding:6px 10px; text-align:left; color:#505050;">Red</th>
                    <th style="padding:6px 10px; text-align:left; color:#505050;">Yellow</th>
                    <th style="padding:6px 10px; text-align:left; color:#505050;">Black</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
