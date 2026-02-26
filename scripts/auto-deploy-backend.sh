#!/bin/bash
# Cron-friendly: pull and restart backend only when origin has new commits.
# Usage in crontab (every 5 min): */5 * * * * /path/to/Lottery-Prediction/scripts/auto-deploy-backend.sh
# Uses main branch; adjust REPO and branch below if needed.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRANCH="${BRANCH:-main}"

cd "$REPO_ROOT"
git fetch -q
if [ -z "$(git rev-list "HEAD..origin/$BRANCH" 2>/dev/null)" ]; then
  exit 0
fi
git pull -q
"$REPO_ROOT/backend/.venv/bin/pip" install -q -r "$REPO_ROOT/backend/requirements.txt"
systemctl restart lottery-backend
