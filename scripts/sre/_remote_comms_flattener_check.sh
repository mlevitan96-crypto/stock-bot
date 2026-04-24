#!/usr/bin/env bash
# Run on droplet: bash scripts/sre/_remote_comms_flattener_check.sh
# Or: ssh root@alpaca 'bash -s' < scripts/sre/_remote_comms_flattener_check.sh
set -euo pipefail
cd /root/stock-bot
./venv/bin/python <<'PY'
from pathlib import Path
import os
import sys

from dotenv import load_dotenv

load_dotenv(Path("/root/stock-bot/.env"), override=True)
import requests

msg = (
    "\U0001f7e2 VANGUARD SYSTEM TEST: Comms link active. Epoch reset successful. "
    "V2 Live / V3 Shadow architecture armed for market open."
)
token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
if not token or not chat:
    print("missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID", file=sys.stderr)
    sys.exit(3)
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat, "text": msg},
    timeout=30,
)
print("telegram_ping", r.status_code, r.text[:400])
sys.exit(0 if r.ok else 1)
PY

echo "--- ML flattener dry-fire ---"
cd /root/stock-bot
PYTHONPATH=. ./venv/bin/python scripts/telemetry/alpaca_ml_flattener.py
echo "flattener_exit=$?"
