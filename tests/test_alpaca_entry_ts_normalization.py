"""Canonical entry timestamp normalization and trade_key (Alpaca strict completeness)."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.telemetry.alpaca_trade_key import (
    build_trade_key,
    normalize_entry_ts_to_utc_second,
    normalize_time,
)


class TestNormalizeEntryTs(unittest.TestCase):
    def test_iso_z_deterministic(self):
        s = "2026-03-14T12:00:05.999000+00:00"
        e = normalize_entry_ts_to_utc_second(s)
        self.assertEqual(e, normalize_entry_ts_to_utc_second("2026-03-14T12:00:05+00:00"))

    def test_naive_datetime_treated_as_utc(self):
        dt = datetime(2026, 3, 14, 12, 0, 7)
        e = normalize_entry_ts_to_utc_second(dt)
        dt_utc = datetime(2026, 3, 14, 12, 0, 7, tzinfo=timezone.utc)
        self.assertEqual(e, int(dt_utc.timestamp()))

    def test_int_passthrough_truncates_float(self):
        self.assertEqual(normalize_entry_ts_to_utc_second(1700000000), 1700000000)
        self.assertEqual(normalize_entry_ts_to_utc_second(1700000000.9), 1700000000)

    def test_microseconds_stripped(self):
        dt = datetime(2026, 1, 1, 0, 0, 1, 500000, tzinfo=timezone.utc)
        self.assertEqual(normalize_entry_ts_to_utc_second(dt), int(datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc).timestamp()))


class TestBuildTradeKeyEpoch(unittest.TestCase):
    def test_matches_normalize_segment(self):
        iso = "2026-03-17T16:00:00+00:00"
        epoch = normalize_entry_ts_to_utc_second(iso)
        tk = build_trade_key("AAPL", "SHORT", iso)
        self.assertEqual(tk, f"AAPL|SHORT|{epoch}")

    def test_normalize_time_iso_roundtrip(self):
        iso = "2026-03-14T12:00:00+00:00"
        self.assertEqual(normalize_time(iso), iso)

    def test_stable_across_subsecond_noise(self):
        """Partial fills must not change canonical id: same UTC second -> same trade_key."""
        a = build_trade_key("SPY", "LONG", "2026-01-15T15:00:00+00:00")
        b = build_trade_key("SPY", "LONG", "2026-01-15T15:00:00.887123+00:00")
        self.assertEqual(a, b)


class TestMainTradeIntentEnteredCanonical(unittest.TestCase):
    def test_main_py_sets_canonical_on_entered_branch(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        txt = (root / "main.py").read_text(encoding="utf-8")
        self.assertIn('elif (decision_outcome or "").lower() == "entered":', txt)
        self.assertIn("build_trade_key(symbol, _side_norm, _anchor)", txt)


class TestStrictCompletenessGate(unittest.TestCase):
    def test_gate_flags_missing_unified_exit(self):
        import json
        import tempfile
        from pathlib import Path

        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            (root / "logs" / "alpaca_unified_events.jsonl").write_text("", encoding="utf-8")
            (root / "logs" / "run.jsonl").write_text("", encoding="utf-8")
            (root / "logs" / "orders.jsonl").write_text("", encoding="utf-8")
            # One synthetic closed trade in exit_attribution
            ex = {
                "trade_id": "open_X_2026-03-25T13:35:10.342511+00:00",
                "symbol": "X",
                "timestamp": "2026-03-25T18:00:00+00:00",
                "entry_timestamp": "2026-03-25T13:35:10.342511+00:00",
                "exit_reason": "test",
                "pnl": 1.23,
                "exit_price": 100.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(json.dumps(ex) + "\n", encoding="utf-8")
            (root / "main.py").write_text("_ctid = None\n" + '"canonical_trade_id": _ctid\n', encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=None)
            self.assertGreaterEqual(r["trades_incomplete"], 1)
            self.assertIn("LEARNING_STATUS", r)
            self.assertEqual(r["LEARNING_STATUS"], "BLOCKED")

    def test_gate_blocks_vacuous_zero_trades(self):
        import tempfile
        from pathlib import Path

        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            (root / "logs" / "alpaca_unified_events.jsonl").write_text("", encoding="utf-8")
            (root / "logs" / "run.jsonl").write_text("", encoding="utf-8")
            (root / "logs" / "orders.jsonl").write_text("", encoding="utf-8")
            (root / "logs" / "exit_attribution.jsonl").write_text("", encoding="utf-8")
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=None)
            self.assertEqual(r["trades_seen"], 0)
            self.assertEqual(r["LEARNING_STATUS"], "BLOCKED")
            self.assertEqual(r.get("learning_fail_closed_reason"), "NO_POST_DEPLOY_PROOF_YET")


if __name__ == "__main__":
    unittest.main()
