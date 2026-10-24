
from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# EXPERIMENTAL SETTINGS
# These are initial image-plane settings, NOT
# validated real-world road-safety thresholds.
# --------------------------------------------------

TTC_THRESHOLD_S = 3.0
CPA_DISTANCE_THRESHOLD_PX = 80.0

WEIGHT_TTC = 0.50
WEIGHT_DISTANCE = 0.50
WEIGHT_CONFLICT = 0.00

# Illustrative risk categories; validate before use.
LOW_RISK_LIMIT = 0.30
HIGH_RISK_LIMIT = 0.60


def calculate_risk_scores(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate experimental risk scores from CPA results."""

    data = data.copy()

    required_columns = [
        "time_to_cpa_s",
        "cpa_distance_px",
        "closing_speed_px_s",
        "prediction_valid",
        "pedestrian_track_id",
        "vehicle_track_id",
        "timestamp_seconds",
    ]

    missing = [c for c in required_columns if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure numeric columns are numeric.
    for column in [
        "time_to_cpa_s",
        "cpa_distance_px",
        "closing_speed_px_s",
        "timestamp_seconds",
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    valid = (
        data["prediction_valid"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1"])
    )

    # CPA time is NOT necessarily collision TTC.
    # Use it only as a provisional time-to-CPA proxy.
    time_to_cpa = data["time_to_cpa_s"]
    distance = data["cpa_distance_px"]

    data["time_score"] = np.where(
        valid & time_to_cpa.notna() & (time_to_cpa > 0),
        np.clip(1 - time_to_cpa / TTC_THRESHOLD_S, 0, 1),
        np.nan,
    )

    data["distance_score"] = np.where(
        valid & distance.notna() & (distance >= 0),
        np.clip(1 - distance / CPA_DISTANCE_THRESHOLD_PX, 0, 1),
        np.nan,
    )

    # Conflict is unknown until a path/conflict-zone model
    # is implemented. Do not silently treat unknown as true.
    data["conflict_predicted"] = pd.Series(
        pd.NA, index=data.index, dtype="boolean"
    )
    data["conflict_score"] = np.nan

    weight_sum = WEIGHT_TTC + WEIGHT_DISTANCE + WEIGHT_CONFLICT
    if not np.isclose(weight_sum, 1.0):
        raise ValueError("Risk weights must sum to 1.")

    # Current prototype combines the two measurable proxies.
    # Conflict weight is zero until conflict prediction exists.
    data["risk_score"] = (
        WEIGHT_TTC * data["time_score"]
        + WEIGHT_DISTANCE * data["distance_score"]
    )

    # Avoid presenting a score when required measurements
    # are unavailable or invalid.
    score_available = (
        valid
        & data["time_score"].notna()
        & data["distance_score"].notna()
    )
    data.loc[~score_available, "risk_score"] = np.nan

    data["risk_level"] = "Unclassified"
    data.loc[
        score_available & (data["risk_score"] < LOW_RISK_LIMIT),
        "risk_level",
    ] = "Low"
    data.loc[
        score_available
        & (data["risk_score"] >= LOW_RISK_LIMIT)
        & (data["risk_score"] < HIGH_RISK_LIMIT),
        "risk_level",
    ] = "Medium"
    data.loc[
        score_available & (data["risk_score"] >= HIGH_RISK_LIMIT),
        "risk_level",
    ] = "High"

    # This is only a candidate flag, not a confirmed near-miss.
    data["near_miss_candidate"] = (
        score_available
        & (time_to_cpa > 0)
        & (time_to_cpa <= TTC_THRESHOLD_S)
        & (distance <= CPA_DISTANCE_THRESHOLD_PX)
        & (data["closing_speed_px_s"] > 0)
    )

    data["interpretation_note"] = (
        "Experimental image-plane estimate; "
        "not a confirmed collision or validated safety prediction."
    )

    return data


def main():
    results_dir = Path("results")
    inputs = sorted(
        results_dir.glob("*_trajectories_cpa.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not inputs:
        raise FileNotFoundError(
            "No *_trajectories_cpa.csv file found in results/."
        )

    input_path = inputs[0]
    output_path = input_path.with_name(
        input_path.stem + "_risk.csv"
    )

    print(f"Input: {input_path}")

    source = pd.read_csv(input_path)
    analysed = calculate_risk_scores(source)
    analysed.to_csv(output_path, index=False)

    print("\nRisk analysis completed.")
    print(f"Output CSV: {output_path}")
    print(f"Rows analysed: {len(analysed)}")
    print(
        "Valid risk scores:",
        int(analysed["risk_score"].notna().sum()),
    )
    print(
        "Potential near-miss candidates:",
        int(analysed["near_miss_candidate"].sum()),
    )
    print("\nRisk-level counts:")
    print(analysed["risk_level"].value_counts().to_string())
    print(
        "\nNote: These are experimental image-plane results, "
        "not validated collision predictions."
    )


if __name__ == "__main__":
    main()
