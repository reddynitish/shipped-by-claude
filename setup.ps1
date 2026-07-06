# ShippedByClaude one-command setup (Windows).
# Auth via GitHub CLI -> install deps -> first ingest -> start both servers.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# --- Step 0: GitHub auth ---
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Installing GitHub CLI via winget..."
    winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "One browser click needed: authorize GitHub CLI." -ForegroundColor Yellow
    gh auth login --web -h github.com --git-protocol https
}

$token = (gh auth token).Trim()
Set-Content -Path "$root\backend\.env" -Value "GITHUB_TOKEN=$token" -Encoding utf8
Write-Host "Token written to backend\.env"

# --- Verify token ---
python -c "import sys; sys.path.insert(0, r'$root\backend'); import github_client; sys.exit(0 if github_client.check_auth() else 1)"
if ($LASTEXITCODE -ne 0) { throw "GitHub token check failed. Run 'gh auth login' manually and retry." }

# --- Install deps ---
Write-Host "Installing backend deps..."
pip install -q -r "$root\backend\requirements.txt"
Write-Host "Installing frontend deps..."
Push-Location "$root\frontend"; npm install --no-fund --no-audit; Pop-Location

# --- First ingest so the feed isn't empty ---
Push-Location "$root\backend"; $env:PYTHONIOENCODING = "utf-8"; python ingest.py; Pop-Location

# --- Start both servers in their own windows ---
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "ShippedByClaude is starting. Open: http://localhost:5173" -ForegroundColor Green
