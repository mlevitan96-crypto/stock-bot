#!/usr/bin/env python3
"""
Send a single Telegram alert when the Alpaca governance experiment 1 validation
window is satisfied and the ledger is healthy. Uses TELEGRAM_BOT_TOKEN and
TELEGRAM_CHAT_ID. Analysis-only; no execution impact.
Accepts --sessions-elapsed N and --trades-count N; completion requires
(sessions-elapsed >= 7) OR (trades-count >= 500) and ledger health PASS.
Sends at most once per experiment phase (marker file prevents duplicate completion messages).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"
COMPLETION_SENT_FLAG = REPO / "state" / "governance_experiment_1_completion_sent.flag"
DECISION_SPINE_REPORT = "reports/QUANTIFIED_DECISION_SPINE_ALPACA_EXPERIMENT_1_2026-03-12.md"


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
    parser = argparse.ArgumentParser(description="Notify Alpaca Experiment #1 completion (once per phase).")
    parser.add_argument("--sessions-elapsed", type=int, default=None, help="Trading sessions elapsed in window")
    parser.add_argument("--trades-count", type=int, default=None, help="Closed trades count in window")
    args = parser.parse_args()
    sessions = args.sessions_elapsed if args.sessions_elapsed is not None else 0
    trades = args.trades_count if args.trades_count is not None else 0
    window_satisfied = (sessions >= 7) or (trades >= 500)

    if not _ledger_healthy():
        print("Ledger not healthy; completion alert not sent.")
        return 0
    if not window_satisfied:
        print(f"Window not satisfied (sessions={sessions}, trades={trades}); need 7 sessions or 500 trades.")
        return 0
    if COMPLETION_SENT_FLAG.exists():
        print("Completion already sent for this experiment phase; skipping.")
        return 0
    msg = (
        "Alpaca Experiment #1 Complete.\n"
        f"Window satisfied: {sessions} sessions / {trades} trades.\n"
        "Ledger health PASS.\n"
        f"Report: {DECISION_SPINE_REPORT}"
    )
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
