"""
Dashboard data loaders. Fast-lane ledger is used by dashboard.py /api/stockbot/fast_lane_ledger.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_dashboard_root() -> Path:
    """Repo root (dashboard.py lives there)."""
    return Path(__file__).resolve().parents[1]


def load_fast_lane_ledger() -> dict[str, Any]:
    """
    Load Alpaca fast-lane shadow ledger (25-trade cycles).
    Returns: {"cycles": list, "total_trades": int, "cumulative_pnl": float, "error": str|None}
    """
    root = get_dashboard_root()
    ledger_path = root / "state" / "fast_lane_experiment" / "fast_lane_ledger.json"
    out = {"cycles": [], "total_trades": 0, "cumulative_pnl": 0.0, "error": None}
    if not ledger_path.exists():
        return out
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8", errors="replace"))
        cycles = data if isinstance(data, list) else []
        out["cycles"] = cycles
        out["total_trades"] = sum(c.get("trade_count", 0) for c in cycles)
        out["cumulative_pnl"] = sum(c.get("pnl_usd", 0) for c in cycles)
    except Exception as e:
        out["error"] = str(e)
    return out
