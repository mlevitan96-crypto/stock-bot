#!/usr/bin/env python3
"""Send CSA Fast-Lane verdict Telegram. Run on droplet with .alpaca_env sourced."""
import os
import sys
try:
    import requests
except ImportError:
    sys.exit(1)
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")
if not token or not chat:
    print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set", file=sys.stderr)
    sys.exit(1)
msg = """CSA REVIEW COMPLETE:
Alpaca Fast-Lane 25-trade review.
Verdict: NO PROMOTION at this time.
See CSA_REVIEW_ALPACA_FASTLANE_25_20260317_1525.md"""
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat, "text": msg},
    timeout=30,
)
print("Telegram sent" if r.ok else r.text)
sys.exit(0 if r.ok else 1)
