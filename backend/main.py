import logging
import threading
import time
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import db
import ingest

log = logging.getLogger("server")

app = FastAPI(title="ShippedByClaude")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/posts")
def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_stars: int = Query(0, ge=0),
    sort: str = Query("top", pattern="^(latest|top)$"),
):
    return {
        "page": page,
        "page_size": page_size,
        "posts": db.get_posts(page, page_size, min_stars, sort),
    }


@app.post("/refresh")
def refresh():
    return {"new_posts": ingest.run_ingest()}


def _hourly_refresh():
    while True:
        time.sleep(3600)
        try:
            ingest.run_ingest()
        except Exception:
            log.exception("hourly ingest failed; will retry next hour")


threading.Thread(target=_hourly_refresh, daemon=True).start()

# static mount registered last so /posts and /refresh keep priority
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent / "frontend" / "dist", html=True),
    name="frontend",
)
