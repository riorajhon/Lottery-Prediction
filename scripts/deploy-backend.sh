#!/bin/bash
# Deploy backend on VPS: pull latest code, install deps, restart service.
# Run from repo root: sudo ./scripts/deploy-backend.sh
# Or from anywhere: sudo /path/to/Lottery-Prediction/scripts/deploy-backend.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "[deploy] Pulling latest code..."
git pull

echo "[deploy] Installing backend dependencies..."
"$REPO_ROOT/backend/.venv/bin/pip" install -q -r "$REPO_ROOT/backend/requirements.txt"

echo "[deploy] Restarting lottery-backend..."
systemctl restart lottery-backend

echo "[deploy] Done. Check: systemctl status lottery-backend"
