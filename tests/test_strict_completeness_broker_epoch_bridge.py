"""Strict gate: broker-era canonical bridges to displacement entry_ts epoch (orders + unified entry)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile

from src.telemetry.alpaca_trade_key import build_trade_key


class TestStrictCompletenessBrokerEpochBridge(unittest.TestCase):
    def test_orders_under_prior_canonical_join_after_bridge(self) -> None:
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        sym = "BRG"
        entry_iso = "2026-04-14T15:28:38.904716+00:00"
        ct_old = build_trade_key(sym, "SHORT", "2026-04-14T13:34:41.506094+00:00")
        ct_new = build_trade_key(sym, "SHORT", entry_iso)
        ct_new_exit_leg = build_trade_key(sym, "LONG", entry_iso)
        tid = f"open_{sym}_{entry_iso}"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True)
            (root / "main.py").write_text("# stub\n", encoding="utf-8")

            exit_row = {
                "trade_id": tid,
                "symbol": sym,
                "timestamp": "2026-04-14T15:32:52.695525+00:00",
                "entry_timestamp": entry_iso,
                "side": "sell",
                "exit_price": 100.0,
                "pnl": -1.23,
            }
            (logs / "exit_attribution.jsonl").write_text(json.dumps(exit_row) + "\n", encoding="utf-8")

            unified_lines = [
                {
                    "event_type": "alpaca_entry_attribution",
                    "trade_key": ct_old,
                    "canonical_trade_id": ct_old,
                    "composite_score": 2.0,
                },
                {
                    "event_type": "alpaca_exit_attribution",
                    "trade_id": tid,
                    "trade_key": ct_new,
                    "canonical_trade_id": ct_new,
                    "terminal_close": True,
                },
            ]
            (logs / "alpaca_unified_events.jsonl").write_text(
                "\n".join(json.dumps(x) for x in unified_lines) + "\n", encoding="utf-8"
            )

            order_row = {"canonical_trade_id": ct_old, "type": "order", "order_id": "o_brg"}
            (logs / "orders.jsonl").write_text(json.dumps(order_row) + "\n", encoding="utf-8")

            run_lines = [
                {
                    "event_type": "entry_decision_made",
                    "entry_intent_synthetic": False,
                    "entry_intent_source": "live_runtime",
                    "entry_intent_status": "OK",
                    "symbol": sym,
                    "trade_id": tid,
                    "canonical_trade_id": ct_new,
                    "trade_key": ct_new,
                    "entry_score_total": 2.0,
                    "entry_score_components": {"close_chain": 1.0},
                    "signal_trace": {"policy_anchor": "displacement_close"},
                },
                {
                    "event_type": "canonical_trade_id_resolved",
                    "symbol": sym,
                    "canonical_trade_id_intent": ct_old,
                    "canonical_trade_id_fill": ct_new,
                    "close_truth_chain_reason": "displacement_close:broker_epoch_bridge",
                },
                {
                    "event_type": "canonical_trade_id_resolved",
                    "symbol": sym,
                    "canonical_trade_id_intent": ct_new,
                    "canonical_trade_id_fill": ct_new_exit_leg,
                    "close_truth_chain_reason": "displacement_close",
                },
                {
                    "event_type": "trade_intent",
                    "symbol": sym,
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct_new,
                    "trade_key": ct_new_exit_leg,
                    "entry_intent_synthetic": False,
                },
                {
                    "event_type": "exit_intent",
                    "symbol": sym,
                    "canonical_trade_id": ct_new,
                    "trade_key": ct_new,
                    "thesis_break_reason": "displacement",
                },
            ]
            (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_lines) + "\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=0.0, audit=False)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED", r)
            self.assertEqual(r["trades_complete"], 1, r)
            self.assertEqual(r["trades_incomplete"], 0, r)


if __name__ == "__main__":
    unittest.main()
