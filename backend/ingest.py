"""Ingest pipeline: fetch from 3 GitHub signals -> dedupe -> filter -> caption
-> upsert into SQLite. Run directly (python ingest.py) or via POST /refresh."""
import logging
from datetime import datetime, timedelta, timezone

import db
import github_client as gh

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ingest")

WINDOW_DAYS = 30


def make_caption(owner: str, repo_name: str, description: str | None) -> str:
    if description:
        desc = description.strip()
        if len(desc) > 120:
            desc = desc[:117].rstrip() + "..."
        return f"{owner} shipped {repo_name} — {desc}"
    return f"{owner} shipped a new project: {repo_name}"


def keep(repo: dict, cutoff: datetime) -> bool:
    """Filter: no forks, must have description, pushed within the window."""
    if repo.get("fork"):
        return False
    if not (repo.get("description") or "").strip():
        return False
    pushed = repo.get("pushed_at")
    if not pushed:
        return False
    return datetime.fromisoformat(pushed.replace("Z", "+00:00")) >= cutoff


def to_post(repo: dict, sources: set[str], now_iso: str) -> dict:
    owner = repo["owner"]["login"]
    name = repo["name"]
    return {
        "id": repo["full_name"],
        "owner_login": owner,
        "owner_avatar_url": repo["owner"]["avatar_url"],
        "repo_name": name,
        "repo_url": repo["html_url"],
        "description": repo.get("description"),
        "caption": make_caption(owner, name, repo.get("description")),
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "signal_source": ",".join(sorted(sources)),
        "pushed_at": repo.get("pushed_at"),
        "ingested_at": now_iso,
    }


def run_ingest() -> int:
    """Returns number of newly discovered posts."""
    # full_name -> (repo dict or None until hydrated, set of signal sources)
    found: dict[str, tuple[dict | None, set[str]]] = {}

    for repo in gh.search_topic_repos():
        found[repo["full_name"]] = (repo, {"topic"})
    log.info("topic search: %d repos", len(found))

    for source, names in (
        ("claude_md", gh.search_claude_md_repos()),
        ("commit_trailer", gh.search_commit_trailer_repos()),
    ):
        log.info("%s search: %d hits", source, len(names))
        for name in names:
            repo, sources = found.get(name, (None, set()))
            sources.add(source)
            found[name] = (repo, sources)

    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    now_iso = datetime.now(timezone.utc).isoformat()
    new_count = 0
    conn = db.get_conn()
    try:
        for full_name, (repo, sources) in found.items():
            if repo is None:  # code/commit search hit — hydrate to full object
                repo = gh.get_repo(full_name)
                if repo is None:
                    continue
            if not keep(repo, cutoff):
                continue
            if db.upsert_post(conn, to_post(repo, sources, now_iso)):
                new_count += 1
        conn.commit()
    finally:
        conn.close()
    log.info("ingest done: %d new posts", new_count)
    return new_count


if __name__ == "__main__":
    if not gh.check_auth():
        raise SystemExit("GitHub auth failed — is GITHUB_TOKEN set in backend/.env?")
    print(f"new posts: {run_ingest()}")
