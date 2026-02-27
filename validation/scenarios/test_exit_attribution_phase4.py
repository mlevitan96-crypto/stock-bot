"""
Phase 4 exit attribution tests.
- exit_score_v2 returns (score, components, reason, attribution_components, exit_reason_code)
- exit_score == sum(attribution_components.contribution_to_score)
- No opaque exit components (every component has signal_id with "exit_" prefix, source)
- build_exit_attribution_record accepts and stores attribution_components, decision_id, exit_reason_code
- exit_quality_metrics module returns expected shape
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_exit_score_v2_returns_attribution_and_reason_code():
    from src.exit.exit_score_v2 import compute_exit_score_v2
    s, comps, reason, ac, code = compute_exit_score_v2(
        symbol="T",
        direction="bullish",
        entry_v2_score=5.0,
        now_v2_score=2.0,
        entry_uw_inputs={"flow_strength": 0.7, "darkpool_bias": 0.1, "sentiment": "BULLISH"},
        now_uw_inputs={"flow_strength": 0.2, "darkpool_bias": 0.0, "sentiment": "NEUTRAL"},
        entry_regime="NEUTRAL",
        now_regime="NEUTRAL",
        entry_sector="TECH",
        now_sector="TECH",
        realized_vol_20d=0.5,
        thesis_flags={},
    )
    assert isinstance(s, (int, float))
    assert isinstance(comps, dict)
    assert isinstance(reason, str)
    assert isinstance(ac, list)
    assert isinstance(code, str)
    assert len(ac) >= 1
    assert code in ("hold", "intel_deterioration", "stop", "replacement", "profit", "other")


def test_exit_attribution_sum_equals_score():
    from src.exit.exit_score_v2 import compute_exit_score_v2
    s, comps, reason, ac, code = compute_exit_score_v2(
        symbol="T",
        direction="bullish",
        entry_v2_score=4.0,
        now_v2_score=1.5,
        entry_uw_inputs={"flow_strength": 0.6, "darkpool_bias": 0.0, "sentiment": "BULLISH"},
        now_uw_inputs={"flow_strength": 0.2, "darkpool_bias": 0.0, "sentiment": "NEUTRAL"},
        entry_regime="NEUTRAL",
        now_regime="NEUTRAL",
        entry_sector="TECH",
        now_sector="TECH",
        realized_vol_20d=0.4,
        thesis_flags={"thesis_invalidated": True},
    )
    total = sum(float(c.get("contribution_to_score") or 0.0) for c in ac)
    assert abs(total - s) < 1e-3, f"sum(attribution_components)={total} != exit_score={s}"


def test_exit_attribution_no_opaque_components():
    from src.exit.exit_score_v2 import compute_exit_score_v2
    _, _, _, ac, _ = compute_exit_score_v2(
        symbol="T",
        direction="bullish",
        entry_v2_score=3.0,
        now_v2_score=2.0,
        entry_uw_inputs={},
        now_uw_inputs={},
        entry_regime="NEUTRAL",
        now_regime="NEUTRAL",
        entry_sector="UNKNOWN",
        now_sector="UNKNOWN",
        thesis_flags={},
    )
    for c in ac:
        assert "signal_id" in c, c
        sid = c.get("signal_id", "")
        assert sid.startswith("exit_"), f"exit attribution signal_id must have 'exit_' prefix, got {sid!r}"
        assert c.get("source") == "exit", c
        assert "contribution_to_score" in c, c


def test_build_exit_attribution_record_phase4_fields():
    from src.exit.exit_attribution import build_exit_attribution_record, ATTRIBUTION_SCHEMA_VERSION
    rec = build_exit_attribution_record(
        symbol="AAPL",
        entry_timestamp="2026-02-17T14:00:00Z",
        exit_reason="profit",
        pnl=50.0,
        pnl_pct=0.5,
        entry_price=100.0,
        exit_price=100.5,
        qty=10,
        time_in_trade_minutes=60.0,
        entry_uw={},
        exit_uw={},
        entry_regime="NEUTRAL",
        exit_regime="NEUTRAL",
        entry_sector_profile={},
        exit_sector_profile={},
        score_deterioration=0.1,
        relative_strength_deterioration=0.0,
        v2_exit_score=0.6,
        v2_exit_components={"score_deterioration": 0.1},
        attribution_components=[{"signal_id": "exit_score_deterioration", "source": "exit", "contribution_to_score": 0.025}],
        decision_id="dec_AAPL_2026-02-17T15-00-00Z",
        exit_reason_code="profit",
        attribution_schema_version=ATTRIBUTION_SCHEMA_VERSION,
        exit_quality_metrics={"mfe": 1.0, "mae": None, "time_in_trade_sec": 3600, "profit_giveback": 0.5, "exit_efficiency": {"saved_loss": True, "left_money": False}},
    )
    assert rec.get("attribution_components") is not None
    assert rec.get("decision_id") == "dec_AAPL_2026-02-17T15-00-00Z"
    assert rec.get("exit_reason_code") == "profit"
    assert rec.get("attribution_schema_version") == ATTRIBUTION_SCHEMA_VERSION
    assert "exit_quality_metrics" in rec
    assert rec["exit_quality_metrics"].get("mfe") == 1.0
    assert rec["exit_quality_metrics"].get("exit_efficiency", {}).get("saved_loss") is True


def test_exit_quality_metrics_shape():
    from src.exit.exit_quality_metrics import compute_exit_quality_metrics
    from datetime import datetime, timezone
    entry_ts = datetime(2026, 2, 17, 14, 0, 0, tzinfo=timezone.utc)
    exit_ts = datetime(2026, 2, 17, 15, 0, 0, tzinfo=timezone.utc)
    q = compute_exit_quality_metrics(
        entry_price=100.0,
        exit_price=101.0,
        entry_ts=entry_ts,
        exit_ts=exit_ts,
        high_water_price=102.0,
        qty=10,
        side="long",
    )
    assert "mfe" in q
    assert "mae" in q
    assert "time_in_trade_sec" in q
    assert "profit_giveback" in q
    assert "exit_efficiency" in q
    assert "saved_loss" in q["exit_efficiency"]
    assert "left_money" in q["exit_efficiency"]
    assert q.get("time_in_trade_sec") == 3600.0
    assert q.get("mfe") == 2.0  # high_water 102 - entry 100
    assert q.get("profit_giveback") is not None
