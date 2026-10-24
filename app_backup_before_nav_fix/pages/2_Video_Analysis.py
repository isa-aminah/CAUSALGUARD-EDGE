"""
CAUSALGUARD-EDGE  —  Page 2: Video Analysis
Upload videos, run YOLO + ByteTrack, inspect trajectories and CPA/risk results.
The existing working upload → track → playback pipeline is fully preserved here.
"""

import sqlite3
import subprocess
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Local imports ────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from style import inject_css
from storage.video_manager import register_video, list_videos
from core.tracking import track_video
from core.trajectory import analyse_trajectories
from core.safety_metrics import analyse_track_pairs
from core.risk_analysis import calculate_risk_scores
from core.event_grouping import group_events

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "causalguard.db"
TEMP_DIR      = PROJECT_ROOT / "data" / "temporary"
RESULTS_DIR   = PROJECT_ROOT / "results"
DATA_VIDEOS   = PROJECT_ROOT / "data" / "videos"

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Video Analysis | CAUSALGUARD-EDGE",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:12px 0 20px 0;">
          <div style="font-size:2rem;">🛡️</div>
          <div style="font-size:1.05rem; font-weight:700; color:#f1f5f9;">CAUSALGUARD</div>
          <div style="font-size:0.7rem; color:#3b82f6; text-transform:uppercase; letter-spacing:0.1em;">EDGE</div>
        </div>
        <hr style="border-color:rgba(59,130,246,0.2); margin:0 0 12px 0;">
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Navigation**")
    st.page_link("app/dashboard.py",                               label="📊 Dashboard")
    st.page_link("app/pages/2_Video_Analysis.py",                  label="🎬 Video Analysis")
    st.page_link("app/pages/3_Causal_Analysis.py",                 label="🔗 Causal Analysis")
    st.page_link("app/pages/4_Counterfactual_Analysis.py",         label="🔀 Counterfactual Analysis")
    st.page_link("app/pages/5_Event_History.py",                   label="📋 Event History")
    st.page_link("app/pages/6_Alert_Settings.py",                  label="🔔 Alert Settings")

