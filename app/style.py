"""Shared visual theme for CAUSALGUARD-EDGE Streamlit pages."""
import streamlit as st

THEME_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root { color-scheme: dark; }
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
  font-family: Inter, Arial, sans-serif !important;
  font-size: 16px !important;
}
.stApp { background: linear-gradient(135deg,#070e1a 0%,#0b1426 60%,#091020 100%) !important; color:#e2e8f0 !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1b2e 0%,#091320 100%) !important; border-right:1px solid rgba(59,130,246,.25) !important; }
/* We use the custom page_link menu. Hide Streamlit's automatic page list to prevent duplicate navigation. */
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"], section[data-testid="stSidebar"] nav { display:none !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { font-size: .95rem !important; line-height:1.5 !important; letter-spacing:normal !important; text-transform:none !important; }
[data-testid="stSidebar"] a, [data-testid="stSidebar"] button { font-size: .95rem !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a { border-radius:8px !important; padding:.55rem .7rem !important; }
h1,h2,h3,h4,h5,h6 { color:#f1f5f9 !important; font-weight:650 !important; }
h1 { font-size:2rem !important; letter-spacing:-.02em !important; }
h2 { font-size:1.55rem !important; }
h3 { font-size:1.25rem !important; }
p, label, li, .stMarkdown, .stText, [data-testid="stCaptionContainer"] { font-size:1rem !important; line-height:1.55 !important; }
[data-testid="stCaptionContainer"] { color:#94a3b8 !important; }
[data-testid="stMetric"] { background:rgba(15,25,50,.78) !important; border:1px solid rgba(59,130,246,.25) !important; border-radius:12px !important; padding:18px 20px !important; }
[data-testid="stMetricLabel"] { color:#9aaac0 !important; font-size:.9rem !important; font-weight:600 !important; letter-spacing:.03em !important; }
[data-testid="stMetricValue"] { color:#60a5fa !important; font-size:2rem !important; font-weight:700 !important; }
.stButton > button, [data-testid="stDownloadButton"] button { border-radius:8px !important; padding:.6rem 1rem !important; font-size:.98rem !important; font-weight:600 !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#1d4ed8,#3b82f6) !important; color:white !important; border:0 !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid rgba(59,130,246,.25) !important; border-radius:10px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] * { font-size:.92rem !important; }
[data-testid="stExpander"] { background:rgba(13,23,45,.55) !important; border:1px solid rgba(59,130,246,.2) !important; border-radius:10px !important; }
[data-testid="stSelectbox"], [data-testid="stMultiSelect"], [data-testid="stTextInput"], [data-testid="stNumberInput"] { font-size:1rem !important; }
hr { border-top:1px solid rgba(59,130,246,.2) !important; margin:1.25rem 0 !important; }
.page-header { border-left:4px solid #3b82f6; padding-left:14px; margin:8px 0 24px; }
.page-header p { color:#9aabc2 !important; font-size:1rem !important; }
.cg-card { background:rgba(13,23,45,.7); border:1px solid rgba(59,130,246,.2); border-radius:12px; padding:20px 24px; margin-bottom:16px; }
.badge-high {color:#f87171;font-weight:700}.badge-medium{color:#fbbf24;font-weight:700}.badge-low{color:#34d399;font-weight:700}.badge-none{color:#94a3b8;font-weight:600}
</style>
"""

def inject_css() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)

def risk_badge(level: str) -> str:
    level = str(level).strip().lower()
    if level == "high": return '<span class="badge-high">High</span>'
    if level == "medium": return '<span class="badge-medium">Medium</span>'
    if level == "low": return '<span class="badge-low">Low</span>'
    return '<span class="badge-none">Unclassified</span>'

def status_badge(status: str) -> str:
    s = str(status).strip().lower()
    colours = {"completed":"#34d399", "processing":"#fbbf24", "pending":"#94a3b8", "failed":"#f87171"}
    colour = colours.get(s, "#cbd5e1")
    return f'<span style="color:{colour};font-weight:700">{str(status).title()}</span>'
