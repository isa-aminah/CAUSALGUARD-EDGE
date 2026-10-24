
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "causalguard.db"


def initialize_database():
    """Create the local database and required tables."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                filename TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN (
                        'pending', 'processing',
                        'completed', 'failed'
                    )),
                result_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id)
                    REFERENCES datasets(dataset_id)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_videos_status ON videos(status)
        """)

        connection.commit()

    print("CAUSALGUARD-EDGE database initialized.")
    print(f"Database location: {DATABASE_PATH}")


if __name__ == "__main__":
    initialize_database()
