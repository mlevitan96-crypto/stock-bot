#!/usr/bin/env python3
"""
Block 3G: Tests for replay-time signal injection.
- compute_signals_for_timestamp with synthetic bars
- Safe defaults when no bars / invalid input
- Attribution structure after injection
"""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


def _mock_bars(count: int = 50, base_price: float = 100.0) -> list:
    """Synthetic bars with t and c for price_series."""
    bars = []
    for i in range(count):
        ts = datetime(2026, 1, 15, 13, 30, 0, tzinfo=timezone.utc)
        from datetime import timedelta
        ts = ts + __import__("datetime").timedelta(minutes=i)
        bars.append({
            "t": ts.isoformat().replace("+00:00", "Z"),
            "c": base_price + i * 0.1,
            "o": base_price, "h": base_price + 1, "l": base_price - 0.5, "v": 1000,
        })
    return bars


class TestReplaySignalInjection(unittest.TestCase):
    def test_compute_signals_for_timestamp_with_mock_bars(self):
        from scripts.replay_signal_injection import (
            compute_signals_for_timestamp,
            REPLAY_SIGNAL_KEYS,
            REPLAY_EXTRA_KEYS,
        )
        event_ts = datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        bars = _mock_bars(50)

        def load_bars_fn(symbol: str, date_str: str, end_ts=None):
            if date_str == "2026-01-15":
                return bars
            return []

        out = compute_signals_for_timestamp("AAPL", event_ts.timestamp(), load_bars_fn=load_bars_fn)
        for k in REPLAY_SIGNAL_KEYS:
            self.assertIn(k, out, msg=f"missing key {k}")
            self.assertIsInstance(out[k], (int, float), msg=f"{k} not numeric")
        for k in REPLAY_EXTRA_KEYS:
            self.assertIn(k, out)
        self.assertIn("regime_label", out)
        self.assertIn("sector_momentum", out)

    def test_compute_signals_for_timestamp_no_bars(self):
        from scripts.replay_signal_injection import compute_signals_for_timestamp, REPLAY_SIGNAL_KEYS

        def empty_bars(symbol, date_str, end_ts=None):
            return []

        event_ts = datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        out = compute_signals_for_timestamp("AAPL", event_ts.timestamp(), load_bars_fn=empty_bars)
        for k in REPLAY_SIGNAL_KEYS:
            self.assertEqual(out.get(k), 0.0, msg=f"{k} should be 0.0 when no bars")
        self.assertIsNone(out.get("regime_label"))

    def test_compute_signals_for_timestamp_invalid_input(self):
        from scripts.replay_signal_injection import compute_signals_for_timestamp, REPLAY_SIGNAL_KEYS

        out = compute_signals_for_timestamp("", None)
        for k in REPLAY_SIGNAL_KEYS:
            self.assertEqual(out.get(k), 0.0)
        out2 = compute_signals_for_timestamp("?", 0)
        for k in REPLAY_SIGNAL_KEYS:
            self.assertEqual(out2.get(k), 0.0)

    def test_injected_signals_match_raw_engine_output(self):
        """Injected signals from synthetic price series match raw_signal_engine.build_raw_signals (same keys, sane range)."""
        from src.signals.raw_signal_engine import build_raw_signals
        from scripts.replay_signal_injection import compute_signals_for_timestamp, REPLAY_SIGNAL_KEYS

        price_series = [100.0 + i * 0.2 for i in range(50)]
        expected = build_raw_signals(price_series, "", 0.0)
        bars = [{"t": f"2026-01-15T13:{30+i:02d}:00Z", "c": p} for i, p in enumerate(price_series)]
        event_ts = datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

        def load_bars_fn(symbol, date_str, end_ts=None):
            if date_str == "2026-01-15":
                return bars
            return []

        out = compute_signals_for_timestamp("AAPL", event_ts.timestamp(), load_bars_fn=load_bars_fn)
        for k in REPLAY_SIGNAL_KEYS:
            self.assertIn(k, expected)
            self.assertIn(k, out)
            ev = float(expected[k])
            ov = float(out[k])
            self.assertGreaterEqual(ov, -1.0, msg=k)
            self.assertLessEqual(ov, 1.0, msg=k)
            # Same ballpark (allow bar/ordering float variance)
            self.assertAlmostEqual(ev, ov, delta=0.15, msg=k)


class TestBacktestReplayWithInjection(unittest.TestCase):
    """Backward compat: backtest script runs with injection (no crash)."""

    def test_backtest_script_imports_injection(self):
        """Backtest script imports compute_signals_for_timestamp (or None on failure)."""
        import sys
        root = Path(__file__).resolve().parents[2]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from scripts.run_30d_backtest_droplet import run
        self.assertTrue(callable(run))


class TestAnalysisReadsInjectedSignals(unittest.TestCase):
    """Signal edge analysis reads injected signals from trade context."""

    def test_analysis_buckets_injected_signals(self):
        from src.analysis.signal_edge_analysis import run_analysis, _extract_signals_from_trade
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "backtest_trades.jsonl"
            rows = [
                {"symbol": "A", "pnl_usd": 5.0, "entry_score": 0.5, "context": {
                    "trend_signal": 0.5, "momentum_signal": 0.3, "volatility_signal": 0.2,
                    "regime_signal": 0.0, "sector_signal": -0.1, "reversal_signal": 0.1,
                    "breakout_signal": 0.4, "mean_reversion_signal": -0.2, "regime_label": "MIXED",
                }},
                {"symbol": "B", "pnl_usd": -3.0, "entry_score": 0.2, "context": {
                    "trend_signal": -0.4, "momentum_signal": -0.2, "volatility_signal": 0.5,
                    "regime_signal": 0.0, "sector_signal": 0.0, "reversal_signal": -0.1,
                    "breakout_signal": -0.3, "mean_reversion_signal": 0.2, "regime_label": "MIXED",
                }},
            ]
            with path.open("w") as f:
                for r in rows:
                    f.write(json.dumps(r, default=str) + "\n")
            (Path(td) / "backtest_exits.jsonl").write_text("")
            (Path(td) / "backtest_blocks.jsonl").write_text("")
            data = run_analysis(Path(td))
        self.assertEqual(data["trades_count"], 2)
        sigs = _extract_signals_from_trade({"context": rows[0]["context"]})
        self.assertEqual(sigs.get("trend_signal"), 0.5)
        self.assertEqual(sigs.get("breakout_signal"), 0.4)
        self.assertIn("positive", str(data) or "") or self.assertIn("negative", str(data) or "") or self.assertIn("near_zero", str(data) or "")
