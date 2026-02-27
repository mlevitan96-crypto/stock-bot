"""
Phase 8/9 — Join logic tests for attribution_loader.

- When entry has trade_id (open_*) and exit has same trade_id, joined row does not get join_fallback.
- When join is by (symbol, entry_ts) only, row has quality_flags including "join_fallback".
- load_from_backtest_dir returns rows with quality_flags including "join_fallback".
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import (
    load_joined_closed_trades,
    load_from_backtest_dir,
)


class TestAttributionLoaderJoin(unittest.TestCase):
    """Join logic: trade_id primary vs fallback quality_flags."""

    def test_join_by_trade_id_no_join_fallback(self):
        """When entry has open_* trade_id and exit has same trade_id, joined row has no join_fallback."""
        ts = "2026-02-18T12:00:00"
        tid = "open_abc123"
        with tempfile.TemporaryDirectory() as d:
            attr_path = Path(d) / "attribution.jsonl"
            exit_path = Path(d) / "exit_attribution.jsonl"
            attr_path.write_text(
                json.dumps({
                    "type": "attribution",
                    "symbol": "AAPL",
                    "trade_id": tid,
                    "context": {"entry_ts": ts, "entry_score": 4.0, "attribution_components": []},
                }) + "\n",
                encoding="utf-8",
            )
            exit_path.write_text(
                json.dumps({
                    "symbol": "AAPL",
                    "entry_timestamp": ts,
                    "trade_id": tid,
                    "pnl": 10.0,
                    "exit_reason_code": "flow_deterioration",
                }) + "\n",
                encoding="utf-8",
            )
            joined = load_joined_closed_trades(attr_path, exit_path)
        self.assertEqual(len(joined), 1)
        flags = joined[0].get("quality_flags") or []
        self.assertNotIn("join_fallback", flags)

    def test_join_by_symbol_entry_ts_has_join_fallback(self):
        """When exit has no trade_id (or different), join is by (symbol, entry_ts); row gets join_fallback."""
        ts = "2026-02-18T12:00:00"
        tid = "open_xyz"
        with tempfile.TemporaryDirectory() as d:
            attr_path = Path(d) / "attribution.jsonl"
            exit_path = Path(d) / "exit_attribution.jsonl"
            attr_path.write_text(
                json.dumps({
                    "type": "attribution",
                    "symbol": "AAPL",
                    "trade_id": tid,
                    "context": {"entry_ts": ts, "entry_score": 4.0, "attribution_components": []},
                }) + "\n",
                encoding="utf-8",
            )
            # Exit has no trade_id; join will be by (symbol, entry_ts) only
            exit_path.write_text(
                json.dumps({
                    "symbol": "AAPL",
                    "entry_timestamp": ts,
                    "pnl": 5.0,
                    "exit_reason_code": "signal_decay",
                }) + "\n",
                encoding="utf-8",
            )
            joined = load_joined_closed_trades(attr_path, exit_path)
        self.assertEqual(len(joined), 1)
        flags = joined[0].get("quality_flags") or []
        self.assertIn("join_fallback", flags)

    def test_load_from_backtest_dir_has_join_fallback(self):
        """Backtest outputs have no trade_id; every joined row gets join_fallback."""
        ts = "2026-02-18T12:00:00"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "backtest_trades.jsonl").write_text(
                json.dumps({
                    "symbol": "AAPL",
                    "timestamp": ts,
                    "context": {"entry_score": 4.0, "attribution_components": []},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "backtest_exits.jsonl").write_text(
                json.dumps({
                    "symbol": "AAPL",
                    "entry_timestamp": ts,
                    "pnl": 10.0,
                    "exit_reason_code": "flow_deterioration",
                }) + "\n",
                encoding="utf-8",
            )
            joined = load_from_backtest_dir(root)
        self.assertEqual(len(joined), 1)
        flags = joined[0].get("quality_flags") or []
        self.assertIn("join_fallback", flags)


if __name__ == "__main__":
    unittest.main()
