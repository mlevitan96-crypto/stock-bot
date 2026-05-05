"""premarket_intel merge must not clobber live uw_flow_cache flow_strength with placeholder 0.0."""

from __future__ import annotations


def test_merge_uw_intel_record_keeps_positive_flow_when_premarket_sends_zero():
    from uw_composite_v2 import _merge_uw_intel_record

    fb = {"flow_strength": 0.85, "sentiment": "BULLISH"}
    partial = {"flow_strength": 0.0, "darkpool_bias": 0.1}
    out = _merge_uw_intel_record(partial, fb)
    assert out["flow_strength"] == 0.85
    assert out["darkpool_bias"] == 0.1
    assert out["sentiment"] == "BULLISH"


def test_merge_uw_intel_record_applies_nonzero_flow_from_premarket():
    from uw_composite_v2 import _merge_uw_intel_record

    fb = {"flow_strength": 0.2, "sentiment": "NEUTRAL"}
    partial = {"flow_strength": 0.9}
    out = _merge_uw_intel_record(partial, fb)
    assert out["flow_strength"] == 0.9


def test_merge_uw_intel_record_zero_when_fallback_also_zero():
    from uw_composite_v2 import _merge_uw_intel_record

    fb = {"flow_strength": 0.0}
    partial = {"flow_strength": 0.0}
    out = _merge_uw_intel_record(partial, fb)
    assert out["flow_strength"] == 0.0
