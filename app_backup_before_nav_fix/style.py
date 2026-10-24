"""
Shared CSS theme for the CAUSALGUARD-EDGE dashboard.
Call inject_css() at the top of every page after st.set_page_config().
"""

import streamlit as st


THEME_CSS = """
<style>
/* ── Google Fonts ────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base reset ──────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Global background ───────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #070e1a 0%, #0b1426 60%, #091020 100%) !important;
    color: #e2e8f0 !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2e 0%, #091320 100%) !important;
    border-right: 1px solid rgba(59, 130, 246, 0.2) !important;
}

[data-testid="stSidebar"] .stMarkdown p {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* Sidebar nav links */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    margin: 2px 8px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarNavLink"]:hover {
    background: rgba(59, 130, 246, 0.15) !important;
}

[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background: rgba(59, 130, 246, 0.25) !important;
    border-left: 3px solid #3b82f6 !important;
}

/* ── Headings ────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

h1 { font-size: 1.8rem !important; letter-spacing: -0.02em !important; }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.1rem !important; }

/* ── Metric cards ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(15, 25, 50, 0.7) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    backdrop-filter: blur(8px) !important;
    transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(59, 130, 246, 0.5) !important;
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.15) !important;
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

[data-testid="stMetricValue"] {
    color: #3b82f6 !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%) !important;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.45) !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    box-shadow: none !important;
}

/* ── Dividers ────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(59, 130, 246, 0.15) !important;
    margin: 20px 0 !important;
}

/* ── DataFrames / Tables ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

/* ── Selectbox, multiselect ──────────────────────────────────────── */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    background: rgba(15, 25, 50, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.25) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── Text input, number input ────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: rgba(15, 25, 50, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.25) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── Expander ────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(13, 23, 45, 0.6) !important;
    border: 1px solid rgba(59, 130, 246, 0.18) !important;
    border-radius: 10px !important;
}

/* ── Info / Success / Warning / Error ────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
    gap: 4px !important;
}

[data-testid="stTabs"] button[role="tab"] {
    color: #64748b !important;
    border-radius: 8px 8px 0 0 !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
    background: rgba(59, 130, 246, 0.08) !important;
}

/* ── Spinner ─────────────────────────────────────────────────────── */
[data-testid="stSpinner"] {
    color: #3b82f6 !important;
}

/* ── File uploader ───────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(59, 130, 246, 0.35) !important;
    border-radius: 12px !important;
    background: rgba(15, 25, 50, 0.4) !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(59, 130, 246, 0.7) !important;
}

/* ── Progress bar ────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #1d4ed8, #3b82f6) !important;
    border-radius: 4px !important;
}

/* ── Caption text ────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-size: 0.78rem !important;
}

/* ── Code / mono ─────────────────────────────────────────────────── */
code {
    font-family: 'JetBrains Mono', monospace !important;
    background: rgba(30, 41, 59, 0.6) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    color: #93c5fd !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(10, 18, 35, 0.8); }
::-webkit-scrollbar-thumb { background: rgba(59, 130, 246, 0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(59, 130, 246, 0.65); }

/* ── Custom card helper ──────────────────────────────────────────── */
.cg-card {
    background: rgba(13, 23, 45, 0.7);
    border: 1px solid rgba(59, 130, 246, 0.18);
    border-radius: 12px;
    padding: 20px 24px;
    backdrop-filter: blur(6px);
    margin-bottom: 16px;
    transition: border-color 0.25s ease;
}
.cg-card:hover { border-color: rgba(59, 130, 246, 0.4); }

/* Risk badge colours */
.badge-high   { color: #f87171; font-weight: 600; }
.badge-medium { color: #fbbf24; font-weight: 600; }
.badge-low    { color: #34d399; font-weight: 600; }
.badge-none   { color: #64748b; font-weight: 500; }

/* Page header rule */
.page-header {
    border-left: 4px solid #3b82f6;
    padding-left: 14px;
    margin-bottom: 24px;
}
</style>
"""


def inject_css() -> None:
    """Inject the shared dark-navy CSS theme into the current page."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def risk_badge(level: str) -> str:
    """Return an HTML badge string for a risk level."""
    level = str(level).strip().lower()
    if level == "high":
        return '<span class="badge-high">🔴 High</span>'
    if level == "medium":
        return '<span class="badge-medium">🟡 Medium</span>'
    if level == "low":
        return '<span class="badge-low">🟢 Low</span>'
    return '<span class="badge-none">— Unclassified</span>'


def status_badge(status: str) -> str:
    """Return an HTML badge string for a processing status."""
    s = str(status).strip().lower()
    colours = {
        "completed": "#34d399",
        "processing": "#fbbf24",
        "pending": "#64748b",
        "failed": "#f87171",
    }
    colour = colours.get(s, "#94a3b8")
    return f'<span style="color:{colour}; font-weight:600;">{status.title()}</span>'
