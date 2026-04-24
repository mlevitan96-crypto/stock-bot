#!/usr/bin/env python3
"""Send a one-off test message via Telegram using TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from env."""
import os
import sys

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        return 1
    try:
        import requests
    except ImportError:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat, "text": "Test from stock-bot droplet. Telegram is live."}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            print(r.read().decode())
        return 0
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": "Test from stock-bot droplet. Telegram is live."},
        timeout=15,
    )
    if r.ok:
        print("Sent. Check your Telegram.")
        return 0
    print(r.text, file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())
