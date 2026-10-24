"""
CAUSALGUARD-EDGE  —  Page 1: System Dashboard
Overview of registered videos, analysis results, risk distribution,
and recent events. All metrics are derived from saved data only.
"""

from pathlib import Path
import sys
import sqlite3

import pandas as pd
import streamlit as st

# ── Ensure project root is always on sys.path ────────────────────────
# This handles both `streamlit run app/dashboard.py` (root on path)
# and cases where only the app/ directory is the working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ── Local imports ────────────────────────────────────────────────────
from style import inject_css, risk_badge, status_badge  # noqa: E402
from storage.video_manager import list_videos  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "causalguard.db"
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_VIDEOS = PROJECT_ROOT / "data" / "videos"

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAUSALGUARD-EDGE | Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar branding ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 12px 0 20px 0;">
          <div style="font-size:2rem;">🛡️</div>
          <div style="font-size:1.05rem; font-weight:700; color:#f1f5f9;
                      letter-spacing:0.04em;">CAUSALGUARD</div>
          <div style="font-size:0.7rem; color:#3b82f6; letter-spacing:0.1em;
                      text-transform:uppercase;">EDGE</div>
        </div>
        <hr style="border-color:rgba(59,130,246,0.2); margin:0 0 12px 0;">
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Navigation**")
    st.page_link("app/dashboard.py",         label="📊 Dashboard",               icon=None)
    st.page_link("app/pages/2_Video_Analysis.py",         label="🎬 Video Analysis",          icon=None)
    st.page_link("app/pages/3_Causal_Analysis.py",        label="🔗 Causal Analysis",         icon=None)
    st.page_link("app/pages/4_Counterfactual_Analysis.py",label="🔀 Counterfactual Analysis", icon=None)
    st.page_link("app/pages/5_Event_History.py",          label="📋 Event History",           icon=None)
    st.page_link("app/pages/6_Alert_Settings.py",         label="🔔 Alert Settings",          icon=None)
    st.divider()
    st.caption("B.Tech Final Year Project\nAI & ML — 2026")

# ── Page header ──────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
      <h1 style="margin:0;">📊 System Dashboard</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Pedestrian–Vehicle Safety Analysis · Real-time overview
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — Load data from saved results
# ════════════════════════════════════════════════════════════════════

videos = list_videos()
total_videos = len(videos)
completed = sum(v["status"] == "completed" for v in videos)
pending   = sum(v["status"] == "pending"   for v in videos)
failed    = sum(v["status"] == "failed"    for v in videos)

