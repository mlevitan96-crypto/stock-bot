#!/usr/bin/env python3
"""
Send Alpaca fast-lane shadow summary to Telegram.
Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (same as Alpaca governance).
Supports: --kind cycle | board.
Analysis-only; no execution impact.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO / "state" / "fast_lane_experiment" / "fast_lane_ledger.json"


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


def _load_ledger() -> list:
    if not LEDGER_PATH.exists():
        return []
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Notify fast-lane summary (cycle or board).")
    parser.add_argument("--kind", choices=("cycle", "board"), required=True, help="cycle = last cycle; board = 500-trade summary")
    parser.add_argument("--cycle-id", type=str, default=None, help="For kind=cycle: cycle_id to report")
    parser.add_argument("--pnl-usd", type=float, default=None, help="For kind=cycle: cycle PnL USD")
    parser.add_argument("--best-candidate-id", type=str, default=None, help="Legacy: best candidate id")
    parser.add_argument("--promoted", type=str, default=None, help="Promoted angle (dimension:value) for this cycle")
    parser.add_argument("--runner-ups", type=str, default="", help="Optional runner-up angles for cycle")
    parser.add_argument("--notes", type=str, default="", help="Optional CSA notes for cycle")
    args = parser.parse_args()

    if args.kind == "cycle":
        msg_parts = ["🔬 Alpaca Fast-Lane (25-trade promotion)"]
        if args.cycle_id:
            msg_parts.append(f"Cycle: {args.cycle_id}")
        if args.pnl_usd is not None:
            sign = "+" if args.pnl_usd >= 0 else ""
            msg_parts.append(f"Window PnL: {sign}${args.pnl_usd:.2f}")
        promoted = args.promoted or args.best_candidate_id
        if promoted:
            msg_parts.append(f"Promoted: {promoted}")
        if args.runner_ups:
            msg_parts.append(f"Runner-ups: {args.runner_ups}")
        if args.notes:
            msg_parts.append(args.notes)
        text = "\n".join(msg_parts)
        ok = _send_telegram(text)
        return 0 if ok else 1

    # kind == board
    ledger = _load_ledger()
    total_trades = sum(entry.get("trade_count", 0) for entry in ledger)
    cumulative_pnl = sum(entry.get("pnl_usd", 0) for entry in ledger)
    best_by_cycle = {}
    for entry in ledger:
        cid = entry.get("promoted_angle") or entry.get("best_candidate_id") or "baseline"
        best_by_cycle[cid] = best_by_cycle.get(cid, 0) + 1
    top_candidates = sorted(best_by_cycle.items(), key=lambda x: -x[1])[:8]

    msg_parts = [
        "📊 Alpaca Fast-Lane — Board Summary (500-trade supervisor)",
        f"Total cycles: {len(ledger)}",
        f"Total trades: {total_trades}",
        f"Cumulative PnL: ${cumulative_pnl:.2f}",
        "Top promoted angles (by cycle wins): " + ", ".join(f"{c}({n})" for c, n in top_candidates) or "—",
        "Shadow only; no live impact.",
    ]
    text = "\n".join(msg_parts)
    ok = _send_telegram(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
