"""Unit tests for TNR + Schmitt (continuous regime)."""

import json
from pathlib import Path

import pytest

from src.regime.continuous_regime_classifier import (
    SchmittTnrAxis,
    calculate_trend_to_noise_ratio,
)
from src.regime.regime_execution_policy import (
    REGIME_EXECUTION_POLICIES,
    log_shadow_regime_execution_intent,
    resolve_regime_execution_policy,
)


def test_tnr_monotonic_high() -> None:
    tnr = calculate_trend_to_noise_ratio([100.0, 101.0, 102.0, 103.0], 4)
    assert tnr > 0.99


def test_tnr_choppy_low() -> None:
    tnr = calculate_trend_to_noise_ratio([100.0, 101.0, 100.0, 101.0, 100.0], 5)
    assert tnr < 0.3


def test_schmitt_tnr_axis_default_thresholds() -> None:
    s = SchmittTnrAxis()
    assert s.step(0.50) == "TREND"
    assert s.step(0.20) == "CHOP"
    assert s.step(0.30) == "CHOP"
    assert s.step(0.41) == "TREND"


def test_resolve_regime_execution_policy_matrix() -> None:
    assert resolve_regime_execution_policy("TREND").entry_style == "market_take"
    assert resolve_regime_execution_policy("TREND").sizing_mult == 1.0
    assert resolve_regime_execution_policy("CHOP").entry_style == "passive_bid_vwap"
    assert resolve_regime_execution_policy("CHOP").sizing_mult == 0.5
    assert resolve_regime_execution_policy("MACRO_DOWNTREND").entry_style == "short_or_deep_discount"
    assert "MACRO_DOWNTREND" in REGIME_EXECUTION_POLICIES


def test_shadow_log_chop_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("REGIME_POLICY_SHADOW", "1")
    from src.regime import regime_execution_policy as rep

    monkeypatch.setattr(rep, "_repo_logs_dir", lambda: tmp_path)
    log_shadow_regime_execution_intent(
        regime_state="CHOP",
        symbol="AAPL",
        side="buy",
        qty=10,
        correlation_id="cid-test",
        entry_score=3.5,
    )
    p = tmp_path / "unified_events.jsonl"
    assert p.exists()
    line = p.read_text(encoding="utf-8").strip().splitlines()[-1]
    rec = json.loads(line)
    assert rec["event_type"] == "regime_shadow_execution_intent"
    assert rec["shadow_entry_style"] == "passive_bid_vwap"
    assert rec["symbol"] == "AAPL"


def test_shadow_skips_when_not_chop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("REGIME_POLICY_SHADOW", "1")
    from src.regime import regime_execution_policy as rep

    monkeypatch.setattr(rep, "_repo_logs_dir", lambda: tmp_path)
    log_shadow_regime_execution_intent(regime_state="TREND", symbol="AAPL", side="buy", qty=1)
    p = tmp_path / "unified_events.jsonl"
    assert not p.exists()
