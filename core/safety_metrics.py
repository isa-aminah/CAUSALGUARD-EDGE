
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

PEDESTRIAN_CLASS_ID = 0
VEHICLE_CLASS_IDS = {2, 3, 5, 7}


def calculate_cpa(
    pedestrian_position: np.ndarray,
    vehicle_position: np.ndarray,
    pedestrian_velocity: np.ndarray,
    vehicle_velocity: np.ndarray,
) -> dict:
    """
    Calculate image-plane relative motion and closest point of approach.

    Positions are in pixels.
    Velocities are in pixels/second.
    CPA distance is in pixels, not metres.
    """

    p = np.asarray(pedestrian_position, dtype=float)
    v = np.asarray(vehicle_position, dtype=float)
    vp = np.asarray(pedestrian_velocity, dtype=float)
    vv = np.asarray(vehicle_velocity, dtype=float)

    if any(array.shape != (2,) for array in (p, v, vp, vv)):
        raise ValueError("Positions and velocities must each contain x and y.")

    if not all(np.isfinite(array).all() for array in (p, v, vp, vv)):
        raise ValueError("Positions and velocities must be finite.")

    # Relative position: pedestrian position minus vehicle position.
    r = p - v

    # Relative velocity: pedestrian velocity minus vehicle velocity.
    relative_velocity = vp - vv
    relative_speed_squared = float(
        np.dot(relative_velocity, relative_velocity)
    )

    result = {
        "relative_x_px": float(r[0]),
        "relative_y_px": float(r[1]),
        "relative_speed_px_s": float(np.linalg.norm(relative_velocity)),
        "time_to_cpa_s": None,
        "cpa_distance_px": None,
        "closing_speed_px_s": None,
        "prediction_valid": False,
        "status": "",
    }

    distance = float(np.linalg.norm(r))

    if distance > 0:
        result["closing_speed_px_s"] = float(
            -np.dot(r, relative_velocity) / distance
        )

    if relative_speed_squared <= 1e-12:
        result["status"] = "Relative velocity is approximately zero."
        return result

    # Time to closest approach under constant relative velocity.
    time_to_cpa = float(
        -np.dot(r, relative_velocity) / relative_speed_squared
    )

    if time_to_cpa < 0:
        result["status"] = "Closest approach is in the past."
        return result

    closest_relative_position = r + relative_velocity * time_to_cpa
    cpa_distance = float(np.linalg.norm(closest_relative_position))

    result.update({
        "time_to_cpa_s": time_to_cpa,
        "cpa_distance_px": cpa_distance,
        "prediction_valid": True,
        "status": "Image-plane CPA estimate; not collision confirmation.",
    })

    return result


def calculate_track_velocities(
    trajectory_csv: str,
    smoothing_window: int = 3,
) -> pd.DataFrame:
    """
    Smooth image positions and estimate image-plane velocity
    separately for each track ID.
    """

    source = Path(trajectory_csv).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Trajectory CSV not found: {source}")

    if smoothing_window < 1:
        raise ValueError("smoothing_window must be at least 1.")

    data = pd.read_csv(source)

    required = {
        "timestamp_seconds",
        "track_id",
        "class_id",
        "center_x",
        "bottom_y",
    }

    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = data.copy()
    data["track_id"] = pd.to_numeric(data["track_id"], errors="coerce")
    data = data.dropna(subset=["track_id", "timestamp_seconds"])
    data["track_id"] = data["track_id"].astype(int)

    data = data.sort_values(
        ["track_id", "timestamp_seconds"]
    ).reset_index(drop=True)

    grouped = data.groupby("track_id", sort=False)

    # Rolling median reduces isolated position jitter.
    for column in ("center_x", "bottom_y"):
        data[f"{column}_smooth"] = grouped[column].transform(
            lambda values: values.rolling(
                window=smoothing_window,
                min_periods=1,
                center=True,
            ).median()
        )

    smoothed = data.groupby("track_id", sort=False)

    data["velocity_x_px_s"] = smoothed["center_x_smooth"].transform(
        lambda values: values.diff()
    ) / smoothed["timestamp_seconds"].transform(
        lambda values: values.diff()
    )

    data["velocity_y_px_s"] = smoothed["bottom_y_smooth"].transform(
        lambda values: values.diff()
    ) / smoothed["timestamp_seconds"].transform(
        lambda values: values.diff()
    )

    # Avoid infinite velocities caused by duplicate timestamps.
    data.replace([np.inf, -np.inf], np.nan, inplace=True)

    return data


def analyse_track_pairs(trajectory_csv: str) -> dict:
    """
    Compare pedestrian and vehicle tracks at matching timestamps.

    This produces candidate image-plane CPA estimates. It does not
    classify validated near misses or calculate physical collision TTC.
    """

    data = calculate_track_velocities(trajectory_csv)

    output_rows = []

    pedestrians = data[data["class_id"] == PEDESTRIAN_CLASS_ID]
    vehicles = data[data["class_id"].isin(VEHICLE_CLASS_IDS)]

    for pedestrian_id, pedestrian_track in pedestrians.groupby("track_id"):
        pedestrian_by_time = {
            round(float(row.timestamp_seconds), 3): row
            for row in pedestrian_track.itertuples()
        }

        for vehicle_id, vehicle_track in vehicles.groupby("track_id"):
            vehicle_by_time = {
                round(float(row.timestamp_seconds), 3): row
                for row in vehicle_track.itertuples()
            }

            common_times = sorted(
                set(pedestrian_by_time) & set(vehicle_by_time)
            )

            for timestamp in common_times:
                pedestrian = pedestrian_by_time[timestamp]
                vehicle = vehicle_by_time[timestamp]

                values = [
                    pedestrian.velocity_x_px_s,
                    pedestrian.velocity_y_px_s,
                    vehicle.velocity_x_px_s,
                    vehicle.velocity_y_px_s,
                ]

                if not all(np.isfinite(value) for value in values):
                    continue

                cpa = calculate_cpa(
                    pedestrian_position=np.array([
                        pedestrian.center_x_smooth,
                        pedestrian.bottom_y_smooth,
                    ]),
                    vehicle_position=np.array([
                        vehicle.center_x_smooth,
                        vehicle.bottom_y_smooth,
                    ]),
                    pedestrian_velocity=np.array([
                        pedestrian.velocity_x_px_s,
                        pedestrian.velocity_y_px_s,
                    ]),
                    vehicle_velocity=np.array([
                        vehicle.velocity_x_px_s,
                        vehicle.velocity_y_px_s,
                    ]),
                )

                output_rows.append({
                    "timestamp_seconds": timestamp,
                    "pedestrian_track_id": int(pedestrian_id),
                    "vehicle_track_id": int(vehicle_id),
                    **cpa,
                })

    results = pd.DataFrame(output_rows)

    output_path = (
        RESULTS_DIR / f"{Path(trajectory_csv).stem}_cpa.csv"
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    return {
        "output_csv": str(output_path),
        "comparisons": len(results),
        "valid_cpa_predictions": (
            int(results["prediction_valid"].sum())
            if not results.empty else 0
        ),
        "note": (
            "Image-plane estimates only. "
            "Not validated collision predictions."
        ),
    }


if __name__ == "__main__":
    trajectory_files = sorted(
        RESULTS_DIR.glob("*_trajectories.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not trajectory_files:
        raise SystemExit(
            "No trajectory CSV found. Run python -m core.trajectory first."
        )

    source = trajectory_files[0]
    print("Input:", source.name)

    summary = analyse_track_pairs(str(source))

    print("\nCPA analysis completed.")
    for key, value in summary.items():
        print(f"{key}: {value}")
