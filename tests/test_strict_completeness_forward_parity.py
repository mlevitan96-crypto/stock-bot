"""Synthetic strict completeness gate: one closed trade with aligned keys must ARM."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile


class TestStrictCompletenessSynthetic(unittest.TestCase):
    def test_single_trade_armed_when_keys_align(self) -> None:
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        ct = "TEST|LONG|1700000000"
        tid = "open_TEST_2023-11-15T00:00:00+00:00"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True)
            (root / "main.py").write_text("# stub\n", encoding="utf-8")

            exit_row = {
                "trade_id": tid,
                "symbol": "TEST",
                "timestamp": "2023-11-15T01:00:00+00:00",
                "entry_timestamp": "2023-11-15T00:00:00+00:00",
                "side": "buy",
                "exit_price": 101.0,
                "pnl": 1.0,
            }
            (logs / "exit_attribution.jsonl").write_text(json.dumps(exit_row) + "\n", encoding="utf-8")

            unified_lines = [
                {"event_type": "alpaca_entry_attribution", "trade_key": ct, "canonical_trade_id": ct},
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
            self.assertEqual(r["LEARNING_STATUS"], "ARMED", r)
            self.assertEqual(r["trades_complete"], 1)
            self.assertEqual(r["trades_incomplete"], 0)


if __name__ == "__main__":
    unittest.main()
