#!/usr/bin/env python3
"""
Reset state/peak_equity.json to current Alpaca account equity (drawdown baseline repair).

Usage (from repo root, with .env loaded):
  python3 scripts/reset_peak_equity_to_broker.py --dry-run
  python3 scripts/reset_peak_equity_to_broker.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Print only; do not write")
    p.add_argument("--apply", action="store_true", help="Write peak_equity.json")
    args = p.parse_args()
    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 2

    import alpaca_trade_api as tradeapi  # type: ignore

    from main import Config

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    acct = api.get_account()
    eq = float(getattr(acct, "equity", 0) or 0)
    out_path = REPO / "state" / "peak_equity.json"
    prev = None
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            prev = "unreadable"

    payload = {
        "peak_equity": eq,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "source": "reset_peak_equity_to_broker",
        "previous_file": prev,
    }
    print(json.dumps({"current_equity": eq, "would_write": payload}, indent=2))
    if args.dry_run:
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
