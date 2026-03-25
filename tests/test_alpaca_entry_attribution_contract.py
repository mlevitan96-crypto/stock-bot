"""
Contract tests for Alpaca entry attribution schema and emitter.
Validates canonical shape, validation rules, and that emitter produces valid JSONL.
Run: pytest tests/test_alpaca_entry_attribution_contract.py -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestEntryAttributionSchema(unittest.TestCase):
    def test_entry_attribution_shape_has_required_keys(self):
        from src.telemetry.alpaca_attribution_schema import entry_attribution_shape

        shape = entry_attribution_shape()
        self.assertEqual(shape["event_type"], "alpaca_entry_attribution")
        self.assertIn("schema_version", shape)
        self.assertIn("trade_id", shape)
        self.assertIn("trade_key", shape)
        self.assertIn("symbol", shape)
        self.assertIn("timestamp", shape)
        self.assertIn("side", shape)
        self.assertIn("raw_signals", shape)
        self.assertIn("weights", shape)
        self.assertIn("contributions", shape)
        self.assertIn("composite_score", shape)
        self.assertIn("gates", shape)
        self.assertIn("decision", shape)
        self.assertIn("decision_reason", shape)
        self.assertIn("entry_dominant_component", shape)
        self.assertIn("entry_dominant_component_value", shape)
        self.assertIn("entry_margin_to_threshold", shape)

    def test_validate_entry_attribution_accepts_valid(self):
        from src.telemetry.alpaca_attribution_schema import (
            SCHEMA_VERSION,
            validate_entry_attribution,
        )

        rec = {
            "event_type": "alpaca_entry_attribution",
            "schema_version": SCHEMA_VERSION,
            "trade_id": "open_AAPL_2026-03-14T12-00-00Z",
            "symbol": "AAPL",
            "timestamp": "2026-03-14T12:00:00+00:00",
            "side": "LONG",
            "raw_signals": {"momentum": 0.5},
            "weights": {"momentum": 1.0},
            "contributions": {"momentum": 0.5},
            "composite_score": 0.5,
            "gates": {},
            "decision": "OPEN_LONG",
            "decision_reason": "filled",
        }
        issues = validate_entry_attribution(rec)
        self.assertEqual(issues, [])

    def test_validate_entry_attribution_rejects_wrong_event_type(self):
        from src.telemetry.alpaca_attribution_schema import (
            SCHEMA_VERSION,
            validate_entry_attribution,
        )

        rec = {
            "event_type": "alpaca_exit_attribution",
            "schema_version": SCHEMA_VERSION,
        }
        issues = validate_entry_attribution(rec)
        self.assertTrue(any("event_type" in i for i in issues))

    def test_validate_entry_attribution_requires_schema_version(self):
        from src.telemetry.alpaca_attribution_schema import validate_entry_attribution

        rec = {"event_type": "alpaca_entry_attribution"}
        issues = validate_entry_attribution(rec)
        self.assertTrue(any("schema_version" in i for i in issues))


class TestEntryAttributionEmitter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.entry_log = Path(self.tmp) / "alpaca_entry_attribution.jsonl"
        self._prev = os.environ.get("ALPACA_ENTRY_ATTRIBUTION_PATH")
        os.environ["ALPACA_ENTRY_ATTRIBUTION_PATH"] = str(self.entry_log)

    def tearDown(self):
        if self._prev is not None:
            os.environ["ALPACA_ENTRY_ATTRIBUTION_PATH"] = self._prev
        elif "ALPACA_ENTRY_ATTRIBUTION_PATH" in os.environ:
            del os.environ["ALPACA_ENTRY_ATTRIBUTION_PATH"]

    def test_emit_entry_attribution_writes_valid_jsonl(self):
        from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution
        from src.telemetry.alpaca_attribution_schema import validate_entry_attribution
        from src.telemetry.alpaca_trade_key import build_trade_key

        _ts = "2026-03-14T12:00:00+00:00"
        _exp = build_trade_key("TSLA", "LONG", _ts)
        emit_entry_attribution(
            trade_id="open_TSLA_2026-03-14T12-00-00Z",
            symbol="TSLA",
            side="LONG",
            decision="OPEN_LONG",
            decision_reason="filled",
            raw_signals={"flow": 0.3},
            weights={"flow": 1.0},
            contributions={"flow": 0.3},
            composite_score=0.3,
            timestamp=_ts,
        )
        self.assertTrue(self.entry_log.exists())
        lines = self.entry_log.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        issues = validate_entry_attribution(rec)
        self.assertEqual(issues, [], f"validation issues: {issues}")
        self.assertEqual(rec["event_type"], "alpaca_entry_attribution")
        self.assertEqual(rec["symbol"], "TSLA")
        self.assertEqual(rec["decision"], "OPEN_LONG")
        self.assertEqual(rec["raw_signals"], {"flow": 0.3})
        self.assertEqual(rec["contributions"], {"flow": 0.3})
        self.assertIn("trade_key", rec)
        self.assertEqual(rec["trade_key"], _exp)
        self.assertEqual(rec["canonical_trade_id"], _exp)
        self.assertEqual(rec["fees_usd"], 0.0)

    def test_entry_trade_key_matches_contract(self):
        from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution
        from src.telemetry.alpaca_trade_key import build_trade_key

        emit_entry_attribution(
            trade_id="open_AAPL_1",
            symbol="aapl",
            side="short",
            decision="OPEN_SHORT",
            decision_reason="test",
            trade_key=build_trade_key("AAPL", "SHORT", "2026-03-17T16:00:00+00:00"),
            timestamp="2026-03-17T16:00:00+00:00",
        )
        rec = json.loads(Path(self.tmp).joinpath("alpaca_entry_attribution.jsonl").read_text().strip().splitlines()[-1])
        self.assertEqual(rec["trade_key"], build_trade_key("AAPL", "SHORT", "2026-03-17T16:00:00+00:00"))
