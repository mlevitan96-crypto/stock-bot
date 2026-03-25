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

    def test_strict_gate_resolves_intent_vs_fill_via_canonical_trade_id_resolved(self):
        import json
        import tempfile
        from pathlib import Path

        from src.telemetry.alpaca_trade_key import build_trade_key
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        entry_iso = "2026-03-25T13:35:10+00:00"
        intent_iso = "2026-03-25T13:35:11+00:00"
        tk_fill = build_trade_key("X", "LONG", entry_iso)
        tk_intent = build_trade_key("X", "LONG", intent_iso)
        trade_id = f"open_X_{entry_iso}"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            unified_lines = [
                {
                    "event_type": "alpaca_entry_attribution",
                    "trade_key": tk_fill,
                    "canonical_trade_id": tk_fill,
                    "symbol": "X",
                },
                {
                    "event_type": "alpaca_exit_attribution",
                    "trade_id": trade_id,
                    "terminal_close": True,
                    "trade_key": tk_fill,
                    "canonical_trade_id": tk_fill,
                    "symbol": "X",
                },
            ]
            (root / "logs" / "alpaca_unified_events.jsonl").write_text(
                "\n".join(json.dumps(x) for x in unified_lines) + "\n", encoding="utf-8"
            )
            (root / "logs" / "orders.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {"type": "order", "symbol": "X", "canonical_trade_id": tk_fill, "action": "buy"},
                        {"type": "order", "symbol": "X", "canonical_trade_id": tk_fill, "action": "close_position"},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            run_recs = [
                {
                    "event_type": "trade_intent",
                    "symbol": "X",
                    "decision_outcome": "entered",
                    "canonical_trade_id": tk_intent,
                },
                {
                    "event_type": "canonical_trade_id_resolved",
                    "symbol": "X",
                    "canonical_trade_id_intent": tk_intent,
                    "canonical_trade_id_fill": tk_fill,
                },
                {"event_type": "exit_intent", "symbol": "X", "canonical_trade_id": tk_fill},
            ]
            (root / "logs" / "run.jsonl").write_text(
                "\n".join(json.dumps(x) for x in run_recs) + "\n", encoding="utf-8"
            )
            ex = {
                "trade_id": trade_id,
                "symbol": "X",
                "side": "long",
                "timestamp": "2026-03-25T18:00:00+00:00",
                "entry_timestamp": entry_iso,
                "exit_reason": "test",
                "pnl": 1.23,
                "exit_price": 100.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(json.dumps(ex) + "\n", encoding="utf-8")
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=None, audit=True)
            self.assertEqual(r["trades_seen"], 1)
            self.assertEqual(r["trades_complete"], 1)
            self.assertEqual(r["trades_incomplete"], 0)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED")
            self.assertTrue(len(r.get("chain_matrices_complete_sample") or []) >= 1)

    def test_strict_gate_orders_entry_and_exit_share_canonical(self):
        import json
        import tempfile
        from pathlib import Path

        from src.telemetry.alpaca_trade_key import build_trade_key
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        entry_iso = "2026-03-26T14:00:00+00:00"
        tk = build_trade_key("ZZ", "SHORT", entry_iso)
        trade_id = f"open_ZZ_{entry_iso}"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            (root / "logs" / "alpaca_unified_events.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {
                            "event_type": "alpaca_entry_attribution",
                            "trade_key": tk,
                            "canonical_trade_id": tk,
                            "symbol": "ZZ",
                        },
                        {
                            "event_type": "alpaca_exit_attribution",
                            "trade_id": trade_id,
                            "terminal_close": True,
                            "trade_key": tk,
                            "symbol": "ZZ",
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "logs" / "orders.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {"type": "order", "symbol": "ZZ", "canonical_trade_id": tk},
                        {"type": "order", "symbol": "ZZ", "canonical_trade_id": tk},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "logs" / "run.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {
                            "event_type": "trade_intent",
                            "symbol": "ZZ",
                            "decision_outcome": "entered",
                            "canonical_trade_id": tk,
                        },
                        {"event_type": "exit_intent", "symbol": "ZZ", "canonical_trade_id": tk},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            ex = {
                "trade_id": trade_id,
                "symbol": "ZZ",
                "side": "short",
                "timestamp": "2026-03-26T20:00:00+00:00",
                "entry_timestamp": entry_iso,
                "exit_reason": "test",
                "pnl": 0.5,
                "exit_price": 50.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(json.dumps(ex) + "\n", encoding="utf-8")
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=None)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED")


class TestStrictEraEntryCohort(unittest.TestCase):
    ERA = 1774458080.0  # 2026-03-25T17:01:20Z

    def test_preera_open_postera_exit_excluded_not_incomplete(self):
        import json
        import tempfile
        from pathlib import Path

        from src.telemetry.alpaca_trade_key import build_trade_key
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        lcid_tid = "open_LCID_2026-03-25T16:20:57.882391+00:00"
        post_entry = "2026-03-25T17:05:00+00:00"
        tk_q = build_trade_key("QQ", "LONG", post_entry)
        q_tid = f"open_QQ_{post_entry}"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            lcid_ex = {
                "trade_id": lcid_tid,
                "symbol": "LCID",
                "side": "long",
                "timestamp": "2026-03-25T17:31:00+00:00",
                "entry_timestamp": "2026-03-25T16:20:57+00:00",
                "exit_reason": "test",
                "pnl": -1.0,
                "exit_price": 3.0,
            }
            q_ex = {
                "trade_id": q_tid,
                "symbol": "QQ",
                "side": "long",
                "timestamp": "2026-03-25T17:40:00+00:00",
                "entry_timestamp": post_entry,
                "exit_reason": "test",
                "pnl": 1.0,
                "exit_price": 100.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(
                json.dumps(lcid_ex) + "\n" + json.dumps(q_ex) + "\n", encoding="utf-8"
            )
            uni = [
                {
                    "event_type": "alpaca_entry_attribution",
                    "trade_key": tk_q,
                    "canonical_trade_id": tk_q,
                    "symbol": "QQ",
                },
                {
                    "event_type": "alpaca_exit_attribution",
                    "trade_id": q_tid,
                    "terminal_close": True,
                    "trade_key": tk_q,
                    "symbol": "QQ",
                },
            ]
            (root / "logs" / "alpaca_unified_events.jsonl").write_text(
                "\n".join(json.dumps(x) for x in uni) + "\n", encoding="utf-8"
            )
            (root / "logs" / "orders.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {"type": "order", "symbol": "QQ", "canonical_trade_id": tk_q},
                        {"type": "order", "symbol": "QQ", "canonical_trade_id": tk_q},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "logs" / "run.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {
                            "event_type": "trade_intent",
                            "symbol": "QQ",
                            "decision_outcome": "entered",
                            "canonical_trade_id": tk_q,
                        },
                        {"event_type": "exit_intent", "symbol": "QQ", "canonical_trade_id": tk_q},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=self.ERA, audit=True)
            self.assertEqual(r["trades_seen"], 1)
            self.assertEqual(r["trades_complete"], 1)
            self.assertEqual(r["trades_incomplete"], 0)
            self.assertEqual(r["strict_cohort_excluded_preera_open_count"], 1)
            self.assertIn("PREERA_OPEN", r["strict_cohort_exclusion_reasons"])
            self.assertIn(lcid_tid, r["excluded_trade_ids_capped"])
            self.assertEqual(r["LEARNING_STATUS"], "ARMED")

    def test_postera_open_included_can_arm(self):
        import json
        import tempfile
        from pathlib import Path

        from src.telemetry.alpaca_trade_key import build_trade_key
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        post_entry = "2026-03-25T17:10:00+00:00"
        tk = build_trade_key("RR", "LONG", post_entry)
        trade_id = f"open_RR_{post_entry}"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            (root / "logs" / "alpaca_unified_events.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {
                            "event_type": "alpaca_entry_attribution",
                            "trade_key": tk,
                            "canonical_trade_id": tk,
                            "symbol": "RR",
                        },
                        {
                            "event_type": "alpaca_exit_attribution",
                            "trade_id": trade_id,
                            "terminal_close": True,
                            "trade_key": tk,
                            "symbol": "RR",
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "logs" / "orders.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {"type": "order", "symbol": "RR", "canonical_trade_id": tk},
                        {"type": "order", "symbol": "RR", "canonical_trade_id": tk},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "logs" / "run.jsonl").write_text(
                "\n".join(
                    json.dumps(x)
                    for x in (
                        {
                            "event_type": "trade_intent",
                            "symbol": "RR",
                            "decision_outcome": "entered",
                            "canonical_trade_id": tk,
                        },
                        {"event_type": "exit_intent", "symbol": "RR", "canonical_trade_id": tk},
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            ex = {
                "trade_id": trade_id,
                "symbol": "RR",
                "side": "long",
                "timestamp": "2026-03-25T18:00:00+00:00",
                "entry_timestamp": post_entry,
                "exit_reason": "test",
                "pnl": 0.5,
                "exit_price": 50.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(json.dumps(ex) + "\n", encoding="utf-8")
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=self.ERA)
            self.assertEqual(r["trades_seen"], 1)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED")

    def test_cohort_empty_after_exclusion_trades_seen_zero_blocked(self):
        import json
        import tempfile
        from pathlib import Path

        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        lcid_tid = "open_LCID_2026-03-25T16:20:57.882391+00:00"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir(parents=True)
            lcid_ex = {
                "trade_id": lcid_tid,
                "symbol": "LCID",
                "side": "long",
                "timestamp": "2026-03-25T17:31:00+00:00",
                "entry_timestamp": "2026-03-25T16:20:57+00:00",
                "exit_reason": "test",
                "pnl": -1.0,
                "exit_price": 3.0,
            }
            (root / "logs" / "exit_attribution.jsonl").write_text(json.dumps(lcid_ex) + "\n", encoding="utf-8")
            for name in ("alpaca_unified_events.jsonl", "orders.jsonl", "run.jsonl"):
                (root / "logs" / name).write_text("", encoding="utf-8")
            (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=self.ERA)
            self.assertEqual(r["trades_seen"], 0)
            self.assertEqual(r["learning_fail_closed_reason"], "NO_POST_DEPLOY_PROOF_YET")
            self.assertEqual(r["LEARNING_STATUS"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
