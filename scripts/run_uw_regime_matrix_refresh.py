#!/usr/bin/env python3
"""
Batch refresh: pull UW GEX / dark pool / sweep snapshot and write ``state/uw_regime_matrix.json``.

**Not** for the live trading hot path — schedule via cron / premarket (Memory Bank §7.8).
"""
from __future__ import annotations

import argparse
import os
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

from src.market_intelligence.uw_regime_matrix import (
    DEFAULT_UW_REGIME_STATE_PATH,
    fetch_uw_regime_live_snapshot,
    save_uw_regime_matrix_state,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Refresh UW regime matrix JSON snapshot (REST batch job).")
    p.add_argument(
        "--tickers",
        type=str,
        default="",
        help="Comma-separated symbols (default: movers / fallback from env).",
    )
    p.add_argument(
        "--out",
        type=str,
        default="",
        help=f"Output JSON path (default: {DEFAULT_UW_REGIME_STATE_PATH}).",
    )
    args = p.parse_args()
    tickers = [x.strip().upper() for x in str(args.tickers or "").split(",") if x.strip()]
    out_path = Path(str(args.out).strip() or os.getenv("UW_REGIME_MATRIX_STATE_PATH", str(DEFAULT_UW_REGIME_STATE_PATH)))
    snap = fetch_uw_regime_live_snapshot(tickers if tickers else None)
    save_uw_regime_matrix_state(out_path, snap, source="scripts/run_uw_regime_matrix_refresh.py")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
