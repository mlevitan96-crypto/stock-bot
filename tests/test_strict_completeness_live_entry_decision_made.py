"""Strict gate: post live-intent epoch trades require contract-satisfying entry_decision_made."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile


class TestStrictCompletenessLiveEntryDecisionMade(unittest.TestCase):
    def _base_logs(self, root: Path, tid: str, ct: str) -> None:
        logs = root / "logs"
        logs.mkdir(parents=True)
        (root / "main.py").write_text("# stub\n", encoding="utf-8")

        exit_row = {
            "trade_id": tid,
            "symbol": "TEST",
            "timestamp": "2026-03-28T16:00:00+00:00",
            "entry_timestamp": "2026-03-28T15:00:00+00:00",
            "side": "buy",
            "exit_price": 101.0,
            "pnl": 1.0,
        }
        (logs / "exit_attribution.jsonl").write_text(json.dumps(exit_row) + "\n", encoding="utf-8")

        unified_lines = [
            {"event_type": "alpaca_entry_attribution", "trade_key": ct, "canonical_trade_id": ct, "composite_score": 2.0},
            {
                "event_type": "alpaca_exit_attribution",
                "trade_id": tid,
                "trade_key": ct,
                "canonical_trade_id": ct,
                "terminal_close": True,
            },
        ]
        (logs / "alpaca_unified_events.jsonl").write_text(
            "\n".join(json.dumps(x) for x in unified_lines) + "\n", encoding="utf-8"
        )

        order_row = {"canonical_trade_id": ct, "type": "order", "order_id": "o1"}
        (logs / "orders.jsonl").write_text(json.dumps(order_row) + "\n", encoding="utf-8")

    def test_post_epoch_armed_with_ok_entry_decision_made(self) -> None:
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        ct = "TEST|LONG|1772222400"
        tid = "open_TEST_2026-03-28T15:00:00+00:00"
        it = {
            "intent_id": "i1",
            "signal_layers": {
                "alpha_signals": [{"name": "a", "score": 1.0}],
                "flow_signals": [{"name": "f", "score": 0.5}],
            },
            "gates": {},
            "final_decision": {"outcome": "entered", "primary_reason": "ok"},
        }
        edm = {
            "event_type": "entry_decision_made",
            "entry_intent_synthetic": False,
            "entry_intent_source": "live_runtime",
            "entry_intent_status": "OK",
            "symbol": "TEST",
            "trade_id": tid,
            "canonical_trade_id": ct,
            "trade_key": ct,
            "signal_trace": {"policy_anchor": "test_policy", "intelligence_trace": it},
            "entry_score_total": 2.0,
            "entry_score_components": {"a": 1.0, "f": 0.5},
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._base_logs(root, tid, ct)
            logs = root / "logs"
            run_lines = [
                {
                    "event_type": "trade_intent",
                    "symbol": "TEST",
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct,
                    "trade_key": ct,
                    "entry_intent_synthetic": False,
                },
                {"event_type": "exit_intent", "symbol": "TEST", "canonical_trade_id": ct, "trade_key": ct},
                edm,
            ]
            (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_lines) + "\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=0.0, audit=False)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED", r)
            self.assertEqual(r["trades_complete"], 1)

    def test_post_epoch_blocked_without_entry_decision_made(self) -> None:
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        ct = "TEST|LONG|1772222400"
        tid = "open_TEST_2026-03-28T15:00:00+00:00"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._base_logs(root, tid, ct)
            logs = root / "logs"
            run_lines = [
                {
                    "event_type": "trade_intent",
                    "symbol": "TEST",
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct,
                    "trade_key": ct,
                },
                {"event_type": "exit_intent", "symbol": "TEST", "canonical_trade_id": ct, "trade_key": ct},
            ]
            (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_lines) + "\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=0.0, audit=False)
            self.assertEqual(r["LEARNING_STATUS"], "BLOCKED", r)
            self.assertIn("live_entry_decision_made_missing_or_blocked", r["reason_histogram"])


if __name__ == "__main__":
    unittest.main()
