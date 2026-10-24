
from pathlib import Path
import sqlite3
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = PROJECT_ROOT / "data" / "videos"
DATABASE_PATH = PROJECT_ROOT / "data" / "causalguard.db"

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def register_video(source_path: str, dataset_id: int | None = None):
    source = Path(source_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Video not found: {source}")

    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported video format: {source.suffix}")

    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            "Database not found. Run python main.py first."
        )

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    destination = VIDEO_DIR / source.name
    counter = 1

    while destination.exists():
        destination = VIDEO_DIR / (
            f"{source.stem}_{counter}{source.suffix.lower()}"
        )
        counter += 1

    shutil.copy2(source, destination)

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            cursor = connection.execute(
                """
                INSERT INTO videos
                    (dataset_id, filename, storage_path, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (
                    dataset_id,
                    destination.name,
                    str(destination.relative_to(PROJECT_ROOT)),
                ),
            )
            connection.commit()
            return cursor.lastrowid
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def list_videos():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT video_id, dataset_id, filename,
                   storage_path, status, result_path, created_at
            FROM videos
            ORDER BY video_id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    for video in list_videos():
        print(video)
