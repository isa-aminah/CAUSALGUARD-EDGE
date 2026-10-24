
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

PEDESTRIAN_CLASS_ID = 0
VEHICLE_CLASS_IDS = {2, 3, 5, 7}


def analyse_trajectories(csv_path: str) -> dict:
    """Calculate image-coordinate trajectories from ByteTrack output."""

    source = Path(csv_path).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Tracking CSV not found: {source}")

    data = pd.read_csv(source)

    required_columns = {
        "frame",
        "timestamp_seconds",
        "track_id",
        "class_id",
        "x1",
        "y1",
        "x2",
        "y2",
    }

    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(
            f"Tracking CSV is missing columns: {sorted(missing)}"
        )

    data["track_id"] = pd.to_numeric(data["track_id"], errors="coerce")
    data["class_id"] = pd.to_numeric(data["class_id"], errors="coerce")

    # Rows without tracking IDs cannot form a reliable trajectory.
    data = data.dropna(subset=["track_id", "class_id"]).copy()

    if data.empty:
        raise ValueError("No detections with tracking IDs were found.")

    data["track_id"] = data["track_id"].astype(int)
    data["class_id"] = data["class_id"].astype(int)

    # Bottom-center of each bounding box approximates the object's
    # contact point with the image plane.
    data["center_x"] = (data["x1"] + data["x2"]) / 2
    data["bottom_y"] = data["y2"]

    data = data.sort_values(
        ["track_id", "timestamp_seconds", "frame"]
    ).copy()

    grouped = data.groupby("track_id", sort=False)

    data["previous_time"] = grouped["timestamp_seconds"].shift(1)
    data["previous_x"] = grouped["center_x"].shift(1)
    data["previous_y"] = grouped["bottom_y"].shift(1)

    data["delta_time_s"] = (
        data["timestamp_seconds"] - data["previous_time"]
    )

    data["delta_x_px"] = data["center_x"] - data["previous_x"]
    data["delta_y_px"] = data["bottom_y"] - data["previous_y"]

    data["displacement_px"] = (
        data["delta_x_px"] ** 2 + data["delta_y_px"] ** 2
    ) ** 0.5

    valid_time = data["delta_time_s"] > 0

    data["image_speed_px_s"] = (
        data["displacement_px"] / data["delta_time_s"]
    ).where(valid_time)

    data["direction_x"] = (
        data["delta_x_px"] / data["displacement_px"]
    ).where(data["displacement_px"] > 0)

    data["direction_y"] = (
        data["delta_y_px"] / data["displacement_px"]
    ).where(data["displacement_px"] > 0)

    data["object_type"] = data["class_id"].map(
        lambda class_id: (
            "pedestrian"
            if class_id == PEDESTRIAN_CLASS_ID
            else "vehicle"
            if class_id in VEHICLE_CLASS_IDS
            else "other"
        )
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DIR / f"{source.stem}_trajectories.csv"

    columns = [
        "frame",
        "timestamp_seconds",
        "track_id",
        "class_id",
        "class_name",
        "object_type",
        "center_x",
        "bottom_y",
        "delta_x_px",
        "delta_y_px",
        "displacement_px",
        "image_speed_px_s",
        "direction_x",
        "direction_y",
    ]

    # Preserve class names if they exist in the tracking CSV.
    if "class_name" not in data.columns:
        data["class_name"] = data["class_id"].astype(str)

    data[columns].to_csv(output_path, index=False)

    pedestrian_ids = data.loc[
        data["object_type"] == "pedestrian", "track_id"
    ].nunique()

    vehicle_ids = data.loc[
        data["object_type"] == "vehicle", "track_id"
    ].nunique()

    return {
        "trajectory_csv": str(output_path),
        "observations": len(data),
        "unique_tracks": data["track_id"].nunique(),
        "pedestrian_tracks": int(pedestrian_ids),
        "vehicle_tracks": int(vehicle_ids),
    }


if __name__ == "__main__":
    tracking_files = sorted(
        RESULTS_DIR.glob("*_tracking.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not tracking_files:
        raise SystemExit(
            "No tracking CSV found. Run the tracking pipeline first."
        )

    tracking_csv = tracking_files[0]
    print("Input:", tracking_csv.name)

    result = analyse_trajectories(str(tracking_csv))

    print("\nTrajectory analysis completed.")
    for key, value in result.items():
        print(f"{key}: {value}")
