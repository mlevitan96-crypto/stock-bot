"""Smoke test: live_whale model loads and returns a bounded probability."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_MODEL = _REPO / "models" / "live_whale_v1.json"


def test_live_whale_engine_load_and_predict():
    pytest.importorskip("xgboost")
    if not _MODEL.is_file():
        pytest.skip(f"missing model: {_MODEL}")

    from src.ml.inference_engine import LiveModelEngine, build_live_whale_feature_dict

    eng = LiveModelEngine(_MODEL)
    assert eng.available, eng.load_error

    feats = build_live_whale_feature_dict(
        {"flow": 0.5, "greeks_gamma": 0.1},
        entry_uw={"flow_strength": 0.3, "darkpool_bias": 0.0, "sentiment_score": 0.2, "earnings_proximity": 1.0},
    )
    p = eng.predict_proba_sync(feats)
    assert p is not None
    assert 0.0 <= p <= 1.0


def test_predict_async_matches_sync():
    pytest.importorskip("xgboost")
    if not _MODEL.is_file():
        pytest.skip(f"missing model: {_MODEL}")

    from src.ml.inference_engine import LiveModelEngine, build_live_whale_feature_dict

    eng = LiveModelEngine(_MODEL)
    if not eng.available:
        pytest.skip(eng.load_error or "engine unavailable")

    feats = build_live_whale_feature_dict({}, entry_uw=None)
    a = asyncio.run(eng.predict_async(feats))
    b = eng.predict_proba_sync(feats)
    assert a is not None and b is not None
    assert abs(a - b) < 1e-9
