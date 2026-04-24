from __future__ import annotations

import json


def test_shadow_execution_log_is_isolated_from_exit_attribution(tmp_path, monkeypatch) -> None:
    from telemetry import shadow_evaluator

    shadow_path = tmp_path / "logs" / "shadow_executions.jsonl"
    exit_path = tmp_path / "logs" / "exit_attribution.jsonl"
    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", shadow_path)

    shadow_evaluator.log_shadow_execution(
        symbol="AAPL",
        side="sell",
        proba=0.91,
        threshold=0.7,
        entry_price=100.0,
        source_event={"decision_outcome": "blocked", "blocked_reason": "primary_gate"},
    )

    assert shadow_path.is_file()
    assert not exit_path.exists()
    rec = json.loads(shadow_path.read_text(encoding="utf-8").strip())
    assert rec["event_type"] == "SHADOW_EXECUTION"
    assert rec["symbol"] == "AAPL"
    assert rec["side"] == "sell"
    assert rec["shadow_take_profit_price"] < rec["entry_price"]
    assert rec["shadow_stop_loss_price"] > rec["entry_price"]


def test_attach_shadow_telemetry_logs_challenger_when_primary_ignored(monkeypatch, tmp_path) -> None:
    from telemetry import shadow_evaluator

    calls = []
    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", tmp_path / "shadow_executions.jsonl")
    monkeypatch.setattr(shadow_evaluator, "shadow_chop_block_now", lambda: False)
    monkeypatch.setattr(shadow_evaluator, "build_vanguard_feature_map", lambda **_kwargs: {"entry_price": 42.0})
    monkeypatch.setattr(shadow_evaluator, "_load_booster_and_meta", lambda: (None, None, "missing"))
    monkeypatch.setattr(shadow_evaluator, "predict_challenger_probability", lambda **_kwargs: (0.88, 0.8, None))

    def fake_log_shadow_execution(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(shadow_evaluator, "log_shadow_execution", fake_log_shadow_execution)

    rec = {"event_type": "trade_intent", "decision_outcome": "blocked", "blocked_reason": "primary_gate"}
    shadow_evaluator.attach_shadow_telemetry(
        rec,
        symbol="AAPL",
        side="buy",
        feature_snapshot={},
        comps={},
        cluster={},
    )

    assert rec["challenger_ai_approved"] is True
    assert rec["challenger_shadow_proba"] == 0.88
    assert calls and calls[0]["symbol"] == "AAPL"
    assert calls[0]["entry_price"] == 42.0


def test_attach_shadow_telemetry_does_not_log_challenger_for_primary_entered(monkeypatch) -> None:
    from telemetry import shadow_evaluator

    calls = []
    monkeypatch.setattr(shadow_evaluator, "shadow_chop_block_now", lambda: False)
    monkeypatch.setattr(shadow_evaluator, "build_vanguard_feature_map", lambda **_kwargs: {"entry_price": 42.0})
    monkeypatch.setattr(shadow_evaluator, "_load_booster_and_meta", lambda: (None, None, "missing"))
    monkeypatch.setattr(shadow_evaluator, "predict_challenger_probability", lambda **_kwargs: (0.88, 0.8, None))
    monkeypatch.setattr(shadow_evaluator, "log_shadow_execution", lambda **kwargs: calls.append(kwargs))

    rec = {"event_type": "trade_intent", "decision_outcome": "entered"}
    shadow_evaluator.attach_shadow_telemetry(
        rec,
        symbol="AAPL",
        side="buy",
        feature_snapshot={},
        comps={},
        cluster={},
    )

    assert rec["challenger_ai_approved"] is True
    assert calls == []
