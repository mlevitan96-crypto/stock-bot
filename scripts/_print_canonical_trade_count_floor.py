#!/usr/bin/env python3
"""One-off: print canonical unique closed trades with STRICT_EPOCH_START floor (SRE / ops)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.governance.canonical_trade_count import compute_canonical_trade_count
from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

if __name__ == "__main__":
    o = compute_canonical_trade_count(ROOT, floor_epoch=float(STRICT_EPOCH_START))
    print("STRICT_EPOCH_START", STRICT_EPOCH_START)
    print("total_trades_post_era", o.get("total_trades_post_era"))
