#!/usr/bin/env python3
"""
Build blocked_counterfactuals and summary for today (run on droplet or locally).

- Reads logs/run.jsonl for blocked trade_intent.
- With --with-bars: uses data/bars_loader + real intraday bars for +5m/+15m/+30m counterfactual PnL.
- With --no-bars (default): metadata only, no bar fetch.
- Writes telemetry/YYYY-MM-DD/blocked_counterfactuals.json and computed/blocked_counterfactuals_summary.json.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _get_bars_via_loader(date_str: str):
    """Return get_bars_for_symbol(symbol, intent_ts, limit_minutes) using data.bars_loader."""
    from data.bars_loader import load_bars

    def get_bars_for_symbol(symbol: str, intent_ts, limit_minutes: int):
        if not symbol or symbol == "?":
            return None
        end = intent_ts + timedelta(minutes=limit_minutes)
        bars = load_bars(
            symbol, date_str, "1Min",
            start_ts=intent_ts, end_ts=end,
            use_cache=True, fetch_if_missing=True,
        )
        return bars if bars else None

    return get_bars_for_symbol


def main() -> int:
    ap = argparse.ArgumentParser(description="Build blocked counterfactuals for a date")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--no-bars", action="store_true", help="Skip bar fetch (metadata only)")
    ap.add_argument("--with-bars", action="store_true", help="Use real intraday bars via data/bars_loader")
    args = ap.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    use_bars = args.with_bars and not args.no_bars
    get_bars = _get_bars_via_loader(date_str) if use_bars else None

    from telemetry.blocked_counterfactuals import run as blocked_run

    raw_path, summary_path = blocked_run(date_str, get_bars=get_bars)
    print(f"[OK] Wrote {raw_path}")
    print(f"[OK] Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
