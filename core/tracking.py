
from pathlib import Path
import csv

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

TARGET_CLASSES = [0, 1, 2, 3, 5, 7]


def track_video(video_path: str) -> dict:
    """Detect road users and track them using ByteTrack."""

    source = Path(video_path).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Video not found: {source}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_video = RESULTS_DIR / f"{source.stem}_tracked.mp4"
    output_csv = RESULTS_DIR / f"{source.stem}_tracking.csv"

    model = YOLO("yolo11n.pt")
    capture = cv2.VideoCapture(str(source))

    if not capture.isOpened():
        raise ValueError(f"Could not open video: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if fps <= 0 or width <= 0 or height <= 0:
        capture.release()
        raise ValueError("Invalid video FPS or dimensions.")

    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        capture.release()
        raise RuntimeError("Could not create tracked output video.")

    frame_number = 0
    detection_count = 0
    tracked_detection_count = 0
    unique_track_ids = set()

    try:
        with output_csv.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow([
                "frame",
                "timestamp_seconds",
                "track_id",
                "class_id",
                "class_name",
                "confidence",
                "x1", "y1", "x2", "y2",
            ])

            while True:
                success, frame = capture.read()

                if not success:
                    break

                result = model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=TARGET_CLASSES,
                    conf=0.25,
                    verbose=False,
                )[0]

                writer.write(result.plot())

                if result.boxes is not None:
                    boxes = result.boxes
                    has_ids = boxes.id is not None

                    for index, box in enumerate(boxes):
                        class_id = int(box.cls[0].item())
                        confidence = float(box.conf[0].item())

                        x1, y1, x2, y2 = [
                            round(value)
                            for value in box.xyxy[0].tolist()
                        ]

                        track_id = None

                        if has_ids:
                            track_id = int(boxes.id[index].item())
                            unique_track_ids.add(track_id)
                            tracked_detection_count += 1

                        csv_writer.writerow([
                            frame_number,
                            round(frame_number / fps, 3),
                            track_id if track_id is not None else "",
                            class_id,
                            model.names[class_id],
                            round(confidence, 4),
                            x1, y1, x2, y2,
                        ])

                        detection_count += 1

                frame_number += 1

                if frame_number % 100 == 0:
                    print(f"Tracked {frame_number} frames")

    finally:
        capture.release()
        writer.release()

    return {
        "video": str(output_video),
        "csv": str(output_csv),
        "frames_processed": frame_number,
        "detections": detection_count,
        "tracked_detections": tracked_detection_count,
        "unique_track_ids": len(unique_track_ids),
    }
