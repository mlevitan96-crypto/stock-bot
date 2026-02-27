#!/usr/bin/env python3
"""Print a single JSON object with positions count, cash, equity (no secrets). For Phase 1 audit."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
try:
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env", override=False)
except Exception:
    pass


def main() -> int:
    key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        print(json.dumps({"error": "keys_missing"}), flush=True)
        return 1
    try:
        from alpaca_trade_api import REST
        api = REST(key, secret, base_url=base)
        acc = api.get_account()
        pos = api.list_positions()
        out = {
            "positions_count": len(pos),
            "cash": getattr(acc, "cash", None),
            "equity": getattr(acc, "equity", None),
            "status": getattr(acc, "status", None),
        }
        print(json.dumps(out), flush=True)
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
