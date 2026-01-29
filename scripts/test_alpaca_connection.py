#!/usr/bin/env python3
"""
Test Alpaca API connection (keys + connectivity).
Loads .env from repo root, then tries to get clock and one bar for AAPL.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from dotenv import load_dotenv
    env_path = REPO / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except Exception:
    pass


def main() -> int:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    if not key or not secret:
        print("FAIL: Alpaca API keys not found in environment.", file=sys.stderr)
        print("Set ALPACA_API_KEY and ALPACA_API_SECRET (or ALPACA_KEY / ALPACA_SECRET), or add them to .env in the repo root.", file=sys.stderr)
        return 1

    print("Keys found (key prefix: {}...). Connecting to {} ...".format(key[:8] if len(key) > 8 else key, base))

    try:
        from alpaca_trade_api import REST
        api = REST(key, secret, base_url=base)
    except Exception as e:
        print("FAIL: Could not create Alpaca REST client: {}".format(e), file=sys.stderr)
        return 1

    try:
        clock = api.get_clock()
        print("OK: get_clock() -> is_open={}".format(getattr(clock, "is_open", clock)))
    except Exception as e:
        print("FAIL: get_clock() failed: {}".format(e), file=sys.stderr)
        return 1

    try:
        from datetime import datetime, timezone, timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=1)
        bars = api.get_bars("AAPL", "1Min", start=start.isoformat().replace("+00:00", "Z"), end=end.isoformat().replace("+00:00", "Z"), limit=5)
        df = getattr(bars, "df", None)
        count = len(df) if df is not None else 0
        print("OK: get_bars(AAPL, 1Min) -> {} bars".format(count))
    except Exception as e:
        print("WARN: get_bars(AAPL) failed (data API may differ): {}".format(e), file=sys.stderr)
        print("Connection to Alpaca is working (clock succeeded). Bar data may require a data plan.", file=sys.stderr)

    print("Alpaca connection test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
