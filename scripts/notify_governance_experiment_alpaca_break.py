#!/usr/bin/env python3
"""
Send a single Telegram alert when the Alpaca governance experiment 1 hypothesis
ledger is invalid or stale. Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
Analysis-only; no execution impact.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parents[1] / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
STALE_DAYS = int(os.environ.get("GOVERNANCE_LEDGER_STALE_DAYS", "7"))


def _ledger_valid_and_fresh() -> tuple[bool, str]:
    if not LEDGER_PATH.exists():
        return False, "ledger missing"
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"ledger invalid or unreadable: {e}"
    if not isinstance(data, list):
        return False, "ledger root is not a list"
    required = {"change_id", "timestamp", "profit_hypothesis_present"}
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or required - set(entry):
            return False, f"entry {i} missing required keys"
        if entry.get("profit_hypothesis_present") not in ("YES", "NO"):
            return False, f"entry {i} invalid profit_hypothesis_present"
    if not data:
        return False, "ledger empty"
    last_ts = data[-1].get("timestamp") or ""
    try:
        # ISO8601
        dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False, "last entry timestamp invalid"
    if datetime.now(timezone.utc) - dt > timedelta(days=STALE_DAYS):
        return False, f"ledger stale (last entry older than {STALE_DAYS} days)"
    return True, ""


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
    ok, reason = _ledger_valid_and_fresh()
    if ok:
        print("Ledger valid and fresh; no break alert sent.")
        return 0
    msg = f"Alpaca governance experiment 1 — BREAK: {reason}"
    if _send_telegram(msg):
        print("Break alert sent.", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
