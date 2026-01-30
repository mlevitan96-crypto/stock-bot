#!/usr/bin/env bash
# Pull latest EOD reports from GitHub to local board/eod/out/.
# Run from repo root; use weekdays after droplet sync (21:32 UTC).
# Ensures board/eod/out/ matches origin/main (droplet source of truth) to avoid conflicts.
# Usage: bash scripts/pull_eod_to_local.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "Pull EOD: repo root $REPO_ROOT"
git fetch origin
# Align board/eod/out/ with origin so pull never conflicts (droplet is source of truth).
git checkout origin/main -- board/eod/out/ 2>/dev/null || true
git pull origin main
echo "Done. EOD outputs in board/eod/out/"