# ── Page header ──────────────────────────────────────────────────────
st.markdown(
    """
    <div class="page-header">
      <h1 style="margin:0;">🎬 Video Analysis</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Upload · Detect · Track · Analyse trajectories and risk
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — Upload new videos
# ════════════════════════════════════════════════════════════════════

with st.expander("📤 Upload New Videos", expanded=True):
    uploaded_files = st.file_uploader(
        "Select one or more video files",
        type=["mp4", "avi", "mov", "mkv"],
        accept_multiple_files=True,
        key="video_upload_pg2",
    )

    if st.button("Register Selected Videos", type="primary", key="btn_register"):
        if not uploaded_files:
            st.warning("Select at least one video file first.")
        else:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            ok_count = 0
            for uf in uploaded_files:
                tmp_path = TEMP_DIR / f"{uuid.uuid4().hex}_{Path(uf.name).name}"
                try:
                    tmp_path.write_bytes(uf.getbuffer())
                    vid_id = register_video(str(tmp_path))
                    st.success(f"✅  Registered **{uf.name}** (ID: {vid_id})")
                    ok_count += 1
                except Exception as exc:
                    st.error(f"Failed to register {uf.name}: {exc}")
                finally:
                    tmp_path.unlink(missing_ok=True)
            if ok_count:
                st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — Video library
# ════════════════════════════════════════════════════════════════════

videos = list_videos()
st.subheader(f"Video Library  ({len(videos)} registered)")

if not videos:
    st.info("No videos yet. Upload a video above.")
else:
    lib_df = pd.DataFrame(videos)
    status_colours = {
        "completed":  "#34d399",
        "processing": "#fbbf24",
        "pending":    "#94a3b8",
        "failed":     "#f87171",
    }

    for video in videos:
        status_col = status_colours.get(video["status"], "#94a3b8")
        with st.expander(
            f"ID {video['video_id']}  ·  {video['filename']}  "
            f"[{video['status'].upper()}]"
        ):
            c_left, c_right = st.columns([1, 1])
            with c_left:
                st.markdown(f"**Status:** <span style='color:{status_col}; font-weight:600;'>{video['status'].title()}</span>", unsafe_allow_html=True)
                st.markdown(f"**Registered:** {video.get('created_at', '—')}")
                if video.get("result_path"):
                    st.markdown(f"**Result:** `{video['result_path']}`")

                original_path = PROJECT_ROOT / video["storage_path"]
                if original_path.is_file():
                    st.video(str(original_path))
                else:
                    st.warning("Original video file not found on disk.")

            with c_right:
                # Show tracked video if available
                result_path = video.get("result_path")
                if result_path:
                    result_p = PROJECT_ROOT / result_path
                    web_p = result_p.with_name(result_p.stem + "_web.mp4")
                    if web_p.is_file():
                        st.caption("Tracked video (H.264 web version):")
                        st.video(str(web_p))
                    elif result_p.is_file():
                        st.caption("Tracked video:")
                        st.video(str(result_p))

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 3 — Run YOLO + ByteTrack
# ════════════════════════════════════════════════════════════════════

st.subheader("🤖 Run YOLO + ByteTrack")

if not videos:
    st.info("Register a video first.")
else:
    selected_video = st.selectbox(
        "Choose a video to analyse",
        videos,
        format_func=lambda v: f"ID {v['video_id']}  —  {v['filename']}  [{v['status']}]",
        key="analysis_video_pg2",
    )

    st.caption(
        "Tracking processes every frame and may take several minutes for longer videos. "
        "Keep this tab open until it completes."
    )

    track_col1, track_col2 = st.columns([1, 3])
    run_track = track_col1.button("▶  Run YOLO + ByteTrack", type="primary", key="btn_track")

    if run_track:
        source_path = PROJECT_ROOT / selected_video["storage_path"]
        video_id    = selected_video["video_id"]

        if not source_path.is_file():
            st.error("Original video file not found on disk.")
        else:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.execute(
                        "UPDATE videos SET status = 'processing' WHERE video_id = ?",
                        (video_id,),
                    )
                    conn.commit()

                with st.spinner("Running YOLO detection + ByteTrack … (this may take a while)"):
                    result = track_video(str(source_path))

                output_path = Path(result["video"]).resolve()
                csv_path    = Path(result["csv"]).resolve()

                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.execute(
                        "UPDATE videos SET status = 'completed', result_path = ? WHERE video_id = ?",
                        (str(output_path.relative_to(PROJECT_ROOT)), video_id),
                    )
                    conn.commit()

                st.session_state["last_tracking_result"]   = result
                st.session_state["last_tracking_video_id"] = video_id
                st.success("✅  Tracking completed successfully!")

            except Exception as err:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.execute(
                        "UPDATE videos SET status = 'failed' WHERE video_id = ?",
                        (video_id,),
                    )
                    conn.commit()
                st.error(f"Tracking failed: {err}")

    # ── Display last tracking result (no rerun) ──────────────────────
    result        = st.session_state.get("last_tracking_result")
    result_vid_id = st.session_state.get("last_tracking_video_id")

    if result and result_vid_id == selected_video["video_id"]:
        st.subheader("Tracking Results")

        output_path = Path(result["video"]).resolve()
        csv_path    = Path(result["csv"]).resolve()
        web_path    = output_path.with_name(output_path.stem + "_web.mp4")

        m1, m2, m3 = st.columns(3)
        m1.metric("Frames Processed",  result["frames_processed"])
        m2.metric("Total Detections",  result["detections"])
        m3.metric("Unique Track IDs",  result["unique_track_ids"])

        if web_path.is_file():
            st.video(str(web_path))
        elif output_path.is_file():
            st.video(str(output_path))
            st.info("Showing original encoded video. For guaranteed browser playback run convert_video.py to produce the H.264 web version.")
        else:
            st.warning("Tracked video file not found.")

        if csv_path.is_file():
            st.download_button(
                "⬇  Download Tracking CSV",
                data=csv_path.read_bytes(),
                file_name=csv_path.name,
                mime="text/csv",
                key="dl_tracking_csv",
            )

        st.caption(f"Output: `{output_path.name}`")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 4 — Full analysis pipeline (trajectory → CPA → risk → events)
# ════════════════════════════════════════════════════════════════════

st.subheader("📈 Full Analysis Pipeline")
st.caption(
    "Run the complete pipeline: trajectory extraction → CPA estimation → "
    "risk scoring → event grouping. Only run once tracking is complete."
)

# Find available tracking CSVs
tracking_csvs = sorted(
    list(RESULTS_DIR.glob("*_tracking.csv")) +
    list(DATA_VIDEOS.glob("*_tracking.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not tracking_csvs:
    st.info("No tracking CSV files found. Run YOLO + ByteTrack first.")
else:
    chosen_csv = st.selectbox(
        "Select tracking CSV",
        tracking_csvs,
        format_func=lambda p: p.name,
        key="pipeline_csv_select",
    )

    run_pipeline = st.button("▶  Run Full Pipeline", type="primary", key="btn_full_pipeline")

    if run_pipeline and chosen_csv:
        progress = st.progress(0, text="Starting pipeline …")

        try:
            # Step 1 — Trajectories
            progress.progress(10, text="Step 1/4 — Extracting trajectories …")
            traj_result = analyse_trajectories(str(chosen_csv))
            traj_csv = traj_result["trajectory_csv"]
            st.success(f"✅  Trajectories: {traj_result['observations']} rows · {traj_result['pedestrian_tracks']} pedestrian tracks · {traj_result['vehicle_tracks']} vehicle tracks")

            # Step 2 — CPA
            progress.progress(35, text="Step 2/4 — Estimating CPA …")
            cpa_result = analyse_track_pairs(traj_csv)
            cpa_csv = cpa_result["output_csv"]
            st.success(f"✅  CPA: {cpa_result['comparisons']} comparisons · {cpa_result['valid_cpa_predictions']} valid estimates")

            # Step 3 — Risk
            progress.progress(60, text="Step 3/4 — Scoring risk …")
            cpa_df = pd.read_csv(cpa_csv)
            risk_df_new = calculate_risk_scores(cpa_df)
            risk_csv_path = Path(cpa_csv).with_name(Path(cpa_csv).stem + "_risk.csv")
            risk_df_new.to_csv(risk_csv_path, index=False)
            valid_scores = int(risk_df_new["risk_score"].notna().sum())
            st.success(f"✅  Risk scoring: {len(risk_df_new)} rows · {valid_scores} valid scores")

            # Step 4 — Event grouping
            progress.progress(85, text="Step 4/4 — Grouping events …")
            grouped_rows, event_summary = group_events(risk_df_new)
            rows_out = risk_csv_path.with_name(risk_csv_path.stem + "_grouped_rows.csv")
            evts_out = risk_csv_path.with_name(risk_csv_path.stem + "_events.csv")
            grouped_rows.to_csv(rows_out, index=False)
            event_summary.to_csv(evts_out, index=False)
            persistent = int(event_summary["persistent_candidate"].sum())
            st.success(f"✅  Events: {len(event_summary)} grouped · {persistent} persistent candidates")

            progress.progress(100, text="Pipeline complete!")

            # Store results for display
            st.session_state["pipeline_event_df"]  = event_summary
            st.session_state["pipeline_risk_df"]   = risk_df_new

        except Exception as exc:
            st.error(f"Pipeline step failed: {exc}")
            st.exception(exc)

    # Show pipeline results from session state
    ev_df_sess = st.session_state.get("pipeline_event_df")
    if ev_df_sess is not None and not ev_df_sess.empty:
        st.subheader("Event Summary")
        show = [c for c in [
            "event_id", "start_time_s", "end_time_s", "duration_s",
            "pedestrian_track_id", "vehicle_track_id",
            "observations", "candidate_observations",
            "peak_risk_score", "event_status",
        ] if c in ev_df_sess.columns]
        st.dataframe(ev_df_sess[show], use_container_width=True, hide_index=True)

        csv_bytes = ev_df_sess[show].to_csv(index=False).encode()
        st.download_button(
            "⬇  Download Event Summary CSV",
            data=csv_bytes,
            file_name="causalguard_events.csv",
            mime="text/csv",
            key="dl_event_csv",
        )

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 5 — Browse existing analysis CSVs
# ════════════════════════════════════════════════════════════════════

st.subheader("📂 Browse Saved Analysis Files")

all_csvs = sorted(
    list(RESULTS_DIR.glob("*.csv")) + list(DATA_VIDEOS.glob("*.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not all_csvs:
    st.info("No analysis CSV files found.")
else:
    selected_csv = st.selectbox(
        "Preview a CSV",
        all_csvs,
        format_func=lambda p: p.name,
        key="browse_csv",
    )
    try:
        preview_df = pd.read_csv(selected_csv)
        st.caption(f"{len(preview_df)} rows × {len(preview_df.columns)} columns  —  `{selected_csv.name}`")
        st.dataframe(preview_df.head(50), use_container_width=True, hide_index=True)

        st.download_button(
            f"⬇  Download {selected_csv.name}",
            data=selected_csv.read_bytes(),
            file_name=selected_csv.name,
            mime="text/csv",
            key="dl_browse_csv",
        )
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")

# ── Footer ───────────────────────────────────────────────────────────
st.divider()
st.caption(
    "All CPA and risk values are experimental image-plane estimates. "
    "Distances are in pixels, speeds in pixels/second. "
    "Results are not validated collision predictions."
)
