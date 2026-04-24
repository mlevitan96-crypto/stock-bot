#!/usr/bin/env bash
# Run on the Alpaca droplet after `git pull` and `systemctl restart stock-bot` (or your unit name).
# Ensures broker keys are visible (merge APCA_* into /root/.alpaca_env with the same values as systemd).
set -euo pipefail
ROOT="${TRADING_BOT_ROOT:-/root/stock-bot}"
cd "$ROOT"
# Repo .env is what systemd uses (ALPACA_KEY / ALPACA_SECRET); .alpaca_env is often Telegram-only.
if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a && . "$ROOT/.env" && set +a
elif [[ -f /root/.alpaca_env ]]; then
  # shellcheck disable=SC1091
  set -a && . /root/.alpaca_env && set +a
fi
export PYTHONPATH=.
python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --root "$ROOT" --days 90 --max-compute
python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from telemetry.alpaca_strict_completeness_gate import evaluate_completeness, STRICT_EPOCH_START; print(evaluate_completeness(Path('.'), open_ts_epoch=STRICT_EPOCH_START, audit=False))"
