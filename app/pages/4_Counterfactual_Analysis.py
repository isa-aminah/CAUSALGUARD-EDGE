"""
CAUSALGUARD-EDGE  —  Page 4: Counterfactual Analysis
Select a saved event, define an intervention, recompute risk under the
counterfactual scenario, and compare factual vs. simulated outcomes.

DISCLAIMER: All outcomes are simulated under the stated SCM assumptions.
They do not prove that any real-world intervention would have prevented
a collision.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from style import inject_css

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR  = PROJECT_ROOT / "results"
DATA_VIDEOS  = PROJECT_ROOT / "data" / "videos"

TTC_THRESHOLD_S  = 3.0
CPA_THRESHOLD_PX = 80.0
WEIGHT_T = 0.5
WEIGHT_D = 0.5

# -- Page config ------------------------------------------------------
st.set_page_config(
    page_title="Counterfactual Analysis | CAUSALGUARD-EDGE",
    page_icon="Counterfactual",
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
      <h1 style="margin:0;">Counterfactual Analysis</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Simulate alternative interventions · Compare factual vs. counterfactual risk
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "**Research disclaimer** — Counterfactual outcomes are computed by applying "
    "an explicit intervention to the SCM variables and recomputing risk scores. "
    "Results are labelled as **simulated** and do not prove that any real-world "
    "action would have prevented a collision."
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 1 — Load event and risk data
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("1 · Select an Event for Analysis")

event_files = sorted(
    list(RESULTS_DIR.glob("*_events.csv")) +
    list(DATA_VIDEOS.glob("*_events.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

risk_files = sorted(
    list(RESULTS_DIR.glob("*_risk.csv")) +
    list(DATA_VIDEOS.glob("*_risk.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not event_files or not risk_files:
    st.warning(
        "No event or risk CSV files found. "
        "Run the full analysis pipeline on the Video Analysis page first."
    )
    st.stop()

chosen_event_file = st.selectbox(
    "Event summary CSV",
    event_files,
    format_func=lambda p: p.name,
    key="cf_event_file",
)
chosen_risk_file = st.selectbox(
    "Risk CSV (source data for this event file)",
    risk_files,
    format_func=lambda p: p.name,
    key="cf_risk_file",
)

try:
    events_df = pd.read_csv(chosen_event_file)
    risk_df   = pd.read_csv(chosen_risk_file)
except Exception as exc:
    st.error(f"Could not read files: {exc}")
    st.stop()

for col in ["peak_risk_score", "start_time_s", "end_time_s", "duration_s",
            "observations", "candidate_observations"]:
    if col in events_df.columns:
        events_df[col] = pd.to_numeric(events_df[col], errors="coerce")

for col in ["risk_score", "time_to_cpa_s", "cpa_distance_px",
            "closing_speed_px_s", "timestamp_seconds"]:
    if col in risk_df.columns:
        risk_df[col] = pd.to_numeric(risk_df[col], errors="coerce")

# Filter events that have at least one candidate observation
candidate_mask = events_df.get("candidate_observations", pd.Series(0)).fillna(0) > 0
candidate_events = events_df[candidate_mask].sort_values(
    "peak_risk_score", ascending=False, na_position="last"
)

if candidate_events.empty:
    st.info(
        "No candidate events found. All interactions in this file have zero "
        "candidate observations. Try a different event file or re-run the pipeline."
    )
    # Still allow all events to be selected
    candidate_events = events_df.copy()

selected_event_id = st.selectbox(
    "Choose an event",
    candidate_events["event_id"].tolist() if "event_id" in candidate_events.columns else [],
    key="cf_event_id",
)

if not selected_event_id:
    st.info("No events available. Check data above.")
    st.stop()

event_row = events_df[events_df["event_id"] == selected_event_id].iloc[0]

# Pull matching risk rows for this pedestrian–vehicle pair
ped_id  = event_row.get("pedestrian_track_id")
veh_id  = event_row.get("vehicle_track_id")
start_t = event_row.get("start_time_s", 0.0)
end_t   = event_row.get("end_time_s", 1e9)

pair_mask = (
    (risk_df.get("pedestrian_track_id", pd.Series()) == ped_id) &
    (risk_df.get("vehicle_track_id",    pd.Series()) == veh_id)
)
if "timestamp_seconds" in risk_df.columns:
    pair_mask &= (risk_df["timestamp_seconds"] >= start_t - 0.1)
    pair_mask &= (risk_df["timestamp_seconds"] <= end_t   + 0.1)

pair_df = risk_df[pair_mask].copy()

valid_mask = (
    pair_df.get("prediction_valid", pd.Series(False))
    .astype(str).str.strip().str.lower().isin(["true", "1"])
)
factual_df = pair_df[valid_mask].copy()

st.divider()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 2 — Factual scenario summary
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("2 · Factual Scenario Summary")

f_cols = st.columns(5)
f_cols[0].metric("Event ID",          str(selected_event_id))
f_cols[1].metric("Pedestrian Track",  str(int(ped_id)) if pd.notna(ped_id) else "—")
f_cols[2].metric("Vehicle Track",     str(int(veh_id)) if pd.notna(veh_id) else "—")
f_cols[3].metric("Duration",          f"{event_row.get('duration_s', 0):.2f} s")
f_cols[4].metric("Peak Risk Score",   f"{event_row.get('peak_risk_score', 0):.4f}" if pd.notna(event_row.get('peak_risk_score')) else "—")

f_cols2 = st.columns(4)
f_cols2[0].metric("Observations (total)",     str(int(event_row.get("observations", 0))))
f_cols2[1].metric("Candidate observations",   str(int(event_row.get("candidate_observations", 0))))
f_cols2[2].metric("Event status",             str(event_row.get("event_status", "—")))
f_cols2[3].metric("Persistent candidate",     str(event_row.get("persistent_candidate", "—")))

if factual_df.empty:
    st.warning(
        "No valid CPA rows found for this event's track pair within the time window. "
        "The event was derived from candidate flags that may not all have valid predictions."
    )
    factual_mean_risk = float(event_row.get("peak_risk_score", 0) or 0)
else:
    factual_mean_risk = float(factual_df["risk_score"].dropna().mean() or 0)
    factual_peak_risk = float(factual_df["risk_score"].dropna().max() or 0)

    with st.expander("View factual risk rows"):
        show_cols = [c for c in [
            "timestamp_seconds", "time_to_cpa_s", "cpa_distance_px",
            "closing_speed_px_s", "time_score", "distance_score", "risk_score", "risk_level",
        ] if c in factual_df.columns]
        st.dataframe(
            factual_df[show_cols].style.format({
                "timestamp_seconds": "{:.2f}",
                "time_to_cpa_s":     "{:.3f}",
                "cpa_distance_px":   "{:.1f}",
                "closing_speed_px_s":"{:.2f}",
                "time_score":        "{:.4f}",
                "distance_score":    "{:.4f}",
                "risk_score":        "{:.4f}",
            }, na_rep="—"),
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 3 — Intervention selector
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("3 · Define an Intervention")

intervention_type = st.selectbox(
    "Intervention type",
    [
        "1 — Reduce vehicle speed (scale closing speed & shorten time-to-CPA)",
        "2 — Apply earlier braking (increase time-to-CPA by fixed offset)",
        "3 — Increase pedestrian clearance (add offset to CPA distance)",
        "4 — Delay pedestrian entry (increase both time-to-CPA and CPA distance)",
    ],
    key="cf_intervention_type",
)

int_code = int(intervention_type[0])

col_slider1, col_slider2 = st.columns(2)

if int_code == 1:
    with col_slider1:
        speed_factor = st.slider(
            "Vehicle speed factor (1.0 = observed, 0.5 = half speed)",
            0.1, 1.0, 0.7, 0.05, key="cf_speed_factor",
        )
    with col_slider2:
        st.markdown(
            f"""
            <div class="cg-card">
              <b>Assumption:</b> Halving vehicle speed scales closing speed by the same factor
              and inversely scales time-to-CPA (more time available). This is a simplified
              constant-velocity SCM approximation. Real braking involves deceleration dynamics.
            </div>
            """,
            unsafe_allow_html=True,
        )
    braking_offset = 0.0
    dist_offset    = 0.0
    ped_delay      = 0.0

elif int_code == 2:
    with col_slider1:
        braking_offset = st.slider(
            "Braking onset advance (seconds added to time-to-CPA)",
            0.0, 5.0, 1.5, 0.25, key="cf_brake_offset",
        )
    with col_slider2:
        st.markdown(
            """
            <div class="cg-card">
              <b>Assumption:</b> Earlier braking increases the time-to-CPA by the specified
              duration. This assumes the vehicle maintains lower speed throughout the approach.
            </div>
            """,
            unsafe_allow_html=True,
        )
    speed_factor = 1.0
    dist_offset  = 0.0
    ped_delay    = 0.0

elif int_code == 3:
    with col_slider1:
        dist_offset = st.slider(
            "Additional CPA distance (pixels)",
            10.0, 200.0, 50.0, 10.0, key="cf_dist_offset",
        )
    with col_slider2:
        st.markdown(
            """
            <div class="cg-card">
              <b>Assumption:</b> The pedestrian crosses farther from the vehicle's path,
              adding the specified pixel offset to the CPA distance. Does not change
              time-to-CPA.
            </div>
            """,
            unsafe_allow_html=True,
        )
    speed_factor   = 1.0
    braking_offset = 0.0
    ped_delay      = 0.0

else:  # int_code == 4
    with col_slider1:
        ped_delay = st.slider(
            "Pedestrian entry delay (seconds added to time-to-CPA)",
            0.0, 5.0, 2.0, 0.25, key="cf_ped_delay",
        )
        dist_offset = st.slider(
            "Additional CPA distance from altered path (pixels)",
            0.0, 100.0, 30.0, 5.0, key="cf_ped_dist",
        )
    with col_slider2:
        st.markdown(
            """
            <div class="cg-card">
              <b>Assumption:</b> The pedestrian waits before entering the conflict zone,
              increasing both the time-to-CPA and the CPA distance.
            </div>
            """,
            unsafe_allow_html=True,
        )
    speed_factor   = 1.0
    braking_offset = 0.0

st.divider()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 4 — Counterfactual computation
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("4 · Counterfactual Risk Estimate")

if factual_df.empty:
    st.warning(
        "Cannot compute counterfactual: no valid CPA rows for this event. "
        "Using peak risk from the event summary as factual baseline."
    )
    st.metric("Factual peak risk (from event summary)", f"{factual_mean_risk:.4f}")
else:
    cf_df = factual_df.copy()

    # Apply the chosen intervention
    if int_code == 1:
        if "closing_speed_px_s" in cf_df.columns:
            cf_df["closing_speed_px_s"] = cf_df["closing_speed_px_s"] * speed_factor
        if "time_to_cpa_s" in cf_df.columns:
            cf_df["time_to_cpa_s"] = (cf_df["time_to_cpa_s"] / speed_factor).clip(lower=0)

    elif int_code == 2:
        if "time_to_cpa_s" in cf_df.columns:
            cf_df["time_to_cpa_s"] = (cf_df["time_to_cpa_s"] + braking_offset).clip(lower=0)

    elif int_code == 3:
        if "cpa_distance_px" in cf_df.columns:
            cf_df["cpa_distance_px"] = (cf_df["cpa_distance_px"] + dist_offset).clip(lower=0)

    else:  # intervention 4
        if "time_to_cpa_s" in cf_df.columns:
            cf_df["time_to_cpa_s"] = (cf_df["time_to_cpa_s"] + ped_delay).clip(lower=0)
        if "cpa_distance_px" in cf_df.columns:
            cf_df["cpa_distance_px"] = (cf_df["cpa_distance_px"] + dist_offset).clip(lower=0)

    # Recompute risk scores
    cf_df["time_score_cf"] = np.clip(
        1.0 - cf_df["time_to_cpa_s"] / TTC_THRESHOLD_S, 0.0, 1.0
    )
    cf_df["dist_score_cf"] = np.clip(
        1.0 - cf_df["cpa_distance_px"] / CPA_THRESHOLD_PX, 0.0, 1.0
    )
    cf_df["risk_score_cf"] = (
        WEIGHT_T * cf_df["time_score_cf"] +
        WEIGHT_D * cf_df["dist_score_cf"]
    )

    factual_mean = float(factual_df["risk_score"].dropna().mean() or 0)
    cf_mean      = float(cf_df["risk_score_cf"].dropna().mean() or 0)
    factual_peak = float(factual_df["risk_score"].dropna().max() or 0)
    cf_peak      = float(cf_df["risk_score_cf"].dropna().max() or 0)

    delta_mean = factual_mean - cf_mean
    delta_peak = factual_peak - cf_peak
    pct_mean   = (delta_mean / factual_mean * 100) if factual_mean > 0 else 0.0
    pct_peak   = (delta_peak / factual_peak * 100) if factual_peak > 0 else 0.0

    # -- Side-by-side comparison --------------------------------------
    col_fact, col_cf = st.columns(2)

    with col_fact:
        st.markdown(
            """
            <div class="cg-card" style="border-color:rgba(239,68,68,0.4);">
              <div style="color:#f87171; font-weight:700; font-size:0.85rem;
                          text-transform:uppercase; letter-spacing:0.05em;">
                âšª Factual Scenario (Observed)
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric("Mean risk score (factual)", f"{factual_mean:.4f}")
        st.metric("Peak risk score (factual)", f"{factual_peak:.4f}")
        if "risk_level" in factual_df.columns:
            dist = factual_df["risk_level"].value_counts()
            st.bar_chart(dist, height=180)

    with col_cf:
        st.markdown(
            """
            <div class="cg-card" style="border-color:rgba(52,211,153,0.4);">
              <div style="color:#34d399; font-weight:700; font-size:0.85rem;
                          text-transform:uppercase; letter-spacing:0.05em;">
                Counterfactual Scenario (Simulated)
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric(
            "Mean risk score (simulated)", f"{cf_mean:.4f}",
            delta=f"{-delta_mean:+.4f}" if abs(delta_mean) > 1e-6 else None,
            delta_color="inverse",
        )
        st.metric(
            "Peak risk score (simulated)", f"{cf_peak:.4f}",
            delta=f"{-delta_peak:+.4f}" if abs(delta_peak) > 1e-6 else None,
            delta_color="inverse",
        )

        # Risk-level distribution after intervention
        def level(score):
            if pd.isna(score): return "Unclassified"
            if score >= 0.6:   return "High"
            if score >= 0.3:   return "Medium"
            return "Low"
        cf_df["risk_level_cf"] = cf_df["risk_score_cf"].map(level)
        dist_cf = cf_df["risk_level_cf"].value_counts()
        st.bar_chart(dist_cf, height=180)

    # -- Summary metrics ----------------------------------------------
    st.divider()
    st.subheader("Intervention Summary")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Î”R (mean)",   f"{delta_mean:.4f}")
    s2.metric("Î”R (peak)",   f"{delta_peak:.4f}")
    s3.metric("Mean reduction", f"{pct_mean:.1f}%")
    s4.metric("Peak reduction", f"{pct_peak:.1f}%")

    st.markdown(
        f"""
        <div class="cg-card">
          <b>Interpretation:</b><br>
          Under the counterfactual scenario "{intervention_type.split('—')[1].strip()}",
          the mean simulated risk score changes from
          <span style="color:#f87171;">{factual_mean:.4f}</span> to
          <span style="color:#34d399;">{cf_mean:.4f}</span>
          (Î” = {delta_mean:.4f}, {pct_mean:.1f}% reduction).
          The peak risk changes from {factual_peak:.4f} to {cf_peak:.4f}
          ({pct_peak:.1f}% reduction).<br><br>
          <span style="color:#64748b; font-size:0.85rem;">
          Note:  These are simulated SCM outcomes, not proof that any real-world
          intervention would have prevented a collision. Thresholds (tau_T = {TTC_THRESHOLD_S}s,
          tau_D = {CPA_THRESHOLD_PX}px) are engineering test values requiring calibration.
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Time-series comparison ---------------------------------------
    st.subheader("Risk Score Over Time")
    ts_data = pd.DataFrame({
        "Timestamp (s)":        factual_df["timestamp_seconds"].values,
        "Factual risk":         factual_df["risk_score"].values,
        "Simulated risk": cf_df["risk_score_cf"].values,
    }).set_index("Timestamp (s)")
    st.line_chart(ts_data, height=280)

    # -- Download -----------------------------------------------------
    st.divider()
    export = cf_df.copy()
    for src_col in ["timestamp_seconds", "time_to_cpa_s", "cpa_distance_px",
                     "closing_speed_px_s", "risk_score"]:
        if src_col in factual_df.columns:
            export[f"{src_col}_factual"] = factual_df[src_col].values

    export_cols = [c for c in export.columns if "_factual" in c or "_cf" in c
                   or c in ["timestamp_seconds", "pedestrian_track_id", "vehicle_track_id"]]

    st.download_button(
        "Download  Download counterfactual comparison CSV",
        data=export[export_cols].to_csv(index=False).encode(),
        file_name=f"causalguard_counterfactual_{selected_event_id}.csv",
        mime="text/csv",
        key="dl_cf_csv",
    )

# -- Footer -----------------------------------------------------------
st.divider()
st.caption(
    "CAUSALGUARD-EDGE · Counterfactual Analysis · "
    "All simulated outcomes are derived from the SCM risk model under stated assumptions. "
    "Risk scores are image-plane estimates. Percentage reductions are model quantities, "
    "not real-world collision probability reductions."
)

