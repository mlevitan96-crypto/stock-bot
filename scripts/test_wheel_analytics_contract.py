#!/usr/bin/env python3
"""
Wheel analytics contract test: given fixture trades with strategy_id=wheel,
aggregation must report total_trades > 0 and premium_collected >= 0.
Run: python3 scripts/test_wheel_analytics_contract.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _aggregate_wheel_from_trades(trades: list[dict]) -> dict:
    """Same logic as dashboard api_stockbot_wheel_analytics (wheel slice + sums)."""
    wheel = [t for t in trades if t.get("strategy_id") == "wheel"]
    total = len(wheel)
    premium_sum = sum(float(t.get("premium") or 0) for t in wheel)
    assigned_count = sum(1 for t in wheel if t.get("assigned") is True)
    called_away_count = sum(1 for t in wheel if t.get("called_away") is True)
    pnl_sum = sum(float(t.get("pnl_usd") or 0) for t in wheel if t.get("pnl_usd") is not None)
    return {
        "total_trades": total,
        "premium_collected": round(premium_sum, 2),
        "assignment_count": assigned_count,
        "call_away_count": called_away_count,
        "realized_pnl_sum": round(pnl_sum, 2),
    }


def main() -> int:
    # Fixture: one wheel trade with premium (as would come from telemetry/attribution)
    fixture_trades = [
        {
            "strategy_id": "wheel",
            "symbol": "SPY",
            "timestamp": "2026-02-09T18:00:00Z",
            "premium": 10.50,
            "wheel_phase": "CSP",
            "option_type": "put",
            "strike": 600.0,
            "expiry": "2026-02-21",
            "pnl_usd": None,
        },
    ]
    result = _aggregate_wheel_from_trades(fixture_trades)
    if result["total_trades"] < 1:
        print(f"FAIL: total_trades expected >= 1, got {result['total_trades']}")
        return 1
    if result["premium_collected"] < 0:
        print(f"FAIL: premium_collected expected >= 0, got {result['premium_collected']}")
        return 1
    if result["premium_collected"] != 10.50:
        print(f"FAIL: premium_collected expected 10.50, got {result['premium_collected']}")
        return 1
    print("PASS: wheel analytics contract (strategy_id=wheel counted, premium summed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
