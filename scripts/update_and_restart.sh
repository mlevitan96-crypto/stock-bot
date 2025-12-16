#!/usr/bin/env bash
set -euo pipefail

# Single-command updater for droplet.
# Usage:
#   ./scripts/update_and_restart.sh [branch] [service] [repo_dir]
BRANCH="${1:-cursor/stock-trading-bot-review-2377}"
SERVICE="${2:-trading-bot}"
REPO_DIR="${3:-$(cd "$(dirname "$0")/.." && pwd)}"

cd "$REPO_DIR"

echo "[update] repo=$REPO_DIR branch=$BRANCH service=$SERVICE"

git fetch --all --prune
git checkout "$BRANCH"
git pull

./scripts/bootstrap_venv.sh "$REPO_DIR"

sudo ./scripts/install_systemd.sh "$REPO_DIR" "$SERVICE"

# Install/enable the self-healing doctor timer
sudo ./scripts/install_doctor_systemd.sh "$REPO_DIR" "$SERVICE"

echo "[update] OK"
