"""Strict gate: LONG→SHORT style close (flip/displacement) joins via canonical_trade_id_resolved."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import tempfile

from src.telemetry.alpaca_trade_key import build_trade_key


class TestStrictCompletenessDisplacementLongToShort(unittest.TestCase):
    def test_flip_close_alias_chain_armed(self) -> None:
        """
        Simulates closing a LONG with an exit-leg trade_key on SHORT (fill-time key),
        bridged from intent-time LONG key by ``canonical_trade_id_resolved``.
        """
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        sym = "DISP"
        entry_iso = "2026-04-10T15:00:00+00:00"
        ct_long = build_trade_key(sym, "LONG", entry_iso)
        ct_short = build_trade_key(sym, "SHORT", entry_iso)
        tid = f"open_{sym}_{entry_iso}"

        it = {
            "intent_id": "i_disp",
            "signal_layers": {
                "alpha_signals": [{"name": "a", "score": 1.0}],
                "flow_signals": [{"name": "f", "score": 0.5}],
            },
            "gates": {},
            "final_decision": {"outcome": "entered", "primary_reason": "preflight_close_chain"},
        }
        edm = {
            "event_type": "entry_decision_made",
            "entry_intent_synthetic": False,
            "entry_intent_source": "live_runtime",
            "entry_intent_status": "OK",
            "symbol": sym,
            "trade_id": tid,
            "canonical_trade_id": ct_long,
            "trade_key": ct_short,
            "signal_trace": {"policy_anchor": "displacement_preflight", "intelligence_trace": it},
            "entry_score_total": 2.0,
            "entry_score_components": {"a": 1.0, "f": 0.5},
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True)
            (root / "main.py").write_text("# stub\n", encoding="utf-8")

            exit_row = {
                "trade_id": tid,
                "symbol": sym,
                "timestamp": "2026-04-10T16:00:00+00:00",
                "entry_timestamp": entry_iso,
                "side": "buy",
                "exit_price": 101.0,
                "pnl": 1.0,
            }
            (logs / "exit_attribution.jsonl").write_text(json.dumps(exit_row) + "\n", encoding="utf-8")

            unified_lines = [
                {
                    "event_type": "alpaca_entry_attribution",
                    "trade_key": ct_long,
                    "canonical_trade_id": ct_long,
                    "composite_score": 2.0,
                },
                {
                    "event_type": "alpaca_exit_attribution",
                    "trade_id": tid,
                    "trade_key": ct_short,
                    "canonical_trade_id": ct_short,
                    "terminal_close": True,
                },
            ]
            (logs / "alpaca_unified_events.jsonl").write_text(
                "\n".join(json.dumps(x) for x in unified_lines) + "\n", encoding="utf-8"
            )

            order_row = {"canonical_trade_id": ct_short, "type": "order", "order_id": "o_disp"}
            (logs / "orders.jsonl").write_text(json.dumps(order_row) + "\n", encoding="utf-8")

            run_lines = [
                {
                    "event_type": "canonical_trade_id_resolved",
                    "symbol": sym,
                    "canonical_trade_id_intent": ct_long,
                    "canonical_trade_id_fill": ct_short,
                },
                {
                    "event_type": "trade_intent",
                    "symbol": sym,
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct_long,
                    "trade_key": ct_short,
                    "entry_intent_synthetic": False,
                },
                {
                    "event_type": "exit_intent",
                    "symbol": sym,
                    "canonical_trade_id": ct_short,
                    "trade_key": ct_short,
                    "thesis_break_reason": "preflight_close_chain:displacement_close",
                },
                edm,
            ]
            (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_lines) + "\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=0.0, audit=False)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED", r)
            self.assertEqual(r["trades_complete"], 1, r)
            self.assertEqual(r["trades_incomplete"], 0, r)

    def test_orders_opposite_side_same_epoch_joins_without_resolved_row(self) -> None:
        """
        Production: unified exit + run keyed SHORT; ``close_position`` order line may carry
        LONG canonical_trade_id for the same UTC-second floor (no ``canonical_trade_id_resolved``).
        """
        from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

        sym = "TSLA"
        entry_iso = "2026-04-22T15:46:21+00:00"
        ct_long = build_trade_key(sym, "LONG", entry_iso)
        ct_short = build_trade_key(sym, "SHORT", entry_iso)
        tid = f"open_{sym}_{entry_iso}"

        it = {
            "intent_id": "i_ts",
            "signal_layers": {
                "alpha_signals": [{"name": "a", "score": 1.0}],
                "flow_signals": [{"name": "f", "score": 0.5}],
            },
            "gates": {},
            "final_decision": {"outcome": "entered", "primary_reason": "displacement"},
        }
        edm = {
            "event_type": "entry_decision_made",
            "entry_intent_synthetic": False,
            "entry_intent_source": "live_runtime",
            "entry_intent_status": "OK",
            "symbol": sym,
            "trade_id": tid,
            "canonical_trade_id": ct_short,
            "trade_key": ct_short,
            "signal_trace": {"policy_anchor": "displacement", "intelligence_trace": it},
            "entry_score_total": 2.0,
            "entry_score_components": {"a": 1.0, "f": 0.5},
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True)
            (root / "main.py").write_text("# stub\n", encoding="utf-8")

            exit_row = {
                "trade_id": tid,
                "symbol": sym,
                "timestamp": "2026-04-22T15:49:52+00:00",
                "entry_timestamp": entry_iso,
                "side": "sell",
                "exit_price": 390.7,
                "pnl": 0.4,
            }
            (logs / "exit_attribution.jsonl").write_text(json.dumps(exit_row) + "\n", encoding="utf-8")

            unified_lines = [
                {
                    "event_type": "alpaca_entry_attribution",
                    "trade_id": tid,
                    "trade_key": ct_short,
                    "canonical_trade_id": ct_short,
                    "composite_score": 2.0,
                },
                {
                    "event_type": "alpaca_exit_attribution",
                    "trade_id": tid,
                    "trade_key": ct_short,
                    "canonical_trade_id": ct_short,
                    "terminal_close": True,
                },
            ]
            (logs / "alpaca_unified_events.jsonl").write_text(
                "\n".join(json.dumps(x) for x in unified_lines) + "\n", encoding="utf-8"
            )

            order_row = {
                "canonical_trade_id": ct_long,
                "trade_key": ct_long,
                "type": "order",
                "order_id": "o_ts",
            }
            (logs / "orders.jsonl").write_text(json.dumps(order_row) + "\n", encoding="utf-8")

            run_lines = [
                {
                    "event_type": "trade_intent",
                    "symbol": sym,
                    "decision_outcome": "entered",
                    "canonical_trade_id": ct_short,
                    "trade_key": ct_short,
                    "entry_intent_synthetic": False,
                },
                {
                    "event_type": "exit_intent",
                    "symbol": sym,
                    "canonical_trade_id": ct_short,
                    "trade_key": ct_short,
                    "thesis_break_reason": "displacement_close",
                },
                edm,
            ]
            (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_lines) + "\n", encoding="utf-8")

            r = evaluate_completeness(root, open_ts_epoch=0.0, audit=False)
            self.assertEqual(r["LEARNING_STATUS"], "ARMED", r)
            self.assertEqual(r["trades_complete"], 1, r)
            self.assertEqual(r["trades_incomplete"], 0, r)


if __name__ == "__main__":
    unittest.main()
