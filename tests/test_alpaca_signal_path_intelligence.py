"""Unit tests for read-only Alpaca Signal Path Intelligence (SPI)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.alpaca_signal_path_intelligence import (
    aggregate_spi,
    classify_path_archetype,
    compute_trade_spi_row,
    dominant_attribution_signal,
    path_mae_mfe_pct,
    summarize_numeric,
    time_to_fractional_move_minutes,
    _iter_hold_bars,
)


def test_dominant_attribution_signal():
    assert dominant_attribution_signal({}) == "attribution_unknown"
    assert dominant_attribution_signal({"exit_contributions": {"a": 0.2, "b": -0.9}}) == "b"
    assert dominant_attribution_signal({"v2_exit_components": {"x": 1.0}}) == "x"


def test_time_to_fractional_move_long():
    entry = datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)
    exit_ = datetime(2026, 1, 1, 15, 0, tzinfo=timezone.utc)
    bars = [
        {"t": "2026-01-01T14:01:00+00:00", "h": 100.3, "l": 99.0, "c": 100.1},
        {"t": "2026-01-01T14:05:00+00:00", "h": 101.2, "l": 100.0, "c": 101.0},
    ]
    hb = _iter_hold_bars(bars, entry, exit_)
    t = time_to_fractional_move_minutes(hb, 100.0, entry, exit_, 0.01, long_side=True)
    assert t is not None
    assert 4.9 <= t <= 5.1


def test_path_mae_mfe_long():
    entry = datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)
    exit_ = datetime(2026, 1, 1, 14, 10, tzinfo=timezone.utc)
    bars = [
        {"t": "2026-01-01T14:01:00+00:00", "h": 102.0, "l": 98.0, "c": 100.0},
    ]
    hb = _iter_hold_bars(bars, entry, exit_)
    mae, mfe = path_mae_mfe_pct(hb, 100.0, entry, exit_, long_side=True)
    assert mae == pytest.approx(2.0, rel=1e-3)
    assert mfe == pytest.approx(2.0, rel=1e-3)


def test_classify_archetype_grind():
    a = classify_path_archetype(0.1, 0.1, 0.05, None, 30.0)
    assert a == "grind_flat"


def test_summarize_numeric_empty():
    assert summarize_numeric([])["n"] == 0


def test_aggregate_spi_groups():
    rows = [
        {
            "trade_id": "a",
            "symbol": "AAA",
            "signal_attribution_bucket": "sig1",
            "hold_minutes": 10.0,
            "mae_pct_hold": 1.0,
            "vol_ratio_path_vs_baseline": 1.2,
            "time_to_profit_frac_minutes": {
                "to_plus_0_5pct_min": 2.0,
                "to_plus_1pct_min": None,
                "to_plus_2pct_min": None,
            },
            "path_archetype": "grind_flat",
        },
        {
            "trade_id": "b",
            "symbol": "BBB",
            "signal_attribution_bucket": "sig1",
            "hold_minutes": 20.0,
            "mae_pct_hold": 3.0,
            "vol_ratio_path_vs_baseline": 0.8,
            "time_to_profit_frac_minutes": {
                "to_plus_0_5pct_min": None,
                "to_plus_1pct_min": None,
                "to_plus_2pct_min": None,
            },
            "path_archetype": "immediate_rejection",
        },
    ]
    agg = aggregate_spi(rows)
    assert "sig1" in agg["per_signal"]
    assert agg["per_signal"]["sig1"]["trade_count"] == 2
    assert len(agg["top_anomalies_descriptive"]) >= 1


def test_compute_trade_spi_row_fixture_exit(tmp_path: Path, monkeypatch):
    """With no bars cache, row degrades to snapshot-only path."""
    exit_row = {
        "trade_id": "open_X_2026-03-26T14:00:00+00:00",
        "symbol": "X",
        "side": "long",
        "entry_timestamp": "2026-03-26T14:00:00+00:00",
        "timestamp": "2026-03-26T15:00:00+00:00",
        "entry_price": 100.0,
        "exit_price": 101.0,
        "pnl_pct": 1.0,
        "exit_contributions": {"momentum": 0.5},
        "snapshot": {"mae_pct": 0.2, "mfe_pct": 0.4},
    }
    r = compute_trade_spi_row(exit_row, tmp_path, fetch_if_missing=False)
    assert r["signal_attribution_bucket"] == "momentum"
    assert r["path_source"] in ("attribution_snapshot_no_bars", "ohlc_bars_hold_window")
    assert r["hold_minutes"] == 60.0
