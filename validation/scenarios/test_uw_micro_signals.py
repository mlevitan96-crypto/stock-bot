"""
Unit tests for UW micro-signal extraction (Phase 2).
Ensures extract_flow_micro_signals, extract_dark_pool_micro_signals,
extract_insider_micro_signals, extract_uw_micro_signals return valid components.
Phase 2 contract: no opaque UW score; sum(UW contributions) = UW portion of composite.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_extract_flow_micro_signals_empty():
    from src.uw.uw_micro_signals import extract_flow_micro_signals
    out = extract_flow_micro_signals([])
    assert len(out) >= 1
    assert out[0].get("signal_id") == "uw.flow.aggregate"
    assert out[0].get("missing_reason") == "no_flow_trades"
    assert out[0].get("contribution_to_score") == 0.0
    assert "missing" in (out[0].get("quality_flags") or [])


def test_extract_flow_micro_signals_single_trade():
    from src.uw.uw_micro_signals import extract_flow_micro_signals
    trades = [
        {
            "premium_usd": 500_000,
            "flow_type": "sweep",
            "direction": "bullish",
            "flow_conv": 0.8,
            "flow_magnitude": "HIGH",
            "volume": 100,
            "open_interest": 500,
        }
    ]
    out = extract_flow_micro_signals(trades)
    assert len(out) >= 5
    signal_ids = [c.get("signal_id") or c.get("name") for c in out]
    assert "uw.flow.premium" in signal_ids
    assert "uw.flow.conviction" in signal_ids
    total_contrib = sum(c.get("contribution_to_score", 0) for c in out)
    assert total_contrib >= 0


def test_extract_dark_pool_micro_signals_empty():
    from src.uw.uw_micro_signals import extract_dark_pool_micro_signals
    out = extract_dark_pool_micro_signals({})
    assert len(out) >= 1
    assert out[0].get("signal_id") == "uw.dark_pool.aggregate"
    assert out[0].get("missing_reason") == "no_dark_pool_data"


def test_extract_dark_pool_micro_signals_with_data():
    from src.uw.uw_micro_signals import extract_dark_pool_micro_signals
    dp = {
        "total_notional_1h": 1_000_000,
        "lit_volume": 100,
        "off_lit_volume": 400,
        "side": "buy",
    }
    out = extract_dark_pool_micro_signals(dp)
    assert len(out) >= 2
    assert any(c.get("signal_id") == "uw.dark_pool.notional" for c in out)


def test_extract_insider_micro_signals_empty():
    from src.uw.uw_micro_signals import extract_insider_micro_signals
    out = extract_insider_micro_signals({})
    assert len(out) >= 1
    assert out[0].get("signal_id") == "uw.insider.aggregate"
    assert out[0].get("missing_reason") == "no_insider_data"


def test_extract_insider_micro_signals_with_data():
    from src.uw.uw_micro_signals import extract_insider_micro_signals
    ins = {"net_buys": 5, "net_sells": 1, "total_usd": 2e6, "sentiment": "BULLISH", "conviction_modifier": 0.1}
    out = extract_insider_micro_signals(ins)
    assert len(out) >= 2
    assert any(c.get("signal_id") == "uw.insider.activity" for c in out)


def test_extract_uw_micro_signals_full():
    from src.uw.uw_micro_signals import extract_uw_micro_signals
    enriched = {
        "flow_trades": [
            {"premium_usd": 200_000, "flow_type": "sweep", "direction": "bullish", "flow_conv": 0.7}
        ],
        "dark_pool": {"total_notional_1h": 500_000, "side": "buy"},
        "insider": {"net_buys": 3, "net_sells": 0, "sentiment": "BULLISH"},
    }
    components, total = extract_uw_micro_signals(enriched)
    assert len(components) >= 5
    assert isinstance(total, (int, float))
    assert abs(total - sum(c.get("contribution_to_score", 0) for c in components)) < 1e-9
    # No single opaque UW score: only uw.* signal_ids
    for c in components:
        assert c.get("signal_id", "").startswith("uw.")


def test_scale_uw_components_to_target():
    from src.uw.uw_micro_signals import extract_uw_micro_signals, scale_uw_components_to_target
    enriched = {"flow_trades": [{"premium_usd": 100_000, "flow_type": "sweep", "direction": "bullish", "flow_conv": 0.6}]}
    components, raw_total = extract_uw_micro_signals(enriched)
    target = 2.0
    scaled = scale_uw_components_to_target(components, target)
    assert len(scaled) == len(components)
    scaled_sum = sum(c.get("contribution_to_score", 0) for c in scaled)
    assert abs(scaled_sum - target) < 1e-6


def test_composite_emits_attribution_components_no_opaque_uw():
    """Phase 2: Composite must emit attribution_components; no single UW score (only uw.* micro-signals)."""
    import uw_composite_v2
    enriched = {
        "sentiment": "BULLISH",
        "conviction": 0.6,
        "trade_count": 5,
        "dark_pool": {"total_notional_1h": 500_000, "side": "buy"},
        "insider": {"net_buys": 2, "net_sells": 0, "sentiment": "BULLISH"},
        "flow_trades": [{"premium_usd": 200_000, "flow_type": "sweep", "direction": "bullish", "flow_conv": 0.6}],
        "iv_term_skew": 0.05,
        "smile_slope": 0.02,
        "toxicity": 0.2,
        "freshness": 1.0,
    }
    result = uw_composite_v2.compute_composite_score_v2(
        "TEST", enriched, "NEUTRAL", use_adaptive_weights=False
    )
    assert result is not None
    ac = result.get("attribution_components") or []
    assert len(ac) > 0, "attribution_components must be present"
    signal_ids = [c.get("signal_id") or c.get("name") for c in ac]
    # No opaque UW score: no single "flow", "dark_pool", "insider" from UW
    assert "flow" not in signal_ids or any(s.startswith("uw.flow.") for s in signal_ids), "UW must be decomposed"
    assert "dark_pool" not in signal_ids or any(s.startswith("uw.dark_pool.") for s in signal_ids)
    assert "insider" not in signal_ids or any(s.startswith("uw.insider.") for s in signal_ids)
    # At least one uw.* component when UW data present
    uw_signal_ids = [s for s in signal_ids if str(s).startswith("uw.")]
    assert len(uw_signal_ids) > 0, "must have uw.* micro-signals"


def test_composite_attribution_sum_equals_score():
    """Phase 2: composite_score == sum(attribution_components.contribution_to_score)."""
    import uw_composite_v2
    enriched = {
        "sentiment": "BULLISH",
        "conviction": 0.5,
        "trade_count": 3,
        "dark_pool": {},
        "insider": {},
        "flow_trades": [{"premium_usd": 100_000, "flow_type": "singleleg", "direction": "bullish", "flow_conv": 0.5}],
        "iv_term_skew": 0.0,
        "smile_slope": 0.0,
        "toxicity": 0.0,
        "freshness": 1.0,
    }
    result = uw_composite_v2.compute_composite_score_v2(
        "TEST", enriched, "NEUTRAL", use_adaptive_weights=False
    )
    assert result is not None
    score = float(result.get("score") or 0.0)
    ac = result.get("attribution_components") or []
    total = sum(float(c.get("contribution_to_score") or 0.0) for c in ac)
    assert abs(total - score) < 1e-4, f"sum(attribution_components)={total} != score={score}"


def test_schema_contract_component_has_signal_id_and_source():
    from src.uw.uw_micro_signals import extract_flow_micro_signals
    trades = [{"premium_usd": 100_000, "flow_type": "singleleg", "direction": "bullish", "flow_conv": 0.5}]
    out = extract_flow_micro_signals(trades)
    for c in out:
        assert "signal_id" in c
        assert c["signal_id"].startswith("uw.")
        assert "name" in c or "signal_id" in c
        assert "source" in c
        assert "contribution_to_score" in c
        assert c["source"] == "uw"
        assert "quality_flags" in c


def test_composite_phase3_no_opaque_components():
    """Phase 3: Every attribution component must have signal_id and source (no opaque components)."""
    import uw_composite_v2
    enriched = {
        "sentiment": "BULLISH",
        "conviction": 0.5,
        "trade_count": 3,
        "dark_pool": {},
        "insider": {},
        "flow_trades": [{"premium_usd": 100_000, "flow_type": "singleleg", "direction": "bullish", "flow_conv": 0.5}],
        "iv_term_skew": 0.0,
        "smile_slope": 0.0,
        "toxicity": 0.0,
        "freshness": 1.0,
    }
    result = uw_composite_v2.compute_composite_score_v2(
        "TEST", enriched, "NEUTRAL", use_adaptive_weights=False
    )
    ac = result.get("attribution_components") or []
    for c in ac:
        assert "signal_id" in c, f"component missing signal_id: {c}"
        assert "source" in c, f"component missing source: {c}"
        assert c.get("source") in ("uw", "internal", "derived"), f"invalid source: {c.get('source')}"
        assert "contribution_to_score" in c, f"component missing contribution_to_score: {c}"


def test_composite_phase3_sum_equals_score_after_v2():
    """Phase 3: sum(attribution_components) == score when v2 path is used (invariant)."""
    import uw_composite_v2
    enriched = {
        "sentiment": "BULLISH",
        "conviction": 0.6,
        "trade_count": 5,
        "dark_pool": {"total_notional_1h": 500_000, "side": "buy"},
        "insider": {"net_buys": 2, "net_sells": 0, "sentiment": "BULLISH"},
        "flow_trades": [{"premium_usd": 200_000, "flow_type": "sweep", "direction": "bullish", "flow_conv": 0.6}],
        "iv_term_skew": 0.05,
        "smile_slope": 0.02,
        "toxicity": 0.2,
        "freshness": 1.0,
    }
    result = uw_composite_v2.compute_composite_score_v2(
        "TEST", enriched, "NEUTRAL", use_adaptive_weights=False
    )
    score = float(result.get("score") or 0.0)
    ac = result.get("attribution_components") or []
    total = sum(float(c.get("contribution_to_score") or 0.0) for c in ac)
    assert abs(total - score) < 1e-3, f"sum(attribution_components)={total} != score={score}"
    # v2 components present
    v2_ids = [c.get("signal_id") for c in ac if str(c.get("signal_id", "")).startswith("internal.v2_")]
    assert len(v2_ids) >= 1, "v2 path must emit internal.v2_* components"
