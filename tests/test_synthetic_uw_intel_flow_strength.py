"""Regression: synthetic UW intel must not zero flow_strength when trade_count is 0 but conviction > 0."""
from __future__ import annotations

import uw_composite_v2 as uw


def test_synthetic_intel_preserves_conviction_when_trade_count_zero():
    row = {"trade_count": 0, "conviction": 0.55, "sentiment": "BULLISH", "dark_pool": {"sentiment": "NEUTRAL"}}
    out = uw._synthetic_uw_intel_from_flow_row(row)
    assert abs(float(out["flow_strength"]) - 0.55) < 1e-9


def test_synthetic_intel_zero_when_no_conviction_and_no_trades():
    row = {"trade_count": 0, "conviction": 0.0, "sentiment": "NEUTRAL", "dark_pool": {}}
    out = uw._synthetic_uw_intel_from_flow_row(row)
    assert float(out["flow_strength"]) == 0.0


def test_synthetic_intel_uses_trade_count_path_when_positive():
    row = {"trade_count": 3, "conviction": 0.4, "sentiment": "BULLISH", "dark_pool": {}}
    out = uw._synthetic_uw_intel_from_flow_row(row)
    assert abs(float(out["flow_strength"]) - 0.4) < 1e-9
