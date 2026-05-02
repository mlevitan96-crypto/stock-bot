#!/bin/bash
# Sovereign V3 root — see MEMORY_BANK_ALPACA.md §6.3.1
ROOT="${STOCK_BOT_ROOT:-/root/stock-bot-v3}"
cd "$ROOT" || exit 1
source venv/bin/activate
exec "$ROOT/venv/bin/python" deploy_supervisor.py
