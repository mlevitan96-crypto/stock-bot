#!/usr/bin/env bash
# Run Alpaca DATA_READY pipeline on the droplet.
# Telegram is sent exactly once when DATA_READY is achieved (requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID).
# Usage: from repo root, ./scripts/run_alpaca_data_ready_on_droplet.sh
#
# On droplet: TELEGRAM_* are in /root/.alpaca_env (see MEMORY_BANK.md). This script sources it when present.

set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
export PYTHONPATH="$REPO"
# Droplet: load Telegram and other Alpaca env from canonical location (cron and manual runs use this)
if [ -f /root/.alpaca_env ]; then
  set -a
  source /root/.alpaca_env
  set +a
fi
# Repo .env (e.g. local or if droplet uses it)
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
exec python scripts/run_alpaca_data_ready_on_droplet.py
