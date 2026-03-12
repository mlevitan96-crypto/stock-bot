#!/usr/bin/env python3
"""
Send stdin as a Telegram message. Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
Used by daily governance update (output-only; no trading or promotion).
"""
from __future__ import annotations

import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests required for Telegram send", file=sys.stderr)
    sys.exit(2)

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        sys.exit(1)
    text = sys.stdin.read()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=30)
    if not r.ok:
        print(r.text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
