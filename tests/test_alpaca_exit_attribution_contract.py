"""
Contract tests for Alpaca exit attribution schema and emitter.
Validates canonical shape, validation rules, and that emitter produces valid JSONL.
Run: pytest tests/test_alpaca_exit_attribution_contract.py -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestExitAttributionSchema(unittest.TestCase):
    def test_exit_attribution_shape_has_required_keys(self):
        from src.telemetry.alpaca_attribution_schema import exit_attribution_shape

        shape = exit_attribution_shape()
        self.assertEqual(shape["event_type"], "alpaca_exit_attribution")
        self.assertIn("schema_version", shape)
        self.assertIn("trade_id", shape)
        self.assertIn("trade_key", shape)
        self.assertIn("symbol", shape)
        self.assertIn("timestamp", shape)
        self.assertIn("exit_components_raw", shape)
        self.assertIn("exit_weights", shape)
        self.assertIn("exit_contributions", shape)
        self.assertIn("exit_pressure_total", shape)
        self.assertIn("thresholds_used", shape)
        self.assertIn("eligible_mechanisms", shape)
        self.assertIn("winner", shape)
        self.assertIn("winner_explanation", shape)
        self.assertIn("snapshot", shape)
        self.assertIn("exit_dominant_component", shape)
        self.assertIn("exit_dominant_component_value", shape)
        self.assertIn("exit_pressure_margin_exit_now", shape)
        self.assertIn("exit_pressure_margin_exit_soon", shape)

    def test_validate_exit_attribution_accepts_valid(self):
        from src.telemetry.alpaca_attribution_schema import (
            SCHEMA_VERSION,
            validate_exit_attribution,
        )

        rec = {
            "event_type": "alpaca_exit_attribution",
            "schema_version": SCHEMA_VERSION,
            "trade_id": "open_AAPL_2026-03-14T12-00-00Z",
            "symbol": "AAPL",
            "timestamp": "2026-03-14T14:00:00+00:00",
            "exit_components_raw": {"timing_pressure": 0.2},
            "exit_weights": {},
            "exit_contributions": {},
            "exit_pressure_total": 0.5,
            "thresholds_used": {"normal": 0.8},
            "eligible_mechanisms": {"tp": False, "time_exit": True},
            "winner": "time_exit",
            "winner_explanation": "hold limit reached",
            "snapshot": {"pnl": 10.0, "mfe": 15.0, "mae": -2.0, "hold_minutes": 60},
        }
        issues = validate_exit_attribution(rec)
        self.assertEqual(issues, [])

    def test_validate_exit_attribution_rejects_wrong_event_type(self):
        from src.telemetry.alpaca_attribution_schema import (
            SCHEMA_VERSION,
            validate_exit_attribution,
        )

        rec = {
            "event_type": "alpaca_entry_attribution",
            "schema_version": SCHEMA_VERSION,
        }
        issues = validate_exit_attribution(rec)
        self.assertTrue(any("event_type" in i for i in issues))

    def test_validate_exit_attribution_requires_schema_version(self):
        from src.telemetry.alpaca_attribution_schema import validate_exit_attribution

        rec = {"event_type": "alpaca_exit_attribution"}
        issues = validate_exit_attribution(rec)
        self.assertTrue(any("schema_version" in i for i in issues))


class TestExitAttributionEmitter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.exit_log = Path(self.tmp) / "alpaca_exit_attribution.jsonl"
        self._prev = os.environ.get("ALPACA_EXIT_ATTRIBUTION_PATH")
        os.environ["ALPACA_EXIT_ATTRIBUTION_PATH"] = str(self.exit_log)

    def tearDown(self):
        if self._prev is not None:
            os.environ["ALPACA_EXIT_ATTRIBUTION_PATH"] = self._prev
        elif "ALPACA_EXIT_ATTRIBUTION_PATH" in os.environ:
            del os.environ["ALPACA_EXIT_ATTRIBUTION_PATH"]

    def test_emit_exit_attribution_writes_valid_jsonl(self):
        from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution
        from src.telemetry.alpaca_attribution_schema import validate_exit_attribution
        from src.telemetry.alpaca_trade_key import build_trade_key

        _iso = "2026-03-14T12:00:00+00:00"
        _tk = build_trade_key("TSLA", "LONG", _iso)
        emit_exit_attribution(
            trade_id="open_TSLA_2026-03-14T12-00-00Z",
            symbol="TSLA",
            winner="time_exit",
            winner_explanation="hold_minutes reached",
            trade_key=_tk,
            canonical_trade_id=_tk,
            terminal_close=True,
            realized_pnl_usd=5.0,
            fees_usd=0.0,
            entry_time_iso=_iso,
            side="LONG",
            exit_components_raw={"timing_pressure": 0.3, "time_decay_pressure": 0.4},
            exit_pressure_total=0.7,
            snapshot={"pnl": 5.0, "pnl_pct": 0.5, "mfe": 8.0, "mae": -1.0, "hold_minutes": 30},
            timestamp="2026-03-14T14:30:00+00:00",
        )
        self.assertTrue(self.exit_log.exists())
        lines = self.exit_log.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        issues = validate_exit_attribution(rec)
        self.assertEqual(issues, [], f"validation issues: {issues}")
        self.assertEqual(rec["event_type"], "alpaca_exit_attribution")
        self.assertEqual(rec["symbol"], "TSLA")
        self.assertEqual(rec["winner"], "time_exit")
        self.assertEqual(rec["exit_pressure_total"], 0.7)
        self.assertEqual(rec["snapshot"]["hold_minutes"], 30)
        self.assertIn("trade_key", rec)
        self.assertEqual(rec["trade_key"], _tk)
        self.assertEqual(rec["canonical_trade_id"], _tk)
        self.assertTrue(rec["terminal_close"])
        self.assertEqual(rec["fees_usd"], 0.0)
        self.assertEqual(rec["realized_pnl_usd"], 5.0)

    def test_exit_trade_key_derived_when_missing(self):
        from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution
        from src.telemetry.alpaca_trade_key import build_trade_key

        emit_exit_attribution(
            trade_id="open_NVDA_1",
            symbol="NVDA",
            winner="pressure",
            entry_time_iso="2026-03-17T10:00:00+00:00",
            side="SHORT",
            timestamp="2026-03-17T11:00:00+00:00",
        )
        rec = json.loads(Path(self.tmp).joinpath("alpaca_exit_attribution.jsonl").read_text().strip().splitlines()[-1])
        self.assertEqual(rec["trade_key"], build_trade_key("NVDA", "SHORT", "2026-03-17T10:00:00+00:00"))
