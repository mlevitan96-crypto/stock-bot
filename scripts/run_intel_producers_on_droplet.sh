#!/usr/bin/env bash
# Intel producers: universe → premarket → postmarket → expanded intel.
# Idempotent; logs append-only. Run on droplet.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
cd "$REPO_DIR" || exit 1

echo "Intel producers: REPO_DIR=$REPO_DIR"

git fetch origin
git pull --rebase --autostash origin main || true

# Order of operations (binding)
python3 scripts/build_daily_universe.py || true
python3 scripts/run_premarket_intel.py || true
python3 scripts/run_postmarket_intel.py || true
python3 scripts/build_expanded_intel.py || true

# Regression checks if present
python3 scripts/run_regression_checks.py || true

echo "Intel producers done."
