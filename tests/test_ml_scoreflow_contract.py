"""Strict ML scoreflow normalization + column contract."""
from __future__ import annotations

import math

from telemetry.ml_scoreflow_contract import (
    ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS,
    normalize_composite_components_for_ml,
)


def test_normalize_fills_missing_with_zero():
    n = normalize_composite_components_for_ml({"flow": 0.42, "whale": float("nan")})
    assert n["flow"] == 0.42
    assert n["whale"] == 0.0
    assert n["dark_pool"] == 0.0
    assert len(n) == len(ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS)


def test_normalize_non_dict_is_all_zeros():
    n = normalize_composite_components_for_ml(None)
    assert all(v == 0.0 for v in n.values())


def test_normalize_all_keys_finite():
    n = normalize_composite_components_for_ml({"flow": 1})
    s = sum(n.values())
    assert math.isfinite(s)
