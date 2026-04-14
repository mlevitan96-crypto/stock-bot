"""Alpha 10 inference: bundle load and row vector shape."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE = REPO_ROOT / "models" / "alpha10_rf_mfe.joblib"


@pytest.mark.skipif(not BUNDLE.is_file(), reason="Alpha10 bundle not present")
def test_predict_mfe_loads_and_returns_finite() -> None:
    from src.ml.alpha10_inference import build_entry_telemetry_row, clear_bundle_cache, predict_mfe

    clear_bundle_cache()
    telem = build_entry_telemetry_row(
        symbol="SPY",
        side="buy",
        score=2.5,
        comps={"flow": 1.0, "regime": 0.5},
        cluster={},
        market_context={},
        regime_posture={"regime_confidence": 0.5},
        symbol_risk={},
        api=None,
    )
    y = predict_mfe(telem, bundle=None)
    assert y == y and abs(y) < 1e6  # finite, not absurd
