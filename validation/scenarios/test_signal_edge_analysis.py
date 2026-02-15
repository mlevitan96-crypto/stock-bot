#!/usr/bin/env python3
"""
Lightweight tests for signal edge analysis.
Uses synthetic trades data.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestSignalEdgeAnalysisLoad(unittest.TestCase):
    def test_load_synthetic_trades(self):
        from src.analysis.signal_edge_analysis import load_trades, _extract_signals_from_trade
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "backtest_trades.jsonl"
            rows = [
                {"symbol": "AAPL", "pnl_usd": 10.0, "entry_score": 0.5, "context": {"market_regime": "BULL", "trend_signal": 0.3}},
                {"symbol": "MSFT", "pnl_usd": -5.0, "entry_score": -0.2, "context": {"market_regime": "BEAR", "trend_signal": -0.4}},
            ]
            with path.open("w") as f:
                for r in rows:
                    f.write(json.dumps(r, default=str) + "\n")
            backtest_dir = Path(td)
            trades = load_trades(backtest_dir)
        self.assertEqual(len(trades), 2)
        sigs = _extract_signals_from_trade(trades[0])
        self.assertEqual(sigs.get("trend_signal"), 0.3)

    def test_bucketing_works(self):
        from src.analysis.signal_edge_analysis import bucket_metrics
        trades = [
            {"pnl_usd": 10.0, "context": {}},
            {"pnl_usd": -5.0, "context": {}},
            {"pnl_usd": 0.0, "context": {}},
        ]
        def get_val(t):
            return t.get("entry_score")  # None for all
        result = bucket_metrics(trades, "entry_score", get_val)
        self.assertIn("missing", result)
        self.assertEqual(result["missing"]["count"], 3)

    def test_analysis_runs_without_crashing(self):
        from src.analysis.signal_edge_analysis import run_analysis, render_markdown_report
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "backtest_trades.jsonl"
            rows = [
                {"symbol": "A", "pnl_usd": 1.0, "entry_score": 0.5, "context": {"market_regime": "BULL"}},
                {"symbol": "B", "pnl_usd": -1.0, "entry_score": -0.3, "context": {"market_regime": "BEAR"}},
            ]
            with path.open("w") as f:
                for r in rows:
                    f.write(json.dumps(r, default=str) + "\n")
            (Path(td) / "backtest_exits.jsonl").write_text("")
            (Path(td) / "backtest_blocks.jsonl").write_text("")
            data = run_analysis(Path(td))
        self.assertEqual(data["trades_count"], 2)
        report = render_markdown_report(data, Path(td))
        self.assertIn("Signal Edge Analysis", report)
