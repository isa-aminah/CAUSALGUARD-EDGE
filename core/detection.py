
from pathlib import Path
import csv

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

# COCO classes: person, bicycle, car, motorcycle, bus, truck
TARGET_CLASSES = [0, 1, 2, 3, 5, 7]


def detect_video(video_path: str) -> dict:
    """Detect road users and save an annotated video and CSV."""

    source = Path(video_path).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Video not found: {source}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_video = RESULTS_DIR / f"{source.stem}_detected.mp4"
    output_csv = RESULTS_DIR / f"{source.stem}_detections.csv"

    model = YOLO("yolo11n.pt")

    capture = cv2.VideoCapture(str(source))

    if not capture.isOpened():
        raise ValueError(f"Could not open video: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or width <= 0 or height <= 0:
        capture.release()
        raise ValueError("The video has invalid FPS or dimensions.")

    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        capture.release()
        raise RuntimeError("Could not create the output video.")

    processed_frames = 0
    detection_count = 0

    try:
        with output_csv.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow([
                "frame", "timestamp_seconds", "track_id",
                "class_id", "class_name", "confidence",
                "x1", "y1", "x2", "y2"
            ])

            while True:
                success, frame = capture.read()

                if not success:
                    break

                result = model.predict(
                    frame,
                    classes=TARGET_CLASSES,
                    conf=0.25,
                    verbose=False,
                )[0]

                annotated_frame = result.plot()
                writer.write(annotated_frame)

                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0].item())
                        confidence = float(box.conf[0].item())
                        x1, y1, x2, y2 = [
                            round(value)
                            for value in box.xyxy[0].tolist()
                        ]

                        class_name = model.names[class_id]
                        timestamp = processed_frames / fps

                        csv_writer.writerow([
                            processed_frames,
                            round(timestamp, 3),
                            "",
                            class_id,
                            class_name,
                            round(confidence, 4),
                            x1, y1, x2, y2,
                        ])

                        detection_count += 1

                processed_frames += 1

                if processed_frames % 100 == 0:
                    print(
                        f"Processed {processed_frames}"
                        f"/{total_frames} frames"
                    )

    finally:
        capture.release()
        writer.release()

    return {
        "video": str(output_video),
        "csv": str(output_csv),
        "frames_processed": processed_frames,
        "detections": detection_count,
    }
