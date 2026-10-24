
from pathlib import Path
from storage.video_manager import list_videos
from core.detection import detect_video

PROJECT_ROOT = Path(__file__).resolve().parent

videos = list_videos()

if not videos:
    print("No registered videos. Upload a video in the dashboard first.")
    raise SystemExit(1)

print("\nRegistered videos:")

for video in videos:
    print(
        f"ID: {video['video_id']} | "
        f"File: {video['filename']} | "
        f"Status: {video['status']}"
    )

selected_id = input("\nEnter the video ID to analyse: ").strip()

if not selected_id.isdigit():
    print("Please enter a numeric video ID.")
    raise SystemExit(1)

selected_video = next(
    (v for v in videos if v["video_id"] == int(selected_id)),
    None,
)

if selected_video is None:
    print("Video ID not found.")
    raise SystemExit(1)

video_path = PROJECT_ROOT / selected_video["storage_path"]

print("\nStarting YOLO detection...")

results = detect_video(str(video_path))

print("\nDetection completed!")
print("Processed video:", results["video"])
print("Detection CSV:", results["csv"])
print("Frames processed:", results["frames_processed"])
print("Total detections:", results["detections"])
