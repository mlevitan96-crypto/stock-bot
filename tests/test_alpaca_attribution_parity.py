"""
Parity proofs: telemetry is faithful and non-invasive.
- Entry: composite_score and contributions consistent; dominant = max abs(contribution).
- Exit: pressure = sum(weighted contributions); dominant and margins correct.
- Non-invasive: emitters never raise into trading loop.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestEntryAttributionParity(unittest.TestCase):
    """A) Entry parity: decision inputs → emitted attribution matches; contributions sum = composite_score; dominant correct."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        os.environ["ALPACA_ENTRY_ATTRIBUTION_PATH"] = str(Path(self.tmp) / "entry.jsonl")

    def tearDown(self):
        if "ALPACA_ENTRY_ATTRIBUTION_PATH" in os.environ:
            del os.environ["ALPACA_ENTRY_ATTRIBUTION_PATH"]

    def test_entry_contributions_sum_equals_composite_score(self):
        from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution

        raw = {"a": 0.5, "b": 0.3}
        weights = {"a": 1.0, "b": 1.0}
        contributions = {"a": 0.5, "b": 0.3}
        composite = 0.8
        emit_entry_attribution(
            trade_id="parity_1",
            symbol="TEST",
            side="LONG",
            decision="OPEN_LONG",
            decision_reason="test",
            raw_signals=raw,
            weights=weights,
            contributions=contributions,
            composite_score=composite,
            entry_threshold=0.5,
        )
        path = Path(self.tmp) / "entry.jsonl"
        self.assertTrue(path.exists())
        rec = json.loads(path.read_text().strip().splitlines()[-1])
        self.assertEqual(rec["event_type"], "alpaca_entry_attribution")
        contrib_sum = sum(rec["contributions"].values())
        self.assertAlmostEqual(contrib_sum, rec["composite_score"], places=5)
        self.assertEqual(rec["composite_score"], composite)

    def test_entry_dominant_component_matches_max_abs_contribution(self):
        from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution

        contributions = {"flow": 0.6, "dark_pool": -0.2, "insider": 0.1}
        emit_entry_attribution(
            trade_id="parity_2",
            symbol="TEST",
            side="LONG",
            decision="OPEN_LONG",
            decision_reason="test",
            raw_signals={"flow": 0.6, "dark_pool": -0.2, "insider": 0.1},
            weights={"flow": 1.0, "dark_pool": 1.0, "insider": 1.0},
            contributions=contributions,
            composite_score=0.5,
            entry_threshold=2.5,
        )
        path = Path(self.tmp) / "entry.jsonl"
        rec = json.loads(path.read_text().strip().splitlines()[-1])
        self.assertEqual(rec["entry_dominant_component"], "flow")
        self.assertEqual(rec["entry_dominant_component_value"], 0.6)
        self.assertAlmostEqual(rec["entry_margin_to_threshold"], 0.5 - 2.5, places=5)


class TestExitAttributionParity(unittest.TestCase):
    """B) Exit parity: pressure = sum(weighted contributions); dominant correct; margins correct."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        os.environ["ALPACA_EXIT_ATTRIBUTION_PATH"] = str(Path(self.tmp) / "exit.jsonl")

    def tearDown(self):
        if "ALPACA_EXIT_ATTRIBUTION_PATH" in os.environ:
            del os.environ["ALPACA_EXIT_ATTRIBUTION_PATH"]

    def test_exit_pressure_equals_sum_contributions_dominant_and_margins(self):
        from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution

        contrib = {"signal_deterioration": 0.15, "time_decay": 0.12, "profit_protection": 0.08}
        pressure = sum(contrib.values())
        thr_norm, thr_urgent = 0.55, 0.80
        emit_exit_attribution(
            trade_id="parity_ex_1",
            symbol="TEST",
            winner="pressure_exit",
            winner_explanation="test",
            exit_components_raw=dict(contrib),
            exit_weights={"signal_deterioration": 0.22, "time_decay": 0.12, "profit_protection": 0.14},
            exit_contributions=contrib,
            exit_pressure_total=pressure,
            thresholds_used={"normal": thr_norm, "urgent": thr_urgent},
        )
        path = Path(self.tmp) / "exit.jsonl"
        self.assertTrue(path.exists())
        rec = json.loads(path.read_text().strip().splitlines()[-1])
        self.assertEqual(rec["event_type"], "alpaca_exit_attribution")
        self.assertAlmostEqual(rec["exit_pressure_total"], pressure, places=5)
        self.assertEqual(rec["exit_dominant_component"], "signal_deterioration")
        self.assertEqual(rec["exit_dominant_component_value"], 0.15)
        self.assertAlmostEqual(rec["exit_pressure_margin_exit_now"], round(pressure - thr_norm, 6), places=5)
        self.assertAlmostEqual(rec["exit_pressure_margin_exit_soon"], round(pressure - thr_urgent, 6), places=5)


class TestAttributionNonInvasive(unittest.TestCase):
    """C) Emitters must not raise; failure mode: log/skip only."""

    def test_entry_emitter_does_not_raise_on_invalid_input(self):
        from src.telemetry.alpaca_attribution_emitter import emit_entry_attribution

        emit_entry_attribution(
            trade_id="",
            symbol="",
            side="",
            decision="",
            decision_reason="",
            raw_signals=None,
            weights=None,
            contributions=None,
            composite_score=None,
        )
        # Validation may skip write; must not raise
        emit_entry_attribution(
            trade_id="inv",
            symbol="X",
            side="LONG",
            decision="OPEN_LONG",
            decision_reason="x",
            raw_signals={"a": "not_a_number"},
            weights={"a": 1.0},
        )

    def test_exit_emitter_does_not_raise_on_invalid_input(self):
        from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution

        emit_exit_attribution(trade_id="", symbol="", winner="", winner_explanation="", snapshot=None)
        emit_exit_attribution(
            trade_id="inv",
            symbol="X",
            winner="x",
            exit_pressure_total="not_float",
            thresholds_used={"normal": 0.5},
        )
