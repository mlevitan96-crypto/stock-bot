#!/usr/bin/env python3
"""Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set (for Alpaca)."""
import os
import sys

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat = os.getenv("TELEGRAM_CHAT_ID")

if not token:
    print("TOKEN: MISSING", file=sys.stderr)
    sys.exit(1)
if not chat:
    print("CHAT: MISSING", file=sys.stderr)
    sys.exit(1)

print("TOKEN: SET")
print("CHAT: SET")
sys.exit(0)
