"""Alpha 11 ensemble funnel (dynamic floor + soft mult vs legacy series)."""
from __future__ import annotations


def test_resolve_dynamic_high_score_allows_weaker_flow(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_FLOW_SERIES_VETO", "0")
    monkeypatch.setenv("ALPHA11_DYNAMIC_FLOOR_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_MIN_FLOW_STRENGTH", "0.75")
    monkeypatch.setenv("REGIME_ENGINE_ENABLED", "0")
    monkeypatch.setenv("ALPHA11_DYNAMIC_SCORE_LO", "3.0")
    monkeypatch.setenv("ALPHA11_DYNAMIC_SCORE_HI", "6.5")
    monkeypatch.setenv("ALPHA11_DYNAMIC_FLOOR_SPAN", "0.20")
    from src.alpha11_gate import resolve_alpha11_entry_funnel

    meta = {"v2_uw_inputs": {"flow_strength": 0.60}}
    r = resolve_alpha11_entry_funnel(
        composite_score=7.0,
        composite_result=meta,
        composite_meta=meta,
        regime_state="TREND",
    )
    assert r.allowed is True
    assert r.policy == "dynamic_pass"
    assert r.notional_mult == 1.0
    assert r.flow_strength == 0.60


def test_resolve_soft_mult_when_flow_below_effective_floor(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_FLOW_SERIES_VETO", "0")
    monkeypatch.setenv("ALPHA11_DYNAMIC_FLOOR_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_MIN_FLOW_STRENGTH", "0.75")
    monkeypatch.setenv("REGIME_ENGINE_ENABLED", "0")
    from src.alpha11_gate import resolve_alpha11_entry_funnel

    meta = {"v2_uw_inputs": {"flow_strength": 0.50}}
    r = resolve_alpha11_entry_funnel(
        composite_score=4.0,
        composite_result=meta,
        composite_meta=meta,
        regime_state="TREND",
    )
    assert r.allowed is True
    assert r.policy == "dynamic_soft_scale"
    assert 0.25 <= r.notional_mult < 1.0
    assert r.flow_strength == 0.50


def test_resolve_catastrophic_blocks(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_FLOW_SERIES_VETO", "0")
    monkeypatch.setenv("ALPHA11_ABSOLUTE_FLOW_FLOOR", "0.22")
    monkeypatch.setenv("REGIME_ENGINE_ENABLED", "0")
    from src.alpha11_gate import resolve_alpha11_entry_funnel

    meta = {"v2_uw_inputs": {"flow_strength": 0.05}}
    r = resolve_alpha11_entry_funnel(
        composite_score=9.0,
        composite_result=meta,
        composite_meta=meta,
        regime_state="TREND",
    )
    assert r.allowed is False
    assert r.block_reason == "alpha11_flow_strength_catastrophic"


def test_check_gate_without_score_stays_strict_series(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_MIN_FLOW_STRENGTH", "0.90")
    monkeypatch.setenv("REGIME_ENGINE_ENABLED", "0")
    from src.alpha11_gate import check_alpha11_flow_strength_gate

    ok, reason, fs = check_alpha11_flow_strength_gate(
        symbol="TEST",
        composite_result={"v2_uw_inputs": {"flow_strength": 0.89}},
        composite_meta={},
        composite_score=None,
    )
    assert ok is False
    assert reason == "alpha11_flow_strength_below_gate"
    assert fs == 0.89
