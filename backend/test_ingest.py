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

print("all checks passed")
