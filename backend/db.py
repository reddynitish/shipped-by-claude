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


# HN-style gravity: stars decayed by age. Computed in SQL so LIMIT/OFFSET
# paginate the ranked set. julianday('now') - julianday(pushed_at) = age in days.
_HOTNESS = "(CAST(stars AS REAL) / pow(julianday('now') - julianday(pushed_at) + 2, 1.5))"

_ORDER = {
    "latest": "pushed_at DESC",
    "top": f"{_HOTNESS} DESC, pushed_at DESC",
}


def get_posts(
    page: int = 1,
    page_size: int = 20,
    min_stars: int = 0,
    sort: str = "top",
    conn: sqlite3.Connection | None = None,
) -> list[dict]:
    own_conn = conn is None
    if own_conn:
        conn = get_conn()
    try:
        rows = conn.execute(
            f"""SELECT * FROM posts WHERE stars >= ?
                ORDER BY {_ORDER.get(sort, _ORDER['top'])}
                LIMIT ? OFFSET ?""",
            (min_stars, page_size, (page - 1) * page_size),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own_conn:
            conn.close()
