#!/usr/bin/env bash
# ShippedByClaude one-command setup (macOS/Linux).
# Auth via GitHub CLI -> install deps -> first ingest -> start both servers.
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"

# --- Step 0: GitHub auth ---
if ! command -v gh >/dev/null 2>&1; then
  echo "Installing GitHub CLI..."
  if command -v brew >/dev/null 2>&1; then brew install gh
  elif command -v apt-get >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y gh
  else echo "Install GitHub CLI manually: https://cli.github.com" && exit 1; fi
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "One browser click needed: authorize GitHub CLI."
  gh auth login --web -h github.com --git-protocol https
fi

printf 'GITHUB_TOKEN=%s\n' "$(gh auth token)" > "$root/backend/.env"
echo "Token written to backend/.env"

# --- Verify token ---
python3 -c "import sys; sys.path.insert(0, '$root/backend'); import github_client; sys.exit(0 if github_client.check_auth() else 1)" \
  || { echo "GitHub token check failed. Run 'gh auth login' manually and retry."; exit 1; }

# --- Install deps ---
echo "Installing backend deps..."
pip3 install -q -r "$root/backend/requirements.txt"
echo "Installing frontend deps..."
(cd "$root/frontend" && npm install --no-fund --no-audit)

# --- First ingest so the feed isn't empty ---
(cd "$root/backend" && python3 ingest.py)

# --- Start both servers ---
(cd "$root/backend" && python3 -m uvicorn main:app --reload --port 8000) &
(cd "$root/frontend" && npm run dev) &

echo ""
echo "ShippedByClaude is starting. Open: http://localhost:5173"
wait
