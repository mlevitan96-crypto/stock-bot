"""
Offensive pivot — Inversion Engine (optional).

When base entry is **buy** (long) with high composite conviction but the paper ML gate regressor
predicts strongly negative EOD-style return (chop-trap proxy), optionally **invert** to **sell**
(short) instead of blocking.

**Safety:** Disabled unless ``ALPACA_INVERSION_ENGINE_ENABLED=1``. Requires shortable asset check
caller-side after flip. Missing joblib / inference errors → no inversion.

Env:
  ALPACA_INVERSION_ENGINE_ENABLED — ``1`` / ``true`` / ``yes`` / ``on`` to enable
  ALPACA_INVERSION_ML_PRED_MAX — prediction at or below this triggers invert on long (default ``-0.01``)
  ALPACA_INVERSION_MIN_ENTRY_SCORE — minimum entry_score to consider inversion (default ``2.0``)
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple


def try_invert_entry_side(
    *,
    executor: Any,
    symbol: str,
    side: str,
    qty: Any,
    entry_score: float,
    entry_components: Optional[Dict[str, Any]],
    market_regime: str,
    ml_gate_feature_snapshot: Optional[Dict[str, Any]] = None,
    ml_gate_cluster: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Returns (possibly_flipped_side, meta_dict_or_none).

    Only long→short is implemented for the Commander path (fade long chop-trap).
    """
    flag = (os.environ.get("ALPACA_INVERSION_ENGINE_ENABLED") or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return str(side or "").strip().lower(), None

    s = str(side or "").strip().lower()
    if s not in ("buy", "long"):
        return s, None

    try:
        min_score = float(os.environ.get("ALPACA_INVERSION_MIN_ENTRY_SCORE", "2.0") or "2.0")
    except (TypeError, ValueError):
        min_score = 2.0
    try:
        pred_max = float(os.environ.get("ALPACA_INVERSION_ML_PRED_MAX", "-0.01") or "-0.01")
    except (TypeError, ValueError):
        pred_max = -0.01

    if float(entry_score or 0.0) < min_score:
        return "buy", None

    try:
        from src.ml.alpaca_shadow_scorer import predict_expected_eod_return

        api = getattr(executor, "api", None)
        comps = dict(entry_components) if isinstance(entry_components, dict) else {}
        yhat = predict_expected_eod_return(
            symbol=str(symbol),
            entry_components=comps,
            entry_score=float(entry_score),
            market_regime=str(market_regime or ""),
            api=api,
        )
    except Exception:
        return "buy", None

    if yhat is None:
        return "buy", None

    if float(yhat) > pred_max:
        return "buy", None

    meta = {
        "inversion_engine": True,
        "prior_side": "buy",
        "new_side": "sell",
        "ml_expected_eod_return": float(yhat),
        "entry_score": float(entry_score),
        "pred_threshold_max": float(pred_max),
        "min_entry_score": float(min_score),
    }
    return "sell", meta
