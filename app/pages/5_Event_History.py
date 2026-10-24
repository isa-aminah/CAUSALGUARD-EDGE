"""
CAUSALGUARD-EDGE  —  Page 5: Event History
Review and filter all grouped pedestrian–vehicle interaction events.
Shows grouped event summaries from the most recent analysis CSVs.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from style import inject_css, risk_badge

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR  = PROJECT_ROOT / "results"
DATA_VIDEOS  = PROJECT_ROOT / "data" / "videos"

# -- Page config ------------------------------------------------------
st.set_page_config(
    page_title="Event History | CAUSALGUARD-EDGE",
    page_icon="Event History",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# -- Sidebar ----------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:12px 0 20px 0;">
          <div style="font-size:1.55rem; font-weight:700; letter-spacing:0.02em;">CAUSALGUARD</div>
          
          <div style="font-size:0.7rem; color:#3b82f6; text-transform:uppercase; letter-spacing:0.1em;">EDGE</div>
        </div>
        <hr style="border-color:rgba(59,130,246,0.2); margin:0 0 12px 0;">
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Navigation**")
    st.page_link("dashboard.py",                               label="Dashboard")
    st.page_link("pages/2_Video_Analysis.py",                  label="Video Analysis")
    st.page_link("pages/3_Causal_Analysis.py",                 label="Causal Analysis")
    st.page_link("pages/4_Counterfactual_Analysis.py",         label="Counterfactual Analysis")
    st.page_link("pages/5_Event_History.py",                   label="Event History")
    st.page_link("pages/6_Alert_Settings.py",                  label="Alert Settings")

# -- Page header ------------------------------------------------------
st.markdown(
    """
    <div class="page-header">
      <h1 style="margin:0;">Event History</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Grouped pedestrian–vehicle interactions · Candidate near-miss events
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 1 — Load data
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

