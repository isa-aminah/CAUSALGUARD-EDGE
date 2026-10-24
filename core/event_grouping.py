
from pathlib import Path

import pandas as pd


# Initial configurable settings; validate against labelled videos.
MAX_EVENT_GAP_SECONDS = 1.0
MIN_CANDIDATE_OBSERVATIONS = 2


def group_events(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Group risk rows into pair-level events and summarize candidates."""

    required = [
        "timestamp_seconds",
        "pedestrian_track_id",
        "vehicle_track_id",
        "risk_score",
        "risk_level",
        "near_miss_candidate",
    ]

    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data = data.copy()
    data["timestamp_seconds"] = pd.to_numeric(
        data["timestamp_seconds"], errors="coerce"
    )
    data["risk_score"] = pd.to_numeric(
        data["risk_score"], errors="coerce"
    )
    data["near_miss_candidate"] = (
        data["near_miss_candidate"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1"])
    )

    data = data.dropna(
        subset=[
            "timestamp_seconds",
            "pedestrian_track_id",
            "vehicle_track_id",
        ]
    )

    data = data.sort_values(
        [
            "pedestrian_track_id",
            "vehicle_track_id",
            "timestamp_seconds",
        ]
    ).reset_index(drop=True)

    pair_columns = ["pedestrian_track_id", "vehicle_track_id"]

    # Start a new event when the track pair changes or the time gap
    # exceeds the configured event gap.
    time_gap = data.groupby(pair_columns)["timestamp_seconds"].diff()

    new_event = (
        time_gap.isna()
        | (time_gap > MAX_EVENT_GAP_SECONDS)
        | data[pair_columns].ne(data[pair_columns].shift()).any(axis=1)
    )

    data["event_sequence"] = new_event.cumsum()

    # Count candidate observations per event.
    candidate_counts = data.groupby("event_sequence")[
        "near_miss_candidate"
    ].sum()

    data["candidate_observations"] = (
        data["event_sequence"].map(candidate_counts).astype(int)
    )

    data["persistent_candidate"] = (
        data["candidate_observations"] >= MIN_CANDIDATE_OBSERVATIONS
    ) & data["near_miss_candidate"]

    # Assign stable-within-this-analysis event labels.
    data["event_id"] = data["event_sequence"].map(
        lambda sequence: f"EVT-{int(sequence):04d}"
    )

    summaries = []

    for event_id, group in data.groupby("event_id", sort=False):
        candidate_rows = group[group["near_miss_candidate"]]
        scored = group["risk_score"].dropna()

        summaries.append(
            {
                "event_id": event_id,
                "pedestrian_track_id": group[
                    "pedestrian_track_id"
                ].iloc[0],
                "vehicle_track_id": group[
                    "vehicle_track_id"
                ].iloc[0],
                "start_time_s": group["timestamp_seconds"].min(),
                "end_time_s": group["timestamp_seconds"].max(),
                "duration_s": (
                    group["timestamp_seconds"].max()
                    - group["timestamp_seconds"].min()
                ),
                "observations": len(group),
                "candidate_observations": len(candidate_rows),
                "peak_risk_score": (
                    scored.max() if not scored.empty else None
                ),
                "persistent_candidate": (
                    len(candidate_rows) >= MIN_CANDIDATE_OBSERVATIONS
                ),
                "event_status": (
                    "Persistent candidate"
                    if len(candidate_rows) >= MIN_CANDIDATE_OBSERVATIONS
                    else (
                        "Unconfirmed candidate"
                        if len(candidate_rows) > 0
                        else "No candidate"
                    )
                ),
            }
        )

    event_summary = pd.DataFrame(summaries)

    return data, event_summary


def main():
    results_dir = Path("results")

    inputs = sorted(
        results_dir.glob("*_cpa_risk.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not inputs:
        raise FileNotFoundError(
            "No *_cpa_risk.csv file found in results/."
        )

    input_path = inputs[0]
    output_rows = input_path.with_name(
        input_path.stem + "_grouped_rows.csv"
    )
    output_events = input_path.with_name(
        input_path.stem + "_events.csv"
    )

    print(f"Input: {input_path}")

    source = pd.read_csv(input_path)
    grouped_rows, event_summary = group_events(source)

    grouped_rows.to_csv(output_rows, index=False)
    event_summary.to_csv(output_events, index=False)

    print("\nEvent grouping completed.")
    print(f"Grouped rows: {output_rows}")
    print(f"Event summary: {output_events}")
    print(f"Total grouped events: {len(event_summary)}")
    print(
        "Persistent candidate events:",
        int(event_summary["persistent_candidate"].sum()),
    )
    print(
        "Unconfirmed candidate events:",
        int((event_summary["event_status"] == "Unconfirmed candidate").sum()),
    )


if __name__ == "__main__":
    main()
