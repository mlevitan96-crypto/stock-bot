from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading.displacement_policy import evaluate_displacement


def test_fast_track_skips_min_hold_when_high_conviction() -> None:
    now = datetime.now(timezone.utc)
    entry_ts = now - timedelta(minutes=5)
    current = {
        "symbol": "AAA",
        "entry_ts": entry_ts,
        "current_score": 3.1,
        "pnl_pct": 0.001,
        "uw_flow_strength": 0.5,
        "dark_pool_bias": 0.1,
    }
    challenger = {"symbol": "BBB", "score": 4.5, "new_signal_score": 4.5, "uw_flow_strength": 0.9, "dark_pool_bias": 0.2}
    ctx = {"regime_label": "bull", "posture": "long"}
    overrides = {
        "DISPLACEMENT_MIN_HOLD_SECONDS": 3600,
        "DISPLACEMENT_MIN_DELTA_SCORE": 0.75,
        "DISPLACEMENT_REQUIRE_THESIS_DOMINANCE": True,
        "DISPLACEMENT_FASTTRACK_MIN_CHALLENGER_SCORE": 4.2,
        "DISPLACEMENT_FASTTRACK_MIN_DELTA_SCORE": 1.25,
    }
    ok, reason, _diag = evaluate_displacement(current, challenger, ctx, config_overrides=overrides)
    assert ok
    assert reason == "displacement_allowed"


def test_no_fast_track_when_delta_too_small() -> None:
    now = datetime.now(timezone.utc)
    entry_ts = now - timedelta(minutes=5)
    current = {
        "symbol": "AAA",
        "entry_ts": entry_ts,
        "current_score": 3.5,
        "pnl_pct": 0.001,
        "uw_flow_strength": 0.5,
        "dark_pool_bias": 0.1,
    }
    challenger = {"symbol": "BBB", "score": 4.4, "new_signal_score": 4.4, "uw_flow_strength": 0.9, "dark_pool_bias": 0.2}
    ctx = {"regime_label": "bull", "posture": "long"}
    overrides = {
        "DISPLACEMENT_MIN_HOLD_SECONDS": 3600,
        "DISPLACEMENT_MIN_DELTA_SCORE": 0.75,
        "DISPLACEMENT_REQUIRE_THESIS_DOMINANCE": True,
        "DISPLACEMENT_FASTTRACK_MIN_CHALLENGER_SCORE": 4.2,
        "DISPLACEMENT_FASTTRACK_MIN_DELTA_SCORE": 1.25,
    }
    ok, reason, _diag = evaluate_displacement(current, challenger, ctx, config_overrides=overrides)
    assert not ok
    assert reason == "displacement_min_hold"
