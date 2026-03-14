#!/usr/bin/env python3
"""
Alpaca fast-lane supervisor: 500-trade board summary.
Reads fast_lane_ledger.json; when total_trades >= 500, sends board-grade Telegram
summary and optionally resets epoch. Use --force to send board summary regardless of count.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = REPO / "state" / "fast_lane_experiment"
LEDGER_PATH = STATE_DIR / "fast_lane_ledger.json"
SUPERVISOR_THRESHOLD = 500


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
    parser = argparse.ArgumentParser(description="Fast-lane supervisor: 500-trade board summary.")
    parser.add_argument("--force", action="store_true", help="Send board summary even if total_trades < 500")
    parser.add_argument("--reset-epoch", action="store_true", help="After sending, reset ledger and state (optional)")
    args = parser.parse_args()

    ledger = _load_ledger()
    total_trades = sum(entry.get("trade_count", 0) for entry in ledger)
    cumulative_pnl = sum(entry.get("pnl_usd", 0) for entry in ledger)

    if total_trades < SUPERVISOR_THRESHOLD and not args.force:
        print(f"Total trades {total_trades} < {SUPERVISOR_THRESHOLD}; run with --force to send anyway.")
        return 0

    # Build top candidates by cycle wins
    best_by_candidate = {}
    for entry in ledger:
        cid = entry.get("best_candidate_id") or "baseline"
        best_by_candidate[cid] = best_by_candidate.get(cid, 0) + 1
    top_candidates = sorted(best_by_candidate.items(), key=lambda x: -x[1])[:5]

    # Notify board
    try:
        subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "notify_fast_lane_summary.py"),
                "--kind", "board",
            ],
            cwd=str(REPO),
            timeout=30,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Board notify failed: {e}", file=sys.stderr)
        return 1

    print(f"Board summary sent. Cycles={len(ledger)} trades={total_trades} cumulative_pnl=${cumulative_pnl:.2f}")
    if top_candidates:
        print("Top candidates:", ", ".join(f"{c}({n})" for c, n in top_candidates))

    if args.reset_epoch:
        STATE_PATH = STATE_DIR / "fast_lane_state.json"
        with open(LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        if STATE_PATH.exists():
            state = {}
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                pass
            state["last_processed_trade_index"] = 0
            state["total_trades_processed"] = 0
            state["last_cycle_id"] = None
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        print("Epoch reset: ledger and state cleared.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