event_files = sorted(
    list(RESULTS_DIR.glob("*_events.csv")) +
    list(DATA_VIDEOS.glob("*_events.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not event_files:
    st.warning(
        "No event history files found. "
        "Run the full analysis pipeline on the Video Analysis page first."
    )
    st.stop()

selected_file = st.selectbox(
    "Analysis result file",
    event_files,
    format_func=lambda p: p.name,
    key="hist_event_file",
)

try:
    events = pd.read_csv(selected_file)
except Exception as exc:
    st.error(f"Could not read event file: {exc}")
    st.stop()

required_columns = {
    "event_id", "pedestrian_track_id", "vehicle_track_id",
    "start_time_s", "end_time_s", "duration_s",
    "observations", "candidate_observations",
    "peak_risk_score", "persistent_candidate", "event_status",
}
missing = required_columns - set(events.columns)
if missing:
    st.error("Missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

for col in ["start_time_s", "end_time_s", "duration_s",
            "observations", "candidate_observations", "peak_risk_score"]:
    events[col] = pd.to_numeric(events[col], errors="coerce")

events["persistent_candidate"] = (
    events["persistent_candidate"]
    .astype(str).str.strip().str.lower()
    .isin(["true", "1", "yes"])
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 2 — Top-level metrics
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

total_events      = len(events)
candidate_events  = int((events["candidate_observations"].fillna(0) > 0).sum())
persistent_events = int(events["persistent_candidate"].sum())
mean_peak_risk    = float(events["peak_risk_score"].dropna().mean()) if not events["peak_risk_score"].dropna().empty else 0.0
max_peak_risk     = float(events["peak_risk_score"].dropna().max()) if not events["peak_risk_score"].dropna().empty else 0.0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Grouped Events",    total_events)
m2.metric("Candidate Groups",        candidate_events)
m3.metric("Persistent Candidates",   persistent_events)
m4.metric("Mean Peak Risk",          f"{mean_peak_risk:.4f}")
m5.metric("Max Peak Risk",           f"{max_peak_risk:.4f}")

st.divider()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 3 — Filters
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("Filter events Filter Events")

filter_cols = st.columns([2, 2, 1, 1])

with filter_cols[0]:
    statuses = sorted(events["event_status"].fillna("Unknown").unique().tolist())
    chosen_statuses = st.multiselect(
        "Event status",
        statuses,
        default=statuses,
        key="hist_status_filter",
    )

with filter_cols[1]:
    if events["peak_risk_score"].notna().any():
        risk_min = float(events["peak_risk_score"].dropna().min())
        risk_max = float(events["peak_risk_score"].dropna().max())
        risk_range = st.slider(
            "Peak risk score range",
            min_value=round(risk_min, 3),
            max_value=round(max(risk_max, risk_min + 0.001), 3),
            value=(round(risk_min, 3), round(max(risk_max, risk_min + 0.001), 3)),
            key="hist_risk_range",
        )
    else:
        risk_range = (0.0, 1.0)

with filter_cols[2]:
    candidate_only = st.checkbox(
        "Candidates only",
        key="hist_cand_only",
    )

with filter_cols[3]:
    persistent_only = st.checkbox(
        "Persistent only",
        key="hist_persist_only",
    )

# Apply filters
filtered = events.copy()
filtered["event_status"] = filtered["event_status"].fillna("Unknown")
filtered = filtered[filtered["event_status"].isin(chosen_statuses)]
filtered = filtered[
    (filtered["peak_risk_score"].isna()) |
    (
        (filtered["peak_risk_score"] >= risk_range[0]) &
        (filtered["peak_risk_score"] <= risk_range[1])
    )
]

if candidate_only:
    filtered = filtered[filtered["candidate_observations"].fillna(0) > 0]
if persistent_only:
    filtered = filtered[filtered["persistent_candidate"]]

filtered = filtered.sort_values("start_time_s", ascending=True, na_position="last")

st.caption(f"Showing **{len(filtered)}** of **{total_events}** grouped interactions")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 4 — Events table
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

display_columns = [
    "event_id", "start_time_s", "end_time_s", "duration_s",
    "pedestrian_track_id", "vehicle_track_id",
    "observations", "candidate_observations",
    "peak_risk_score", "persistent_candidate", "event_status",
]

def colour_event_row(row):
    """Colour entire row based on event_status."""
    status = str(row.get("event_status", "")).lower()
    if "persistent" in status:
        return ["color: #f87171;" if col == "event_status" else "" for col in display_columns]
    if "unconfirmed" in status:
        return ["color: #fbbf24;" if col == "event_status" else "" for col in display_columns]
    return ["" for _ in display_columns]

st.dataframe(
    filtered[display_columns].style
    .format({
        "start_time_s":         "{:.3f}",
        "end_time_s":           "{:.3f}",
        "duration_s":           "{:.3f}",
        "peak_risk_score":      "{:.4f}",
    }, na_rep="—")
    .map(
        lambda v: "color:#f87171; font-weight:600;" if str(v).lower() == "persistent candidate" else
                ("color:#fbbf24; font-weight:600;" if str(v).lower() == "unconfirmed candidate" else ""),
        subset=["event_status"],
    )
    .map(
        lambda v: "color:#34d399; font-weight:600;" if str(v).lower() in ["true", "yes", "1"] else "",
        subset=["persistent_candidate"],
    ),
    use_container_width=True,
    hide_index=True,
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 5 — Event detail view
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader(" Event Detail")

if not filtered.empty:
    selected_id = st.selectbox(
        "Select event for detail view",
        filtered["event_id"].tolist(),
        key="hist_detail_id",
    )
    detail = filtered[filtered["event_id"] == selected_id].iloc[0]

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(
            f"""
            <div class="cg-card">
              <div style="color:#64748b; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">Event ID</div>
              <div style="font-size:1.5rem; font-weight:700; color:#f1f5f9;">{detail['event_id']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric("Pedestrian Track ID", str(int(detail.get("pedestrian_track_id", 0))))
        st.metric("Vehicle Track ID",    str(int(detail.get("vehicle_track_id", 0))))

    with d2:
        st.metric("Start time",   f"{detail.get('start_time_s', 0):.3f} s")
        st.metric("End time",     f"{detail.get('end_time_s', 0):.3f} s")
        st.metric("Duration",     f"{detail.get('duration_s', 0):.3f} s")

    with d3:
        st.metric("Total observations",    str(int(detail.get("observations", 0))))
        st.metric("Candidate observations",str(int(detail.get("candidate_observations", 0))))
        peak = detail.get("peak_risk_score")
        st.metric("Peak risk score", f"{peak:.4f}" if pd.notna(peak) else "—")

    ev_status = str(detail.get("event_status", "—"))
    is_persistent = detail.get("persistent_candidate", False)

    if "persistent" in ev_status.lower():
        st.error(f" Event Status: **{ev_status}**  ·  Persistent: **{is_persistent}**")
    elif "unconfirmed" in ev_status.lower():
        st.warning(f" Event Status: **{ev_status}**  ·  Persistent: **{is_persistent}**")
    else:
        st.info(f"Not found: Event Status: **{ev_status}**  ·  Persistent: **{is_persistent}**")

    st.markdown(
        """
        **Links to deeper analysis:**
        Navigate to **Causal Analysis** or **Counterfactual Analysis**
        and select the same pedestrian–vehicle pair to investigate this event further.
        """,
    )

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 6 — Download
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader("Download  Download")

csv_bytes = filtered[display_columns].to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered event history (CSV)",
    data=csv_bytes,
    file_name="causalguard_event_history_filtered.csv",
    mime="text/csv",
    key="hist_dl_filtered",
)

full_bytes = events[display_columns].to_csv(index=False).encode("utf-8")
st.download_button(
    "Download complete event history (CSV)",
    data=full_bytes,
    file_name="causalguard_event_history_full.csv",
    mime="text/csv",
    key="hist_dl_full",
)

# -- Footer -----------------------------------------------------------
st.divider()
st.caption(
    "Research note: candidate groups are algorithmic indicators derived from the SCM risk model. "
    "They are not confirmed collisions or validated near-miss events. "
    "Risk scores and persistence thresholds require calibration against labelled data."
)

