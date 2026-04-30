#!/usr/bin/env python3
"""Print v2_row_quality_metrics for a sparse XLF-like row (droplet smoke; no logs)."""
from __future__ import annotations

from telemetry import shadow_evaluator
from telemetry.vanguard_ml_runtime import v2_row_quality_metrics


def main() -> int:
    snap = {
        "symbol": "XLF",
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
        symbol="XLF",
        side="buy",
        now_utc=None,
        feature_snapshot=snap,
        comps=snap["components"],
        cluster={},
        trade_id=None,
    )
    print(v2_row_quality_metrics(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
