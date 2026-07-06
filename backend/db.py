"""SQLite storage for posts. No external DB — posts.db lives next to this file."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "posts.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    owner_login TEXT,
    owner_avatar_url TEXT,
    repo_name TEXT,
    repo_url TEXT,
    description TEXT,
    caption TEXT,
    stars INTEGER,
    language TEXT,
    signal_source TEXT,
    pushed_at TEXT,
    ingested_at TEXT
)
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def upsert_post(conn: sqlite3.Connection, post: dict) -> bool:
    """Insert or update one post. Returns True if the repo was new."""
    existed = conn.execute(
        "SELECT 1 FROM posts WHERE id = ?", (post["id"],)
    ).fetchone()
    conn.execute(
        """INSERT OR REPLACE INTO posts
           (id, owner_login, owner_avatar_url, repo_name, repo_url, description,
            caption, stars, language, signal_source, pushed_at, ingested_at)
           VALUES (:id, :owner_login, :owner_avatar_url, :repo_name, :repo_url,
                   :description, :caption, :stars, :language, :signal_source,
                   :pushed_at, :ingested_at)""",
        post,
    )
    return existed is None


def get_posts(page: int = 1, page_size: int = 20) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY pushed_at DESC LIMIT ? OFFSET ?",
            (page_size, (page - 1) * page_size),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
