"""
CAUSALGUARD-EDGE  —  Page 3: Causal Analysis
Defines an explicit Structural Causal Model (SCM) over observed motion
features, visualises the causal graph, and presents model-derived
explanations of pedestrian–vehicle risk.

IMPORTANT DISCLAIMER:
  All results on this page are MODEL-DERIVED from a hand-specified SCM.
  They represent structural simulations, not empirically identified causal
  effects estimated from a controlled study or randomised experiment.
  Observational video data alone cannot establish every causal claim.
  Results are labelled accordingly.
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

# -- Page config ------------------------------------------------------
st.set_page_config(
    page_title="Causal Analysis | CAUSALGUARD-EDGE",
    page_icon="Causal",
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
      <h1 style="margin:0;">Causal Analysis</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Structural Causal Model · Causal graph · Model-derived explanations
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 0 — Research disclaimer
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.info(
    "**Research disclaimer** — This page implements a hand-specified Structural Causal "
    "Model (SCM) using observed motion features from tracked video. The causal graph "
    "encodes domain assumptions. Effects are derived by structural simulation, not by "
    "randomised experiment or controlled study. All quantities labelled as 'causal' "
    "are model-derived estimates under stated assumptions."
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 1 — Load data
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.subheader("1 · Select Analysis Data")

risk_files = sorted(
    list(RESULTS_DIR.glob("*_risk.csv")) +
    list(DATA_VIDEOS.glob("*_risk.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

event_files = sorted(
    list(RESULTS_DIR.glob("*_events.csv")) +
    list(DATA_VIDEOS.glob("*_events.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not risk_files:
    st.warning(
        "No risk CSV found. Run the full analysis pipeline on the "
        "Video Analysis page first."
    )
    st.stop()

chosen_risk_file = st.selectbox(
    "Risk analysis CSV",
    risk_files,
    format_func=lambda p: p.name,
    key="causal_risk_file",
)

try:
    risk_df = pd.read_csv(chosen_risk_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

for col in ["risk_score", "time_to_cpa_s", "cpa_distance_px",
            "closing_speed_px_s", "timestamp_seconds"]:
    if col in risk_df.columns:
        risk_df[col] = pd.to_numeric(risk_df[col], errors="coerce")

valid_mask = (
    risk_df.get("prediction_valid", pd.Series(False))
    .astype(str).str.strip().str.lower().isin(["true", "1"])
)
valid_df = risk_df[valid_mask].copy()

st.caption(f"Loaded {len(risk_df)} rows · {valid_mask.sum()} with valid CPA predictions · `{chosen_risk_file.name}`")

if valid_df.empty:
    st.warning("No valid CPA predictions found in this file.")
    st.stop()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 2 — Causal graph definition
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader("2 · Causal Graph (SCM Definition)")

st.markdown(
    """
    The following directed acyclic graph (DAG) encodes the assumed causal
    structure for a single pedestrian–vehicle interaction at one timestamp.
    Arrows represent direct causal influence **under the stated assumptions**.

    ```
    Vehicle Speed (Vv)  ---------------------------------------------------
    Pedestrian Speed (Vp)  --------------------------------------------   |
                                                                      v   v
    Relative Position (r = Pp - Pv)  ------------------------->  Closing Speed (V_close)
    Relative Velocity (Vr = Vp - Vv) ------------------------->  Time to CPA (t*)
                                                                      v   v
                                                                 Distance at CPA (d_CPA)
                                                                      v
                                                               Risk Score (R)
                                                                      v
                                                         Near-Miss Candidate Flag
    ```

    **Structural equations (image-plane, pixel units):**

    | Variable | Equation | Notes |
    |---|---|---|
    | Relative position | r = Pp - Pv | Pixel difference of footpoints |
    | Relative velocity | Vr = Vp - Vv | Pixel/s difference |
    | Closing speed | V_close = -(r · Vr) / ||r|| | Positive = approaching |
    | Time to CPA | t* = -(r · Vr) / ||Vr||^2 | Undefined if Vr ~ 0 |
    | CPA distance | d_CPA = ||r + Vr · t*|| | Pixels |
    | Time score | R_T = clip(1 - t* / tau_T, 0, 1) | tau_T = 3 s |
    | Distance score | R_D = clip(1 - d_CPA / tau_D, 0, 1) | tau_D = 80 px |
    | Risk score | R = 0.5 × R_T + 0.5 × R_D | Conflict weight = 0 |

    **Key assumptions:**
    1. Constant-velocity model between consecutive frames.
    2. Image-plane geometry only — no camera calibration applied.
    3. No conflict-zone model; conflict score is currently zero.
    4. Speed proxied from pixel displacement / frame interval.
    """
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 3 — Observed feature distributions
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader("3 · Observed Feature Distributions")

tabs = st.tabs([
    "Closing Speed", "Time to CPA", "CPA Distance",
    "Risk Score", "Track-pair summary",
])

with tabs[0]:
    if "closing_speed_px_s" in valid_df.columns:
        col_a, col_b = st.columns(2)
        cs = valid_df["closing_speed_px_s"].dropna()
        col_a.metric("Mean closing speed",   f"{cs.mean():.2f} px/s")
        col_a.metric("Positive (approaching)", f"{(cs > 0).sum()} rows")
        col_a.metric("Max closing speed",    f"{cs.max():.2f} px/s")
        col_b.bar_chart(
            pd.cut(cs, bins=20).astype(str).value_counts().sort_index().rename("count"),
            height=220,
        )
    else:
        st.info("closing_speed_px_s not found in this file.")

with tabs[1]:
    if "time_to_cpa_s" in valid_df.columns:
        col_a, col_b = st.columns(2)
        ttc = valid_df["time_to_cpa_s"].dropna()
        col_a.metric("Mean time to CPA",  f"{ttc.mean():.2f} s")
        col_a.metric("Min time to CPA",   f"{ttc.min():.2f} s")
        col_a.metric("Max time to CPA",   f"{ttc.max():.2f} s")
        col_b.bar_chart(
            pd.cut(ttc, bins=15).astype(str).value_counts().sort_index().rename("count"),
            height=220,
        )
    else:
        st.info("time_to_cpa_s not found in this file.")

with tabs[2]:
    if "cpa_distance_px" in valid_df.columns:
        col_a, col_b = st.columns(2)
        dist = valid_df["cpa_distance_px"].dropna()
        col_a.metric("Mean CPA distance", f"{dist.mean():.1f} px")
        col_a.metric("Min CPA distance",  f"{dist.min():.1f} px")
        col_a.metric("Max CPA distance",  f"{dist.max():.1f} px")
        col_b.bar_chart(
            pd.cut(dist, bins=15).astype(str).value_counts().sort_index().rename("count"),
            height=220,
        )
    else:
        st.info("cpa_distance_px not found in this file.")

with tabs[3]:
    if "risk_score" in valid_df.columns:
        col_a, col_b = st.columns(2)
        rs = valid_df["risk_score"].dropna()
        col_a.metric("Mean risk score", f"{rs.mean():.3f}")
        col_a.metric("Max risk score",  f"{rs.max():.3f}")
        col_a.metric("High-risk rows (>=0.6)", f"{(rs >= 0.6).sum()}")
        if "risk_level" in valid_df.columns:
            dist2 = valid_df["risk_level"].value_counts()
            col_b.bar_chart(dist2, height=220)
    else:
        st.info("risk_score not found in this file.")

with tabs[4]:
    if "pedestrian_track_id" in valid_df.columns and "vehicle_track_id" in valid_df.columns:
        pair_summary = (
            valid_df.groupby(["pedestrian_track_id", "vehicle_track_id"])
            .agg(
                observations=("risk_score", "count"),
                mean_risk=("risk_score", "mean"),
                max_risk=("risk_score", "max"),
                mean_cpa_dist=("cpa_distance_px", "mean"),
                mean_time_cpa=("time_to_cpa_s", "mean"),
            )
            .reset_index()
            .sort_values("max_risk", ascending=False)
        )
        st.dataframe(
            pair_summary.style.format({
                "mean_risk":     "{:.3f}",
                "max_risk":      "{:.3f}",
                "mean_cpa_dist": "{:.1f}",
                "mean_time_cpa": "{:.2f}",
            }, na_rep="—"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Track-pair columns not found.")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 4 — Structural simulation: effect of changing one variable
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader("4 · Structural Simulation — Causal Effect Exploration")

st.markdown(
    """
    Choose a causal variable, adjust it, and see how the SCM propagates
    the change to the risk score. This is a **structural simulation under
    stated assumptions**, not a statistically identified causal effect.
    """
)

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    intervention_var = st.selectbox(
        "Intervention variable",
        ["Vehicle Speed (closing speed multiplier)",
         "CPA Distance (add offset in pixels)",
         "Time to CPA (add offset in seconds)"],
        key="causal_intervention_var",
    )

    if "multiplier" in intervention_var:
        speed_factor = st.slider(
            "Speed scaling factor", 0.1, 2.0, 1.0, 0.05,
            key="causal_speed_factor",
            help="1.0 = observed; < 1.0 = slower; > 1.0 = faster",
        )
        offset_dist = 0.0
        offset_time = 0.0
    elif "Distance" in intervention_var:
        offset_dist = st.slider(
            "CPA distance offset (pixels)", -60.0, 100.0, 0.0, 5.0,
            key="causal_dist_offset",
            help="Positive = objects farther apart (safer)",
        )
        speed_factor = 1.0
        offset_time  = 0.0
    else:
        offset_time = st.slider(
            "Time-to-CPA offset (seconds)", -2.0, 5.0, 0.0, 0.25,
            key="causal_time_offset",
            help="Positive = more time available (safer)",
        )
        speed_factor = 1.0
        offset_dist  = 0.0

with sim_col2:
    if not valid_df.empty and "risk_score" in valid_df.columns:

        TTC_THRESHOLD_S   = 3.0
        CPA_THRESHOLD_PX  = 80.0

        # Apply intervention to a copy of the data
        sim_df = valid_df.copy()

        if speed_factor != 1.0 and "closing_speed_px_s" in sim_df.columns:
            # Faster vehicle -> shorter time to CPA (proportional scaling)
            sim_df["time_to_cpa_s"]       = sim_df["time_to_cpa_s"] / speed_factor
            sim_df["closing_speed_px_s"]  = sim_df["closing_speed_px_s"] * speed_factor

        if offset_dist != 0.0 and "cpa_distance_px" in sim_df.columns:
            sim_df["cpa_distance_px"] = (sim_df["cpa_distance_px"] + offset_dist).clip(lower=0)

        if offset_time != 0.0 and "time_to_cpa_s" in sim_df.columns:
            sim_df["time_to_cpa_s"] = (sim_df["time_to_cpa_s"] + offset_time).clip(lower=0)

        # Recompute scores under intervention
        sim_df["time_score_cf"] = np.clip(
            1 - sim_df["time_to_cpa_s"] / TTC_THRESHOLD_S, 0, 1
        )
        sim_df["dist_score_cf"] = np.clip(
            1 - sim_df["cpa_distance_px"] / CPA_THRESHOLD_PX, 0, 1
        )
        sim_df["risk_score_cf"] = 0.5 * sim_df["time_score_cf"] + 0.5 * sim_df["dist_score_cf"]

        orig_mean = float(valid_df["risk_score"].dropna().mean())
        cf_mean   = float(sim_df["risk_score_cf"].dropna().mean())
        delta     = orig_mean - cf_mean
        pct       = (delta / orig_mean * 100) if orig_mean > 0 else 0.0

        r1, r2, r3 = st.columns(3)
        r1.metric("Factual mean risk",         f"{orig_mean:.4f}")
        r2.metric("Simulated mean risk",        f"{cf_mean:.4f}",
                  delta=f"{-delta:.4f}" if abs(delta) > 1e-6 else None,
                  delta_color="inverse")
        r3.metric("Estimated risk reduction",   f"{pct:.1f}%",
                  help="Simulated reduction in the SCM risk score — not real-world crash probability")

        # Side-by-side comparison
        compare_df = pd.DataFrame({
            "Factual risk score":       valid_df["risk_score"].dropna().values,
            "Simulated risk score": sim_df["risk_score_cf"].dropna().values[:len(valid_df["risk_score"].dropna())],
        })
        st.line_chart(compare_df, height=250)

        st.caption(
            "Note:  These are structural simulation results under the stated SCM assumptions. "
            "They are not validated causal effect estimates from a controlled study."
        )
    else:
        st.info("No valid risk rows to simulate. Check data selection above.")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 5 — Download causal analysis results
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

st.divider()
st.subheader("5 · Download Causal Analysis Results")

if not valid_df.empty:
    export_cols = [c for c in [
        "timestamp_seconds", "pedestrian_track_id", "vehicle_track_id",
        "time_to_cpa_s", "cpa_distance_px", "closing_speed_px_s",
        "time_score", "distance_score", "risk_score", "risk_level",
        "near_miss_candidate",
    ] if c in valid_df.columns]

    st.download_button(
        "Download  Download causal analysis CSV (valid rows only)",
        data=valid_df[export_cols].to_csv(index=False).encode(),
        file_name="causalguard_causal_analysis.csv",
        mime="text/csv",
        key="dl_causal_csv",
    )

# -- Footer -----------------------------------------------------------
st.divider()
st.caption(
    "CAUSALGUARD-EDGE · Causal Analysis · "
    "All causal quantities are model-derived from a hand-specified SCM. "
    "Real-world causal identification requires controlled studies or validated natural experiments."
)

