# ShippedByClaude

A social feed of real projects people built with Claude Code.

It searches GitHub for three fingerprints Claude Code leaves behind — a `CLAUDE.md` file, the `claude-code` topic tag, and the `Co-Authored-By: Claude` commit trailer — then shows every match as a post in a scrollable, Twitter-style feed. No fake data: every card is a real repo someone pushed in the last 30 days.

## One-command setup

**Windows:**
```powershell
.\setup.ps1
```
**macOS/Linux:**
```bash
./setup.sh
```

This installs the GitHub CLI if needed, opens a browser once so you can click **Authorize** (the only manual step — GitHub requires it), writes your token to `backend/.env`, installs all dependencies, runs the first ingest, and starts both servers. Then open **http://localhost:5173**.

## Manual setup (if you'd rather)

1. **Get a GitHub token.** Easiest: install the [GitHub CLI](https://cli.github.com), run `gh auth login`, then `gh auth token`. (Or create a classic Personal Access Token at github.com → Settings → Developer settings — no special scopes needed for public search.)
2. **Create `backend/.env`** (copy `backend/.env.example`) and put the token in it:
   ```
   GITHUB_TOKEN=ghp_yourtokenhere
   ```
3. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python ingest.py            # first fetch — populates posts.db
   uvicorn main:app --reload --port 8000
   ```
4. **Frontend** (second terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. Open http://localhost:5173.

## How it works

- `POST /refresh` (or the **↻ Refresh Feed** button) fetches from all three GitHub search signals, dedupes by `owner/repo`, filters out forks, repos with no description, and anything not pushed in the last 30 days, then upserts into a local SQLite file (`backend/posts.db`).
- `GET /posts?page=1&page_size=20` serves the feed, newest push first.
- Captions are generated with a deterministic template — no LLM calls, free to run.

## Assumptions made (MVP)

- Each search signal takes only the first page of results (30 items) per refresh, to stay far away from GitHub's search rate limits. Repeated refreshes accumulate more repos over time.
- GitHub's code/commit search sometimes returns a transient timeout (HTTP 408) — the ingest logs it and continues with the other signals rather than failing.
- Code and commit search return partial repo objects, so those hits are hydrated with one extra `GET /repos/{name}` call each.
- The Vite dev server reads a `PORT` env var if set; otherwise it uses 5173. The backend accepts any localhost origin so a shifted port still works.

## Quick sanity check

```bash
cd backend && python test_ingest.py   # asserts caption + filter logic, no network
```
