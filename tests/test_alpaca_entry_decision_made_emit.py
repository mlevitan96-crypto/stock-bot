"""Contract tests for live `entry_decision_made` telemetry (no execution)."""
from __future__ import annotations

import unittest

from telemetry.alpaca_entry_decision_made_emit import (
    ENTRY_INTENT_STATUS_BLOCKER,
    ENTRY_INTENT_STATUS_OK,
    audit_entry_decision_made_row_ok,
    build_entry_decision_made_record,
    emit_entry_decision_made,
)


def _minimal_trace() -> dict:
    return {
        "intent_id": "test-intent",
        "signal_layers": {
            "alpha_signals": [{"name": "momentum", "score": 1.2}],
            "flow_signals": [{"name": "flow", "score": 0.3}],
        },
        "gates": {},
        "final_decision": {"outcome": "entered", "primary_reason": "all_gates_passed"},
    }


class TestEntryDecisionMadeEmit(unittest.TestCase):
    def test_ok_row_passes_audit(self) -> None:
        tr = _minimal_trace()
        rec = build_entry_decision_made_record(
            symbol="PLTR",
            side="buy",
            score=2.1,
            comps={"momentum": 1.2, "flow": 0.3},
            cluster={"direction": "bullish", "composite_meta": {}},
            intelligence_trace=tr,
            canonical_trade_id="PLTR|LONG|1700000000",
            trade_id_open="open_PLTR_2026-03-28T15:00:00+00:00",
            decision_event_id="de1",
            time_bucket_id="tb1",
            symbol_normalized="PLTR",
        )
        self.assertEqual(rec["entry_intent_status"], ENTRY_INTENT_STATUS_OK)
        self.assertEqual(rec["event_type"], "entry_decision_made")
        self.assertFalse(rec.get("entry_intent_synthetic"))
        self.assertTrue(audit_entry_decision_made_row_ok(rec))

    def test_blocker_when_no_numeric_score(self) -> None:
        rec = build_entry_decision_made_record(
            symbol="PLTR",
            side="buy",
            score=None,
            comps={},
            cluster={"direction": "bullish", "composite_meta": {}},
            intelligence_trace=_minimal_trace(),
            canonical_trade_id="K",
            trade_id_open="open_PLTR_2026-03-28T15:00:00+00:00",
            decision_event_id=None,
            time_bucket_id=None,
            symbol_normalized="PLTR",
        )
        self.assertEqual(rec["entry_intent_status"], ENTRY_INTENT_STATUS_BLOCKER)
        self.assertTrue(rec["entry_score_components"].get("_blocked"))
        self.assertFalse(audit_entry_decision_made_row_ok(rec))

    def test_components_only_ok_without_layers_still_ok(self) -> None:
        rec = build_entry_decision_made_record(
            symbol="X",
            side="buy",
            score=1.5,
            comps={"a": 1.0, "b": 0.5},
            cluster={"direction": "bullish", "composite_meta": {}},
            intelligence_trace={"intent_id": "z", "gates": {}, "final_decision": {"outcome": "entered"}},
            canonical_trade_id="K",
            trade_id_open="open_X_2026-03-28T15:00:00+00:00",
            decision_event_id=None,
            time_bucket_id=None,
            symbol_normalized="X",
        )
        self.assertEqual(rec["entry_intent_status"], ENTRY_INTENT_STATUS_OK)
        src = rec["signal_trace"].get("source", "")
        self.assertTrue(
            "equalizer_components_only" in src or "intelligence_trace_without_layers" in src,
            msg=src,
        )
        self.assertTrue(audit_entry_decision_made_row_ok(rec))

    def test_synthetic_rejected_by_audit(self) -> None:
        rec = build_entry_decision_made_record(
            symbol="X",
            side="buy",
            score=1.0,
            comps={"a": 1.0},
            cluster={"direction": "bullish"},
            intelligence_trace=_minimal_trace(),
            canonical_trade_id="K",
            trade_id_open="open_X_2026-03-28T15:00:00+00:00",
            decision_event_id=None,
            time_bucket_id=None,
            symbol_normalized="X",
        )
        rec["strict_backfilled"] = True
        self.assertFalse(audit_entry_decision_made_row_ok(rec))

    def test_emit_writes_via_callback(self) -> None:
        buf: list = []

        def _w(name: str, r: dict) -> None:
            buf.append((name, r))

        emit_entry_decision_made(
            _w,
            symbol="Z",
            side="buy",
            score=3.0,
            comps={"x": 3.0},
            cluster={"direction": "bullish"},
            intelligence_trace=_minimal_trace(),
            canonical_trade_id="Z|LONG|1",
            trade_id_open="open_Z_2026-03-28T16:00:00+00:00",
            decision_event_id="d",
            time_bucket_id="t",
            symbol_normalized="Z",
            phase2_enabled=True,
        )
        self.assertTrue(buf)
        self.assertEqual(buf[0][0], "run")
        self.assertEqual(buf[0][1]["event_type"], "entry_decision_made")

    def test_fixture_decision_fields_stable(self) -> None:
        """Guard: payload is telemetry-only; same inputs -> same enter/skip semantics not applicable here;
        we assert stable economic fields for replayed builder input."""
        a = build_entry_decision_made_record(
            symbol="FIX",
            side="buy",
            score=9.0,
            comps={"u": 9.0},
            cluster={"direction": "bullish"},
            intelligence_trace=_minimal_trace(),
            canonical_trade_id="FIX|LONG|9",
            trade_id_open="open_FIX_2026-03-28T12:00:00+00:00",
            decision_event_id=None,
            time_bucket_id=None,
            symbol_normalized="FIX",
        )
        b = build_entry_decision_made_record(
            symbol="FIX",
            side="buy",
            score=9.0,
            comps={"u": 9.0},
            cluster={"direction": "bullish"},
            intelligence_trace=_minimal_trace(),
            canonical_trade_id="FIX|LONG|9",
            trade_id_open="open_FIX_2026-03-28T12:00:00+00:00",
            decision_event_id=None,
            time_bucket_id=None,
            symbol_normalized="FIX",
        )
        self.assertEqual(a["entry_score_total"], b["entry_score_total"])
        self.assertEqual(a["entry_score_components"], b["entry_score_components"])
        self.assertEqual(a["entry_intent_status"], b["entry_intent_status"])


if __name__ == "__main__":
    unittest.main()
