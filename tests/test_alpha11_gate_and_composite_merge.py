"""Alpha 11 flow gate + composite_components_at_entry merge for exit telemetry."""
from __future__ import annotations

def test_merge_composite_components_at_entry_prefers_v2_components():
    from src.exit.exit_attribution import merge_composite_components_at_entry

    meta = {
        "components": {"flow_count": 1.0, "market_tide": 0.1},
        "v2": {
            "components": {"flow": 0.5, "market_tide": 0.3, "greeks_gamma": 0.2},
            "feature_snapshot": {"legacy": 9.0},
        },
    }
    m = merge_composite_components_at_entry(meta)
    assert m["flow_count"] == 1.0
    assert m["legacy"] == 9.0
    assert m["flow"] == 0.5
    assert m["market_tide"] == 0.3
    assert m["greeks_gamma"] == 0.2


def test_merge_composite_components_at_entry_top_level_only():
    from src.exit.exit_attribution import merge_composite_components_at_entry

    meta = {"components": {"greeks_gamma": 0.15}, "v2": {}}
    m = merge_composite_components_at_entry(meta)
    assert m["greeks_gamma"] == 0.15


def test_alpha11_gate_blocks_below_floor(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_MIN_FLOW_STRENGTH", "0.985")
    from src.alpha11_gate import check_alpha11_flow_strength_gate

    ok, reason, fs = check_alpha11_flow_strength_gate(
        symbol="TEST",
        composite_result={"v2_uw_inputs": {"flow_strength": 0.98}},
        composite_meta={},
    )
    assert ok is False
    assert reason == "alpha11_flow_strength_below_gate"
    assert fs == 0.98


def test_alpha11_gate_allows_at_floor(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    monkeypatch.setenv("ALPHA11_MIN_FLOW_STRENGTH", "0.985")
    from src.alpha11_gate import check_alpha11_flow_strength_gate

    ok, reason, fs = check_alpha11_flow_strength_gate(
        symbol="TEST",
        composite_result=None,
        composite_meta={"v2_uw_inputs": {"flow_strength": 0.985}},
    )
    assert ok is True
    assert reason is None
    assert fs == 0.985


def test_alpha11_gate_skips_when_missing(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "1")
    from src.alpha11_gate import check_alpha11_flow_strength_gate

    ok, reason, fs = check_alpha11_flow_strength_gate(
        symbol="TEST",
        composite_result={"score": 3.0},
        composite_meta={},
    )
    assert ok is True
    assert reason == "alpha11_flow_skipped_missing_flow_strength"
    assert fs is None


def test_alpha11_gate_disabled(monkeypatch):
    monkeypatch.setenv("ALPHA11_FLOW_GATE_ENABLED", "0")
    from src.alpha11_gate import check_alpha11_flow_strength_gate

    ok, reason, fs = check_alpha11_flow_strength_gate(
        symbol="TEST",
        composite_result={"v2_uw_inputs": {"flow_strength": 0.1}},
        composite_meta={},
    )
    assert ok is True
    assert reason is None
    assert fs is None
