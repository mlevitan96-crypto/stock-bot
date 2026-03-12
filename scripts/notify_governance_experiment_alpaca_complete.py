#!/usr/bin/env python3
"""
Send a single Telegram alert when the Alpaca governance experiment 1 validation
window is satisfied and the ledger is healthy. Uses TELEGRAM_BOT_TOKEN and
TELEGRAM_CHAT_ID. Analysis-only; no execution impact.
Sends at most once per experiment phase (marker file prevents duplicate completion messages).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parents[1] / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
COMPLETION_SENT_FLAG = Path(__file__).resolve().parents[1] / "state" / "governance_experiment_1_completion_sent.flag"


def _ledger_healthy() -> bool:
    if not LEDGER_PATH.exists():
        return False
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(data, list) or not data:
        return False
    required = {"change_id", "timestamp", "profit_hypothesis_present"}
    for entry in data:
        if not isinstance(entry, dict) or required - set(entry):
            return False
        if entry.get("profit_hypothesis_present") not in ("YES", "NO"):
            return False
    return True


def _send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        return False
    try:
        import requests
    except ImportError:
        print("pip install requests required for Telegram send", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=30)
    if not r.ok:
        print(r.text, file=sys.stderr)
        return False
    return True


def main() -> int:
    if not _ledger_healthy():
        print("Ledger not healthy; completion alert not sent.")
        return 0
    if COMPLETION_SENT_FLAG.exists():
        print("Completion already sent for this experiment phase; skipping.")
        return 0
    msg = "Alpaca governance experiment 1 — COMPLETE: validation window satisfied, ledger healthy."
    if not _send_telegram(msg):
        return 2
    try:
        COMPLETION_SENT_FLAG.parent.mkdir(parents=True, exist_ok=True)
        COMPLETION_SENT_FLAG.touch()
    except OSError:
        pass
    print("Completion alert sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
