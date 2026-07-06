"""Thin wrapper over the GitHub search API. Rate-limit hits log and return
partial results instead of crashing the ingest."""
import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

log = logging.getLogger("github")
API = "https://api.github.com"
# ponytail: first page only per source (30 items) — keeps us far from search
# rate limits; upgrade path is paginating with the Link header.
PER_PAGE = 30


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(path: str, params: dict | None = None) -> dict | None:
    """GET with one retry on secondary-rate-limit. None on failure."""
    url = f"{API}{path}"
    for attempt in (1, 2):
        try:
            resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        except requests.RequestException as e:
            log.warning("request failed %s: %s", path, e)
            return None
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (403, 429) and attempt == 1:
            wait = int(resp.headers.get("Retry-After", "5"))
            log.warning("rate limited on %s, retrying in %ss", path, wait)
            time.sleep(min(wait, 30))
            continue
        log.warning("GitHub %s -> %s: %s", path, resp.status_code, resp.text[:200])
        return None
    return None


def check_auth() -> bool:
    data = _get("/rate_limit")
    return data is not None


def search_topic_repos() -> list[dict]:
    """Full repo objects tagged topic:claude-code, most recently pushed first."""
    data = _get(
        "/search/repositories",
        {"q": "topic:claude-code", "sort": "updated", "per_page": PER_PAGE},
    )
    return data.get("items", []) if data else []


def search_claude_md_repos() -> list[str]:
    """full_names of repos with a root CLAUDE.md (code search returns partial
    repo objects, so we only take names and hydrate later)."""
    data = _get(
        "/search/code",
        {"q": "filename:CLAUDE.md path:/", "per_page": PER_PAGE},
    )
    if not data:
        return []
    return [item["repository"]["full_name"] for item in data.get("items", [])]


def search_commit_trailer_repos() -> list[str]:
    """full_names of repos with Claude Code's Co-Authored-By commit trailer."""
    data = _get(
        "/search/commits",
        {"q": '"Co-Authored-By: Claude"', "sort": "committer-date", "per_page": PER_PAGE},
    )
    if not data:
        return []
    return [item["repository"]["full_name"] for item in data.get("items", [])]


def get_repo(full_name: str) -> dict | None:
    """Full repo object for one repo (used to hydrate code/commit search hits)."""
    return _get(f"/repos/{full_name}")
