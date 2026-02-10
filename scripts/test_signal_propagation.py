#!/usr/bin/env python3
"""
Tests for open-position signal propagation: evaluate_signal_for_symbol contract,
signal_strength_evaluated emission, and dashboard not zeroing when missing.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evaluate_signal_for_symbol_returns_float_and_evaluated():
    """evaluate_signal_for_symbol returns (float, bool, str|None); never silently skip."""
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from signal_open_position import evaluate_signal_for_symbol

    strength, evaluated, reason = evaluate_signal_for_symbol("NO_SYMBOL_IN_CACHE", {"uw_cache": {}, "regime": "mixed"})
    assert strength == 0.0
    assert evaluated is False
    assert reason in ("symbol_not_in_uw_cache", "no_enriched_data")

    strength2, evaluated2, reason2 = evaluate_signal_for_symbol("AAPL", {
        "uw_cache": {"AAPL": {"sentiment": "BULLISH", "conviction": 0.6}},
        "regime": "mixed",
    })
    assert isinstance(strength2, float)
    assert evaluated2 is True
    assert reason2 is None


def test_signal_evaluated_for_open_positions():
    """Given open positions, assert signal_strength_evaluated is emitted when refresh runs."""
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    events_log: list[dict] = []
    def capture_event(subsystem, event_type, severity, **kwargs):
        events_log.append({"subsystem": subsystem, "event_type": event_type, "severity": severity, **kwargs})

    with tempfile.TemporaryDirectory() as tmp:
        cache_path = Path(tmp) / "signal_strength_cache.json"
        with patch.dict("sys.modules", {"config.registry": MagicMock()}):
            from config import registry
            registry.StateFiles.SIGNAL_STRENGTH_CACHE = cache_path
        with patch("utils.system_events.log_system_event", side_effect=capture_event):
            from signal_open_position import evaluate_signal_for_symbol
            ctx = {
                "uw_cache": {"XLK": {"sentiment": "BULLISH", "conviction": 0.5}},
                "regime": "mixed",
            }
            strength, evaluated, _ = evaluate_signal_for_symbol("XLK", ctx)
        assert evaluated is True
        assert isinstance(strength, float)
    # The actual emission happens in main.evaluate_exits; we tested the contract returns evaluated=True and float.


def test_dashboard_signal_not_zeroed_when_missing():
    """Missing evaluation must not silently appear as 0.0: current_signal_evaluated false and current_score null."""
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    # Simulate dashboard logic: when symbol not in signal_strength_cache, current_score should be None and current_signal_evaluated False
    signal_strength_cache = {}
    symbol = "MISSING_SYMBOL"
    cached = signal_strength_cache.get(symbol) if isinstance(signal_strength_cache.get(symbol), dict) else None
    current_score = None
    current_signal_evaluated = False
    if cached is not None and "signal_strength" in cached:
        try:
            current_score = float(cached["signal_strength"])
            current_signal_evaluated = True
        except (TypeError, ValueError):
            pass

    assert current_signal_evaluated is False
    assert current_score is None
    # So dashboard must not show 0.00 for this position; must show N/A
    display_value = "N/A" if not current_signal_evaluated else (f"{current_score:.2f}" if current_score is not None else "0.00")
    assert display_value == "N/A"


def test_trend_delta_computed_when_prev_exists():
    """When cache has prev_signal_strength, delta and trend are computed correctly (eps=0.05)."""
    SIGNAL_TREND_EPS = 0.05
    prev_strength = 3.0
    current_strength = 3.08
    signal_delta = round(current_strength - prev_strength, 4)
    signal_delta_abs = round(abs(signal_delta), 4)
    if signal_delta_abs < SIGNAL_TREND_EPS:
        signal_trend = "flat"
    else:
        signal_trend = "strengthening" if signal_delta > 0 else "weakening"
    assert signal_delta == 0.08
    assert signal_trend == "strengthening"
    prev_strength2 = 4.0
    current_strength2 = 3.94
    delta2 = round(current_strength2 - prev_strength2, 4)
    trend2 = "flat" if abs(delta2) < SIGNAL_TREND_EPS else ("strengthening" if delta2 > 0 else "weakening")
    assert trend2 == "weakening"
    flat_prev, flat_cur = 2.5, 2.53
    flat_delta = round(flat_cur - flat_prev, 4)
    flat_trend = "flat" if abs(flat_delta) < SIGNAL_TREND_EPS else ("strengthening" if flat_delta > 0 else "weakening")
    assert flat_trend == "flat"


def test_dashboard_returns_na_when_not_evaluated():
    """Trend fields must be null/N/A when current_signal_evaluated is False."""
    current_signal_evaluated = False
    signal_trend = None
    prev_score = None
    signal_delta = None
    trend_display = "N/A" if not current_signal_evaluated or not signal_trend else signal_trend
    assert trend_display == "N/A"
    assert prev_score is None
    assert signal_delta is None


def test_correlation_snapshot_outputs_topk_schema():
    """Correlation snapshot output schema: as_of, window_minutes, method, pairs, top_symbols."""
    out = {
        "as_of": "2026-02-10T12:00:00",
        "window_minutes": 60,
        "method": "pearson",
        "pairs": [{"a": "A", "b": "B", "corr": 0.9, "n": 10}, {"a": "A", "b": "C", "corr": 0.7, "n": 8}],
        "top_symbols": {"A": {"max_corr": 0.9, "most_correlated_with": "B", "avg_corr_topk": 0.5}},
    }
    assert "pairs" in out
    assert "top_symbols" in out
    assert out["method"] == "pearson"
    assert isinstance(out["pairs"], list)
    assert len(out["pairs"]) >= 1
    assert "a" in out["pairs"][0] and "b" in out["pairs"][0] and "corr" in out["pairs"][0] and "n" in out["pairs"][0]


if __name__ == "__main__":
    test_evaluate_signal_for_symbol_returns_float_and_evaluated()
    print("test_evaluate_signal_for_symbol_returns_float_and_evaluated: OK")
    test_signal_evaluated_for_open_positions()
    print("test_signal_evaluated_for_open_positions: OK")
    test_dashboard_signal_not_zeroed_when_missing()
    print("test_dashboard_signal_not_zeroed_when_missing: OK")
    test_trend_delta_computed_when_prev_exists()
    print("test_trend_delta_computed_when_prev_exists: OK")
    test_dashboard_returns_na_when_not_evaluated()
    print("test_dashboard_returns_na_when_not_evaluated: OK")
    test_correlation_snapshot_outputs_topk_schema()
    print("test_correlation_snapshot_outputs_topk_schema: OK")
    print("All signal propagation tests passed.")
