#!/usr/bin/env bash
# Run ON the Alpaca droplet after `git pull` (or pipe: `ssh root@alpaca bash -s < thisfile`).
set -euo pipefail
ROOT="${TRADING_BOT_ROOT:-/root/stock-bot}"
cd "$ROOT"

git pull --ff-only origin main

mkdir -p reports/archive
STAMP="$(date -u +%F_%H%M)"
if compgen -G "logs/*.jsonl" >/dev/null; then
  tar -czvf "reports/archive/logs_pre_v2_live_${STAMP}.tar.gz" logs/*.jsonl
  truncate -s 0 logs/*.jsonl
else
  echo "No logs/*.jsonl to archive (ok)."
fi

mkdir -p state
echo '{}' > state/alpaca_10trade_harvester_sent.json
echo '{}' > state/alpaca_100trade_sent.json
echo '{}' > state/alpaca_milestone_250_state.json
rm -f state/alpaca_milestone_integrity_arm.json
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "{\"started_at_utc\": \"${NOW}\", \"fired_milestones\": []}" > state/epoch_state.json

sudo systemctl restart stock-bot.service
systemctl is-active stock-bot.service
systemctl status stock-bot.service --no-pager -l | head -n 30
