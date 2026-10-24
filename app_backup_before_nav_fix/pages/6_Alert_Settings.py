"""
CAUSALGUARD-EDGE  —  Page 6: Alert Status & Settings
Configure risk thresholds, persistence rules, and inspect alert history.
MQTT/ESP32 integration is planned but not yet implemented.
Software-only local alerts are labelled clearly as simulated.
"""

from pathlib import Path
import json
from datetime import datetime

import pandas as pd
import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from style import inject_css

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR  = PROJECT_ROOT / "results"
DATA_VIDEOS  = PROJECT_ROOT / "data" / "videos"
SETTINGS_FILE = PROJECT_ROOT / "data" / "alert_settings.json"

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alert Settings | CAUSALGUARD-EDGE",
    page_icon="🔔",
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
      <h1 style="margin:0;">🔔 Alert Status &amp; Settings</h1>
      <p style="color:#64748b; margin:4px 0 0 0; font-size:0.9rem;">
        Risk thresholds · Persistence rules · MQTT/ESP32 (planned)
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Load / init settings ─────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "risk_threshold_on":     0.60,
    "risk_threshold_off":    0.40,
    "min_consecutive_frames": 2,
    "max_event_gap_s":        1.0,
    "min_candidate_obs":      2,
    "mqtt_enabled":           False,
    "mqtt_broker":            "",
    "mqtt_port":              1883,
    "mqtt_topic":             "causalguard/alert",
    "esp32_enabled":          False,
}

