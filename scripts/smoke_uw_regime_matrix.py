#!/usr/bin/env python3
"""
Smoke: call UW REST for a tiny universe and print GEX / dark pool / sweep snapshot (schema check).

Requires ``UW_API_KEY``. Does not write ``state/uw_regime_matrix.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

from src.market_intelligence.uw_regime_matrix import fetch_uw_regime_live_snapshot


def main() -> int:
    p = argparse.ArgumentParser(description="Smoke-test UW regime snapshot fetch (prints JSON).")
    p.add_argument(
        "--tickers",
        type=str,
        default="SPY,QQQ,AAPL",
        help="Comma-separated symbols (default: SPY,QQQ,AAPL).",
    )
    args = p.parse_args()
    tickers = [x.strip().upper() for x in str(args.tickers or "").split(",") if x.strip()][:12]
    if not tickers:
        print("No tickers", file=sys.stderr)
        return 2
    snap = fetch_uw_regime_live_snapshot(tickers)
    print(json.dumps(snap, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
