"""V2 ML row densification lowers reported NaN fraction for gate telemetry."""
from __future__ import annotations

from telemetry import shadow_evaluator
from telemetry.vanguard_ml_runtime import v2_row_quality_metrics


def test_densify_lowers_nan_fraction_on_sparse_snapshot(monkeypatch):
    if shadow_evaluator._import_flattener() is None:
        return
    snap = {
        "symbol": "AMD",
        "composite_score": 5.3,
        "v2_score": 5.3,
        "entry_uw": {
            "flow_strength": 1.0,
            "darkpool_bias": 0.0,
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.0,
            "earnings_proximity": 999.0,
            "sector_alignment": 0.0,
            "regime_alignment": 0.25,
        },
        "components": {"flow": 2.5, "dark_pool": 0.02},
    }
    row = shadow_evaluator.build_vanguard_feature_map(
        symbol="AMD",
        side="buy",
        now_utc=None,
        feature_snapshot=snap,
        comps=snap["components"],
        cluster={},
        trade_id=None,
    )
    q = v2_row_quality_metrics(row)
    assert q.get("v2_row_nan_fraction", 1.0) < 0.10, q
