
from pathlib import Path
import subprocess
import imageio_ffmpeg

results_dir = Path(__file__).resolve().parent / "results"

videos = sorted(
    results_dir.glob("*_tracked.mp4"),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)

if not videos:
    raise SystemExit("No tracked MP4 video found in results/.")

source = videos[0]
output = source.with_name(source.stem + "_web.mp4")
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

command = [
    ffmpeg,
    "-y",
    "-i", str(source),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    "-an",
    str(output),
]

print("Converting:", source.name)

subprocess.run(command, check=True)

print("Converted video:", output)
print("Size (MB):", round(output.stat().st_size / (1024 * 1024), 2))
