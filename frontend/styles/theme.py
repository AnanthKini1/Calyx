"""
theme.py — ChroniScan design system.

Apple-inspired dark UI with purple accent and glassmorphism cards.
Inject into Streamlit via inject_css().
"""

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

COLORS = {
    "bg_primary":    "#080808",
    "bg_secondary":  "#0f0f0f",
    "bg_glass":      "rgba(255, 255, 255, 0.04)",
    "bg_glass_hover":"rgba(255, 255, 255, 0.07)",
    "purple_primary":"#8B5CF6",
    "purple_light":  "#A78BFA",
    "purple_dim":    "rgba(139, 92, 246, 0.15)",
    "purple_border": "rgba(139, 92, 246, 0.35)",
    "white":         "#FFFFFF",
    "grey_high":     "#E5E5E5",
    "grey_mid":      "#A0A0A0",
    "grey_low":      "#505050",
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    # Clinical alert palette
    "critical":      "#FF3B30",
    "high":          "#FF9500",
    "medium":        "#FFD60A",
    "low":           "#34C759",
    "ok":            "#30D158",
}

PRIORITY_COLORS = {
    "CRITICAL": COLORS["critical"],
    "HIGH":     COLORS["high"],
    "MEDIUM":   COLORS["medium"],
    "LOW":      COLORS["low"],
    "OK":       COLORS["ok"],
}

PRIORITY_ICONS = {
    "CRITICAL": "⬛",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
    "OK":       "✅",
}

CSS = """
<style>
/* ── Reset & Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stApp"] {
    background-color: #080808 !important;
    color: #E5E5E5 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0a0a0a !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}

/* ── Main container padding ── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* ── Glass card ── */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: border-color 0.2s ease;
    margin-bottom: 16px;
}
.glass-card:hover {
    border-color: rgba(139, 92, 246, 0.3);
}

/* ── Purple glow card ── */
.glass-card-accent {
    background: rgba(139, 92, 246, 0.06);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    margin-bottom: 16px;
}

/* ── Section headings ── */
.section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8B5CF6;
    margin-bottom: 12px;
}

/* ── Metric chip ── */
.metric-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
    color: #E5E5E5;
}

/* ── Alert banner ── */
.alert-banner {
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    border-left: 4px solid;
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
}
.alert-critical { background: rgba(255,59,48,0.12);  border-color: #FF3B30; color: #FF6B63; }
.alert-high     { background: rgba(255,149,0,0.12);  border-color: #FF9500; color: #FFAD33; }
.alert-medium   { background: rgba(255,214,10,0.12); border-color: #FFD60A; color: #FFE066; }
.alert-low      { background: rgba(52,199,89,0.12);  border-color: #34C759; color: #5BD97A; }
.alert-ok       { background: rgba(48,209,88,0.12);  border-color: #30D158; color: #52D97A; }

/* ── Priority badge ── */
.priority-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── Tissue bar ── */
.tissue-bar-wrap {
    border-radius: 8px;
    overflow: hidden;
    height: 10px;
    background: rgba(255,255,255,0.06);
    display: flex;
    margin-bottom: 8px;
}

/* ── RYB stat row ── */
.ryb-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.ryb-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.ryb-label {
    font-size: 13px;
    color: #A0A0A0;
    flex: 1;
}
.ryb-value {
    font-size: 14px;
    font-weight: 600;
    color: #E5E5E5;
}

/* ── Logo / hero ── */
.hero-title {
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 60%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin: 0;
}
.hero-sub {
    font-size: 15px;
    color: #606060;
    font-weight: 400;
    margin-top: 6px;
    letter-spacing: -0.01em;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.4), transparent);
    margin: 24px 0;
}

/* ── Spacing ── */
.block-container { padding-top: 2.5rem !important; }
[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* ── Streamlit overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
    width: 100%;
    letter-spacing: 0.01em;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* Nav buttons — override purple for sidebar nav */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #707070 !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: rgba(139,92,246,0.30) !important;
    color: #A78BFA !important;
    background: rgba(139,92,246,0.08) !important;
}

/* Sign out button in sidebar */
[data-testid="stSidebar"] [data-testid="stButton"]:last-child > button {
    background: rgba(255,59,48,0.08) !important;
    border: 1px solid rgba(255,59,48,0.20) !important;
    color: #FF6B63 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-child > button:hover {
    background: rgba(255,59,48,0.14) !important;
    border-color: rgba(255,59,48,0.35) !important;
}

.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 10px !important;
    color: #E5E5E5 !important;
}

/* Camera widget */
[data-testid="stCameraInput"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(139,92,246,0.25) !important;
}
[data-testid="stCameraInput"] > div {
    background: #0a0a0a !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1px dashed rgba(139,92,246,0.35) !important;
    border-radius: 12px !important;
    background: rgba(139,92,246,0.04) !important;
    padding: 8px !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #606060 !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #A78BFA !important;
    border-bottom: 2px solid #8B5CF6 !important;
}

/* Plotly chart container */
[data-testid="stPlotlyChart"] {
    border-radius: 12px;
    overflow: hidden;
}

/* st.image */
[data-testid="stImage"] > img {
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Info / success / error boxes */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
}
</style>
"""


def inject_css() -> None:
    """Inject the ChroniScan CSS theme into the active Streamlit page."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
