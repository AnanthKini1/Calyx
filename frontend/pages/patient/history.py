"""
pages/patient/history.py — Patient wound scan history.
"""

from __future__ import annotations

import sys
import os

_PAGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PAGE, "..", "..", ".."))
sys.path.insert(0, os.path.join(_PAGE, "..", ".."))

import streamlit as st
from components.trend_chart import render_trend_chart
from utils.patient_store import get_patient


def render_history_page(patient_id: str) -> None:
    patient = get_patient(patient_id)
    if patient is None:
        st.error("Patient not found.")
        return

    history = patient.get("wound_history", [])

    st.markdown(
        f"""
        <div style="margin-bottom:32px;">
            <div style="font-size:26px; font-weight:700; color:#E5E5E5;
                        letter-spacing:-0.02em; margin-bottom:6px;">Healing History</div>
            <div style="font-size:14px; color:#505050;">
                {patient['name']} · {len(history)} scan{"s" if len(history) != 1 else ""} recorded
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not history:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; min-height:300px; text-align:center;
                        border:1px dashed rgba(139,92,246,0.20); border-radius:16px;
                        padding:48px 32px;">
                <div style="font-size:48px; opacity:0.4; margin-bottom:16px;">📈</div>
                <div style="font-size:16px; font-weight:600; color:#505050; margin-bottom:8px;">
                    No Scans Yet</div>
                <div style="font-size:13px; color:#404040;">
                    Head to the Scan page to capture your first wound image.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    _section("Trajectory")
    render_trend_chart(patient)
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    _section("Scan Log")
    _render_scan_table(history)


def _section(label: str) -> None:
    st.markdown(
        f'<div style="font-size:11px; font-weight:600; letter-spacing:0.12em;'
        f'text-transform:uppercase; color:#8B5CF6; margin-bottom:14px;">{label}</div>',
        unsafe_allow_html=True,
    )


def _render_scan_table(history: list[dict]) -> None:
    rows = ""
    for i, scan in enumerate(reversed(history)):
        ryb = scan.get("ryb_ratios", {})
        red, yellow, black = ryb.get("red", 0), ryb.get("yellow", 0), ryb.get("black", 0)
        prev_idx = len(history) - 2 - i
        trend = ""
        if prev_idx >= 0:
            diff = scan["area_cm2"] - history[prev_idx]["area_cm2"]
            if diff < -0.05:
                trend = f'<span style="color:#34C759;">↓ {abs(diff):.2f}</span>'
            elif diff > 0.05:
                trend = f'<span style="color:#FF3B30;">↑ {diff:.2f}</span>'
            else:
                trend = '<span style="color:#FFD60A;">→</span>'

        rows += f"""
        <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="padding:12px 14px; color:#A0A0A0; font-size:13px;">{scan['date']}</td>
            <td style="padding:12px 14px; color:#E5E5E5; font-size:14px;
                       font-weight:600;">{scan['area_cm2']:.2f} cm²</td>
            <td style="padding:12px 14px; font-size:12px;">{trend}</td>
            <td style="padding:12px 8px;">
                <div style="display:flex; gap:4px; align-items:center;">
                    <div style="width:{max(red,2):.0f}px; max-width:56px; height:8px;
                                background:#E74C3C; border-radius:4px;"></div>
                    <div style="width:{max(yellow,2):.0f}px; max-width:56px; height:8px;
                                background:#F1C40F; border-radius:4px;"></div>
                    <div style="width:{max(black,2):.0f}px; max-width:56px; height:8px;
                                background:#555; border-radius:4px;"></div>
                </div>
            </td>
            <td style="padding:12px 14px; font-size:12px; color:#606060;">
                <span style="color:#E74C3C;">{red:.0f}%</span> ·
                <span style="color:#F1C40F;">{yellow:.0f}%</span> ·
                <span style="color:#888;">{black:.0f}%</span>
            </td>
        </tr>"""

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px; overflow:hidden;">
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
                    {''.join(f'<th style="padding:12px 14px; text-align:left; color:#404040; font-size:11px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase;">{h}</th>' for h in ["Date","Area","Trend","Tissue","RYB %"])}
                </tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
