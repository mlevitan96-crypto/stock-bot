#!/usr/bin/env python3
"""
Build exit attribution and exit_quality_summary for today (run on droplet or locally).

- Reads logs/exit_attribution.jsonl and logs/attribution.jsonl.
- With --with-bars: uses data/bars_loader for MFE/MAE and left-on-table.
- Writes telemetry/YYYY-MM-DD/exit_attribution.json and computed/exit_quality_summary.json.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build exit attribution for a date")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--with-bars", action="store_true", help="Use real intraday bars for MFE/MAE via data/bars_loader")
    args = ap.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    get_bars = None
    if args.with_bars:
        from data.bars_loader import load_bars
        def _get_bars(symbol: str, d: str, start_ts, end_ts):
            return load_bars(symbol, d, "1Min", start_ts=start_ts, end_ts=end_ts, use_cache=True, fetch_if_missing=True)
        get_bars = lambda sym, d, start, end: _get_bars(sym, d, start, end)

    from telemetry.exit_attribution_enhancer import run as exit_run

    raw_path, summary_path = exit_run(date_str, get_bars=get_bars)
    print(f"[OK] Wrote {raw_path}")
    print(f"[OK] Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
