#!/usr/bin/env bash
# Daily Telegram governance update — run after market close.
# Requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
# Usage: DATE=2026-03-12 ./run_daily_telegram_update.sh
set -euo pipefail
DATE="${DATE:-$(date +%Y-%m-%d)}"

python3 scripts/notify/build_daily_telegram_message.py "$DATE" \
  | python3 scripts/notify/send_telegram_message.py