def load_settings() -> dict:
    if SETTINGS_FILE.is_file():
        try:
            with SETTINGS_FILE.open() as f:
                saved = json.load(f)
            return {**DEFAULT_SETTINGS, **saved}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(cfg: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w") as f:
        json.dump(cfg, f, indent=2)

cfg = load_settings()

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — Current alert status overview
# ════════════════════════════════════════════════════════════════════

st.subheader("1 · Current Alert Status")

status_cols = st.columns(4)

status_cols[0].markdown(
    f"""
    <div class="cg-card">
      <div style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">Alert Mode</div>
      <div style="color:#34d399; font-size:1.1rem; font-weight:700; margin-top:4px;">
        🟢 SOFTWARE ONLY
      </div>
      <div style="color:#64748b; font-size:0.78rem; margin-top:6px;">
        Local simulation · No hardware
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

status_cols[1].markdown(
    f"""
    <div class="cg-card">
      <div style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">MQTT Broker</div>
      <div style="color:#f87171; font-size:1.1rem; font-weight:700; margin-top:4px;">
        ⬜ NOT CONNECTED
      </div>
      <div style="color:#64748b; font-size:0.78rem; margin-top:6px;">
        Planned — not yet implemented
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

status_cols[2].markdown(
    f"""
    <div class="cg-card">
      <div style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">ESP32 Device</div>
      <div style="color:#f87171; font-size:1.1rem; font-weight:700; margin-top:4px;">
        ⬜ NOT VERIFIED
      </div>
      <div style="color:#64748b; font-size:0.78rem; margin-top:6px;">
        Planned — hardware not connected
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Active threshold display
active_on  = cfg["risk_threshold_on"]
active_off = cfg["risk_threshold_off"]
status_cols[3].markdown(
    f"""
    <div class="cg-card">
      <div style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">Active Thresholds</div>
      <div style="font-size:0.95rem; font-weight:600; margin-top:4px; color:#f1f5f9;">
        ON ≥ <span style="color:#f87171;">{active_on:.2f}</span>
      </div>
      <div style="font-size:0.95rem; font-weight:600; color:#f1f5f9;">
        OFF ≤ <span style="color:#34d399;">{active_off:.2f}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — Risk threshold configuration
# ════════════════════════════════════════════════════════════════════

st.subheader("2 · Risk Threshold Configuration")
st.caption(
    "**Hysteresis rule:** A warning activates when risk ≥ θ_on for at least "
    "k consecutive observations. It clears when risk ≤ θ_off. "
    "θ_off must be less than θ_on to prevent rapid on/off switching."
)

th_col1, th_col2 = st.columns(2)

with th_col1:
    new_threshold_on = st.slider(
        "Activation threshold θ_on",
        min_value=0.10, max_value=1.00, step=0.05,
        value=float(cfg["risk_threshold_on"]),
        key="cfg_threshold_on",
        help="Warning activates when risk score ≥ this value",
    )
    new_threshold_off = st.slider(
        "Clearing threshold θ_off",
        min_value=0.05, max_value=0.95, step=0.05,
        value=float(cfg["risk_threshold_off"]),
        key="cfg_threshold_off",
        help="Warning clears when risk score ≤ this value. Must be < θ_on.",
    )
    if new_threshold_off >= new_threshold_on:
        st.error("⚠️  θ_off must be strictly less than θ_on to ensure hysteresis.")

with th_col2:
    new_min_frames = st.number_input(
        "Minimum consecutive candidate observations (k)",
        min_value=1, max_value=30,
        value=int(cfg["min_consecutive_frames"]),
        key="cfg_min_frames",
        help="Minimum number of consecutive frames at risk ≥ θ_on before alert fires",
    )
    new_max_gap = st.number_input(
        "Maximum event gap (seconds)",
        min_value=0.1, max_value=10.0, step=0.1,
        value=float(cfg["max_event_gap_s"]),
        key="cfg_max_gap",
        help="Time gap above which a new event group starts",
    )
    new_min_cand_obs = st.number_input(
        "Minimum candidate observations for persistence",
        min_value=1, max_value=20,
        value=int(cfg["min_candidate_obs"]),
        key="cfg_min_cand",
        help="An event is flagged 'persistent candidate' when it has at least this many candidate observations",
    )

# ── Risk band visualiser ─────────────────────────────────────────────
st.markdown("**Current illustrative risk bands:**")
band_cols = st.columns(3)
band_cols[0].metric("Low",    "0.00 – 0.30", help="Not yet calibrated")
band_cols[1].metric("Medium", "0.30 – 0.60", help="Not yet calibrated")
band_cols[2].metric("High",   "0.60 – 1.00", help="Not yet calibrated")

st.caption(
    "⚠️  These bands are illustrative engineering test categories. "
    "They must be calibrated against labelled video data before use in safety research."
)

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 3 — MQTT configuration (planned)
# ════════════════════════════════════════════════════════════════════

st.subheader("3 · MQTT Configuration (Planned)")
st.info(
    "MQTT messaging and ESP32 integration are planned future features. "
    "The fields below are preparation for that integration. "
    "They have **no effect** in the current software-only prototype."
)

mq_col1, mq_col2 = st.columns(2)

with mq_col1:
    new_mqtt_enabled = st.toggle(
        "Enable MQTT (planned — no effect currently)",
        value=bool(cfg["mqtt_enabled"]),
        key="cfg_mqtt_enabled",
        disabled=True,
    )
    new_mqtt_broker = st.text_input(
        "MQTT Broker IP or hostname",
        value=str(cfg["mqtt_broker"]),
        placeholder="e.g. 192.168.1.100",
        key="cfg_mqtt_broker",
    )
    new_mqtt_port = st.number_input(
        "MQTT Broker Port",
        min_value=1, max_value=65535,
        value=int(cfg["mqtt_port"]),
        key="cfg_mqtt_port",
    )

with mq_col2:
    new_mqtt_topic = st.text_input(
        "MQTT Alert Topic",
        value=str(cfg["mqtt_topic"]),
        key="cfg_mqtt_topic",
    )
    new_esp32_enabled = st.toggle(
        "ESP32 Device Connected (planned — not verified)",
        value=bool(cfg["esp32_enabled"]),
        key="cfg_esp32_enabled",
        disabled=True,
    )
    st.markdown(
        """
        <div class="cg-card" style="margin-top:8px;">
          <b>Planned ESP32 indicators:</b><br>
          · LED: continuous = active warning<br>
          · Buzzer: short pulses on alert<br>
          · Heartbeat ping every 5 s to confirm connection
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 4 — Save settings
# ════════════════════════════════════════════════════════════════════

if st.button("💾  Save Settings", type="primary", key="btn_save_settings"):
    if new_threshold_off >= new_threshold_on:
        st.error("Cannot save: θ_off must be strictly less than θ_on.")
    else:
        new_cfg = {
            "risk_threshold_on":      new_threshold_on,
            "risk_threshold_off":     new_threshold_off,
            "min_consecutive_frames": int(new_min_frames),
            "max_event_gap_s":        float(new_max_gap),
            "min_candidate_obs":      int(new_min_cand_obs),
            "mqtt_enabled":           False,   # forced off until implemented
            "mqtt_broker":            new_mqtt_broker,
            "mqtt_port":              int(new_mqtt_port),
            "mqtt_topic":             new_mqtt_topic,
            "esp32_enabled":          False,   # forced off until verified
        }
        save_settings(new_cfg)
        st.success(f"✅  Settings saved to `{SETTINGS_FILE.name}`")
        cfg = new_cfg

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 5 — Alert history from saved event files
# ════════════════════════════════════════════════════════════════════

st.subheader("4 · Alert History (from saved events)")
st.caption(
    "Persistent candidate events from the most recent analysis are shown here "
    "as the closest proxy for a warning history until MQTT logging is implemented."
)

event_files = sorted(
    list(RESULTS_DIR.glob("*_events.csv")) +
    list(DATA_VIDEOS.glob("*_events.csv")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

if not event_files:
    st.info("No event files found. Run the analysis pipeline first.")
else:
    selected_alert_file = st.selectbox(
        "Event file",
        event_files,
        format_func=lambda p: p.name,
        key="alert_hist_file",
    )
    try:
        ev_df = pd.read_csv(selected_alert_file)
        for col in ["peak_risk_score", "start_time_s", "end_time_s", "duration_s"]:
            if col in ev_df.columns:
                ev_df[col] = pd.to_numeric(ev_df[col], errors="coerce")

        if "persistent_candidate" in ev_df.columns:
            ev_df["persistent_candidate"] = (
                ev_df["persistent_candidate"]
                .astype(str).str.strip().str.lower()
                .isin(["true", "1", "yes"])
            )

        persistent_df = ev_df[ev_df.get("persistent_candidate", pd.Series(False))]

        a1, a2, a3 = st.columns(3)
        a1.metric("Total events",         len(ev_df))
        a2.metric("Persistent candidates",len(persistent_df))
        a3.metric("No-candidate events",  int((ev_df.get("candidate_observations", pd.Series(0)).fillna(0) == 0).sum()))

        alert_cols = [c for c in [
            "event_id", "start_time_s", "end_time_s", "duration_s",
            "pedestrian_track_id", "vehicle_track_id",
            "candidate_observations", "peak_risk_score", "event_status",
        ] if c in ev_df.columns]

        # Show the persistent + unconfirmed events as alert-worthy
        alert_df = ev_df[ev_df.get("event_status", pd.Series("")).str.contains("candidate", case=False, na=False)]

        if alert_df.empty:
            st.info("No candidate events found in this file.")
        else:
            st.dataframe(
                alert_df[alert_cols].style.format({
                    "start_time_s":   "{:.3f}",
                    "end_time_s":     "{:.3f}",
                    "duration_s":     "{:.3f}",
                    "peak_risk_score":"{:.4f}",
                }, na_rep="—"),
                use_container_width=True,
                hide_index=True,
            )

    except Exception as exc:
        st.error(f"Could not read event file: {exc}")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 6 — Simulated alert test
# ════════════════════════════════════════════════════════════════════

st.subheader("5 · Simulated Alert Test")
st.caption("Test the local alert mechanism. This is a software simulation only — no hardware is triggered.")

test_risk = st.slider(
    "Test risk value",
    0.0, 1.0, 0.65, 0.01,
    key="test_risk_slider",
)

if st.button("🔔  Simulate alert evaluation", key="btn_test_alert"):
    threshold_on  = cfg["risk_threshold_on"]
    threshold_off = cfg["risk_threshold_off"]

    if test_risk >= threshold_on:
        st.error(
            f"⚠️  **SIMULATED WARNING ACTIVE** — Risk {test_risk:.3f} ≥ θ_on {threshold_on:.2f}  "
            f"· [LOCAL SIMULATION ONLY — No hardware triggered]"
        )
    elif test_risk <= threshold_off:
        st.success(
            f"✅  **All Clear** — Risk {test_risk:.3f} ≤ θ_off {threshold_off:.2f}  "
            f"· Warning would be cleared  · [LOCAL SIMULATION ONLY]"
        )
    else:
        st.warning(
            f"⏳  **Hysteresis zone** — Risk {test_risk:.3f} is between θ_off ({threshold_off:.2f}) "
            f"and θ_on ({threshold_on:.2f}). Warning state unchanged  · [LOCAL SIMULATION ONLY]"
        )

# ── Footer ───────────────────────────────────────────────────────────
st.divider()
st.caption(
    "CAUSALGUARD-EDGE · Alert Settings · "
    "MQTT and ESP32 integration are planned future features. "
    "All thresholds require calibration against labelled data before operational use. "
    "Do not use simulated alerts as a validated safety warning system."
)
