"""Smallest runnable check for the non-trivial ingest logic (no network).
Run: python test_ingest.py"""
from datetime import datetime, timedelta, timezone

from ingest import keep, make_caption

# caption: description path, truncation, no-description path
assert make_caption("ada", "loom", "weaves things") == "ada shipped loom — weaves things"
long = "x" * 200
capped = make_caption("ada", "loom", long)
assert len(capped) <= len("ada shipped loom — ") + 120 and capped.endswith("...")
assert make_caption("ada", "loom", None) == "ada shipped a new project: loom"

# filter: fork / no description / stale / fresh
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
fresh = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
stale = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
base = {"fork": False, "description": "a thing", "pushed_at": fresh}
assert keep(base, cutoff)
assert not keep({**base, "fork": True}, cutoff)
assert not keep({**base, "description": "  "}, cutoff)
assert not keep({**base, "pushed_at": stale}, cutoff)

# get_posts: min_stars filter + top/latest ordering, on an in-memory DB
import sqlite3

import db

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.execute(db.SCHEMA)


def _post(id_, stars, days_old):
    pushed = (datetime.now(timezone.utc) - timedelta(days=days_old)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": id_, "owner_login": "o", "owner_avatar_url": "", "repo_name": id_,
        "repo_url": "", "description": "d", "caption": "c", "stars": stars,
        "language": None, "signal_source": "topic", "pushed_at": pushed,
        "ingested_at": pushed,
    }


db.upsert_post(conn, _post("old-hit", stars=500, days_old=25))   # 500/27^1.5 ≈ 3.6
db.upsert_post(conn, _post("fresh-mid", stars=60, days_old=1))   # 60/3^1.5 ≈ 11.5
db.upsert_post(conn, _post("fresh-zero", stars=0, days_old=0))   # score 0, newest push
conn.commit()

top = [p["id"] for p in db.get_posts(sort="top", conn=conn)]
assert top == ["fresh-mid", "old-hit", "fresh-zero"], top  # gravity beats raw stars; zero-star last
latest = [p["id"] for p in db.get_posts(sort="latest", conn=conn)]
assert latest == ["fresh-zero", "fresh-mid", "old-hit"], latest
filtered = [p["id"] for p in db.get_posts(sort="top", min_stars=50, conn=conn)]
assert filtered == ["fresh-mid", "old-hit"], filtered
assert db.get_posts(min_stars=1000, conn=conn) == []

print("all checks passed")
