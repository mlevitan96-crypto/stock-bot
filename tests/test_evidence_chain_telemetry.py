"""Evidence chain: shadow tape + capacity-block join vocabulary (offline)."""

from __future__ import annotations

import json
from pathlib import Path

def test_shadow_log_ready_and_unpriced_row(tmp_path, monkeypatch) -> None:
    from telemetry import shadow_evaluator

    shadow_path = tmp_path / "logs" / "shadow_executions.jsonl"
    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", shadow_path)

    shadow_evaluator.ensure_shadow_executions_log_ready()
    assert shadow_path.is_file()

    shadow_evaluator.log_shadow_execution(
        symbol="ZZZ",
        side="buy",
        proba=0.9,
        threshold=0.5,
        entry_price=None,
        source_event={"decision_outcome": "blocked", "blocked_reason": "max_positions_reached"},
        entry_price_source="unresolved",
    )
    rec = json.loads(shadow_path.read_text(encoding="utf-8").strip())
    assert rec["entry_price"] is None
    assert rec["shadow_take_profit_price"] is None
    assert rec["primary_blocked_reason"] == "max_positions_reached"


def test_displacement_lab_capacity_blocked_codes(tmp_path) -> None:
    from scripts.research.displacement_counterfactual_lab import _is_capacity_blocked_intent

    base = {
        "event_type": "trade_intent",
        "decision_outcome": "blocked",
        "symbol": "X",
        "score": 3.0,
    }
    assert _is_capacity_blocked_intent({**base, "blocked_reason": "max_positions_reached"})
    assert _is_capacity_blocked_intent({**base, "blocked_reason_code": "capacity_full"})
    assert _is_capacity_blocked_intent(
        {
            **base,
            "blocked_reason": "other",
            "intelligence_trace": {"final_decision": {"primary_reason": "max_positions_reached"}},
        }
    )
    assert not _is_capacity_blocked_intent({**base, "blocked_reason": "score_below_min"})


def test_rotated_run_jsonl_loads_from_dot_one(tmp_path) -> None:
    from scripts.research.displacement_counterfactual_lab import _load_max_positions_blocked

    logs = tmp_path / "logs"
    logs.mkdir(parents=True)
    intent = {
        "ts": "2024-06-05T15:00:05+00:00",
        "event_type": "trade_intent",
        "symbol": "CAND",
        "side": "buy",
        "score": 3.1,
        "decision_outcome": "blocked",
        "blocked_reason_code": "capacity_full",
    }
    (logs / "run.jsonl.1").write_text(json.dumps(intent) + "\n", encoding="utf-8")

    rows = _load_max_positions_blocked(logs / "run.jsonl")
    assert len(rows) == 1
    assert rows[0]["symbol"] == "CAND"


def test_concordance_loads_candidates_from_rotated_run(tmp_path) -> None:
    from scripts.research.shadow_challenger_concordance import _load_trade_intent_candidates

    logs = tmp_path / "logs"
    logs.mkdir(parents=True)
    intent = {
        "ts": "2024-06-05T15:30:02+00:00",
        "event_type": "trade_intent",
        "symbol": "SPY",
        "side": "buy",
        "score": 3.1,
        "decision_outcome": "blocked",
        "blocked_reason": "max_positions_reached",
        "challenger_ai_approved": True,
    }
    (logs / "run.jsonl.2").write_text(json.dumps(intent) + "\n", encoding="utf-8")

    cands = _load_trade_intent_candidates(logs / "run.jsonl")
    assert len(cands) == 1
    assert cands[0]["symbol"] == "SPY"