# Load the most recent events CSV (if any exist in results/)
event_files = sorted(
    list(RESULTS_DIR.glob("*_events.csv")) +
    list(DATA_VIDEOS.glob("*_events.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

events_df = pd.DataFrame()
grouped_df = pd.DataFrame()
risk_df = pd.DataFrame()

if event_files:
    try:
        events_df = pd.read_csv(event_files[0])
        for col in ["start_time_s", "end_time_s", "duration_s",
                    "peak_risk_score", "observations", "candidate_observations"]:
            if col in events_df.columns:
                events_df[col] = pd.to_numeric(events_df[col], errors="coerce")
        if "persistent_candidate" in events_df.columns:
            events_df["persistent_candidate"] = (
                events_df["persistent_candidate"]
                .astype(str).str.strip().str.lower()
                .isin(["true", "1", "yes"])
            )
    except Exception:
        events_df = pd.DataFrame()

# Load grouped rows for risk distribution
grouped_files = sorted(
    list(RESULTS_DIR.glob("*_grouped_rows.csv")) +
    list(DATA_VIDEOS.glob("*_grouped_rows.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if grouped_files:
    try:
        grouped_df = pd.read_csv(grouped_files[0])
    except Exception:
        grouped_df = pd.DataFrame()

# Load risk CSV for valid score counts
risk_files = sorted(
    list(RESULTS_DIR.glob("*_risk.csv")) +
    list(DATA_VIDEOS.glob("*_risk.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if risk_files:
    try:
        risk_df = pd.read_csv(risk_files[0])
        risk_df["risk_score"] = pd.to_numeric(risk_df.get("risk_score", pd.Series()), errors="coerce")
    except Exception:
        risk_df = pd.DataFrame()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — Top-level KPI metrics
# ════════════════════════════════════════════════════════════════════

valid_risk_count = int(risk_df["risk_score"].notna().sum()) if not risk_df.empty and "risk_score" in risk_df.columns else 0
total_events     = len(events_df)
persistent_ev    = int(events_df["persistent_candidate"].sum()) if not events_df.empty and "persistent_candidate" in events_df.columns else 0
candidate_ev     = int((events_df.get("candidate_observations", pd.Series(0)).fillna(0) > 0).sum()) if not events_df.empty else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Registered Videos",     total_videos)
c2.metric("Completed Analyses",    completed)
c3.metric("Pending / Failed",      f"{pending} / {failed}")
c4.metric("Valid Risk Estimates",  valid_risk_count)
c5.metric("Candidate Events",      candidate_ev)
c6.metric("Persistent Candidates", persistent_ev)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 3 — Two-column layout: chart + recent events
# ════════════════════════════════════════════════════════════════════

left_col, right_col = st.columns([1, 1], gap="large")

# ── Risk-level distribution ──────────────────────────────────────────
with left_col:
    st.subheader("Risk Level Distribution")

    if not grouped_df.empty and "risk_level" in grouped_df.columns:
        dist = grouped_df["risk_level"].value_counts()
        order = ["High", "Medium", "Low", "Unclassified"]
        counts = {lvl: int(dist.get(lvl, 0)) for lvl in order}

        colours = {
            "High":         "#ef4444",
            "Medium":       "#f59e0b",
            "Low":          "#10b981",
            "Unclassified": "#475569",
        }

        # Simple bar chart using st.bar_chart friendly data
        chart_data = pd.DataFrame({
            "Risk Level": list(counts.keys()),
            "Count":      list(counts.values()),
        })
        st.bar_chart(chart_data.set_index("Risk Level"), color="#3b82f6", height=260)

        # Pill summary
        cols_risk = st.columns(4)
        for i, lvl in enumerate(order):
            cols_risk[i].metric(lvl, counts[lvl])

        st.caption(
            "⚠️ Research note: risk levels are experimental image-plane "
            "estimates, not validated safety classifications."
        )
    else:
        st.info(
            "No risk analysis results found yet. Run the Video Analysis "
            "pipeline to generate risk data."
        )

# ── Recent events table ──────────────────────────────────────────────
with right_col:
    st.subheader("Recent Events")

    if not events_df.empty:
        show_cols = [
            c for c in [
                "event_id", "start_time_s", "duration_s",
                "pedestrian_track_id", "vehicle_track_id",
                "peak_risk_score", "event_status",
            ]
            if c in events_df.columns
        ]
        recent = events_df.sort_values(
            "start_time_s" if "start_time_s" in events_df.columns else events_df.columns[0],
            ascending=False,
        ).head(10)

        st.dataframe(
            recent[show_cols].style.format({
                "start_time_s":   "{:.2f}s",
                "duration_s":     "{:.2f}s",
                "peak_risk_score": "{:.3f}",
            }, na_rep="—"),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("📁 Source file"):
            st.code(str(event_files[0].name))
    else:
        st.info(
            "No grouped events found yet. Complete the full analysis pipeline "
            "to see events here."
        )

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 4 — Video library status
# ════════════════════════════════════════════════════════════════════

st.subheader("Video Library")

if not videos:
    st.info("No videos registered yet. Go to **Video Analysis** to upload a video.")
else:
    vid_df = pd.DataFrame(videos)
    display_cols = [c for c in ["video_id", "filename", "status", "created_at", "result_path"] if c in vid_df.columns]

    def colour_status(val):
        colour_map = {
            "completed":  "color: #34d399; font-weight:600;",
            "processing": "color: #fbbf24; font-weight:600;",
            "pending":    "color: #94a3b8; font-weight:600;",
            "failed":     "color: #f87171; font-weight:600;",
        }
        return colour_map.get(str(val).lower(), "")

    styled = vid_df[display_cols].style.applymap(
        colour_status, subset=["status"] if "status" in display_cols else []
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 5 — Processing pipeline status
# ════════════════════════════════════════════════════════════════════

st.subheader("Analysis Pipeline Status")

pipeline_steps = {
    "YOLO + ByteTrack (Tracking CSVs)":   ("*_tracking.csv",              RESULTS_DIR),
    "Trajectory Extraction":              ("*_trajectories.csv",          RESULTS_DIR),
    "CPA Estimation":                     ("*_trajectories_cpa.csv",      RESULTS_DIR),
    "Risk Scoring":                       ("*_trajectories_cpa_risk.csv", RESULTS_DIR),
    "Event Grouping":                     ("*_events.csv",                RESULTS_DIR),
}

# Also check data/videos directory for older outputs
alt_dirs = [DATA_VIDEOS]

p_cols = st.columns(len(pipeline_steps))
for i, (label, (pattern, base_dir)) in enumerate(pipeline_steps.items()):
    found = list(base_dir.glob(pattern))
    for alt in alt_dirs:
        found += list(alt.glob(pattern))
    status_txt = f"✅ {len(found)} file(s)" if found else "⬜ Not found"
    p_cols[i].metric(label, status_txt)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 6 — Quick navigation cards
# ════════════════════════════════════════════════════════════════════

st.subheader("Quick Access")

nav_c1, nav_c2, nav_c3 = st.columns(3)

with nav_c1:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">🎬</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Video Analysis</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Upload videos, run YOLO + ByteTrack, inspect trajectories and CPA results.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_c2:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">🔗</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Causal Analysis</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Explore causal factors behind pedestrian–vehicle risk using structural models.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_c3:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">🔀</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Counterfactual Analysis</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Simulate alternative interventions and compare estimated risk outcomes.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

nav_c4, nav_c5, nav_c6 = st.columns(3)

with nav_c4:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">📋</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Event History</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Review and filter all grouped pedestrian–vehicle interaction events.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_c5:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">🔔</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Alert Settings</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Configure risk thresholds, persistence rules, and future MQTT alerts.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_c6:
    st.markdown(
        """
        <div class="cg-card">
          <div style="font-size:1.6rem;">⚗️</div>
          <div style="font-size:1rem; font-weight:600; color:#f1f5f9; margin:6px 0 4px;">Research Platform</div>
          <div style="color:#64748b; font-size:0.83rem;">
            Decoupled safety monitoring · Causal reasoning · Edge AI integration.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Footer ───────────────────────────────────────────────────────────
st.divider()
st.caption(
    "CAUSALGUARD-EDGE · B.Tech Final Year Project · "
    "All risk estimates are experimental image-plane results and are not "
    "validated collision predictions."
)
