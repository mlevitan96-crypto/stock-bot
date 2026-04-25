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
    assert rec.get("entry_price_source") == "unspecified"
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
    assert calls[0].get("entry_price_source") == "row:entry_price"


def test_attach_shadow_telemetry_logs_challenger_using_row_last_price_when_no_entry_price(
    monkeypatch, tmp_path
) -> None:
    """Blocked path: no broker entry_price in ML row; shadow tape must still append using quote fallback."""
    from telemetry import shadow_evaluator

    calls = []
    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", tmp_path / "shadow_executions.jsonl")
    monkeypatch.setattr(shadow_evaluator, "shadow_chop_block_now", lambda: False)
    monkeypatch.setattr(
        shadow_evaluator,
        "build_vanguard_feature_map",
        lambda **_kwargs: {"last_price": 155.25},
    )
    monkeypatch.setattr(shadow_evaluator, "_load_booster_and_meta", lambda: (None, None, "missing"))
    monkeypatch.setattr(shadow_evaluator, "predict_challenger_probability", lambda **_kwargs: (0.88, 0.8, None))

    monkeypatch.setattr(shadow_evaluator, "log_shadow_execution", lambda **kwargs: calls.append(kwargs))

    rec = {"event_type": "trade_intent", "decision_outcome": "blocked", "blocked_reason": "capacity_full"}
    shadow_evaluator.attach_shadow_telemetry(
        rec,
        symbol="MSFT",
        side="buy",
        feature_snapshot={},
        comps={},
        cluster={},
    )

    assert rec["challenger_ai_approved"] is True
    assert calls and calls[0]["entry_price"] == 155.25
    assert calls[0].get("entry_price_source") == "row:last_price"


def test_attach_shadow_telemetry_logs_challenger_using_feature_snapshot_when_row_has_no_quotes(
    monkeypatch, tmp_path
) -> None:
    from telemetry import shadow_evaluator

    calls = []
    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", tmp_path / "shadow_executions.jsonl")
    monkeypatch.setattr(shadow_evaluator, "shadow_chop_block_now", lambda: False)
    monkeypatch.setattr(shadow_evaluator, "build_vanguard_feature_map", lambda **_kwargs: {})
    monkeypatch.setattr(shadow_evaluator, "_load_booster_and_meta", lambda: (None, None, "missing"))
    monkeypatch.setattr(shadow_evaluator, "predict_challenger_probability", lambda **_kwargs: (0.91, 0.5, None))
    monkeypatch.setattr(shadow_evaluator, "log_shadow_execution", lambda **kwargs: calls.append(kwargs))

    fs = {"close": 88.5, "symbol": "XOM"}
    rec = {"event_type": "trade_intent", "decision_outcome": "blocked", "blocked_reason": "score_below_min"}
    shadow_evaluator.attach_shadow_telemetry(
        rec,
        symbol="XOM",
        side="buy",
        feature_snapshot=fs,
        comps={},
        cluster={},
    )

    assert calls and calls[0]["entry_price"] == 88.5
    assert calls[0].get("entry_price_source") == "feature_snapshot:close"


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
