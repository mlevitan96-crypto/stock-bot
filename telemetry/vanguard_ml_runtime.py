"""
V2 live gate + V3 shadow inference (XGBoost boosters + threshold JSON).

Keeps heavy imports lazy; safe defaults when artifacts are missing.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]

_V2_MODEL = REPO_ROOT / "models" / "vanguard_v2_profit_agent.json"
_V2_META = REPO_ROOT / "models" / "vanguard_v2_profit_agent_features.json"
_V2_THR_JSON = REPO_ROOT / "models" / "vanguard_v2_profit_agent_threshold.json"
_DEFAULT_V2_THR = 0.3876

_V3_MODEL = REPO_ROOT / "models" / "vanguard_v3_hunter_agent.json"
_V3_FEATURES = REPO_ROOT / "models" / "vanguard_v3_hunter_features.json"
_V3_THR_JSON = REPO_ROOT / "models" / "vanguard_v3_hunter_threshold.json"

_CACHE: Dict[str, Any] = {"v2": None, "v2_err": None, "v3": None, "v3_err": None}


def _symbol_code(sym: str, classes: List[str]) -> float:
    if not classes:
        return float("nan")
    s = str(sym or "").upper().strip()
    try:
        return float(classes.index(s)) if s in classes else float("nan")
    except Exception:
        return float("nan")


def _side_code(side: str, classes: List[str]) -> float:
    if not classes:
        return float("nan")
    s = str(side or "").upper().strip()
    if s in ("BUY", "LONG"):
        s2 = "LONG"
    elif s in ("SELL", "SHORT"):
        s2 = "SHORT"
    else:
        s2 = s
    try:
        return float(classes.index(s2)) if s2 in classes else float("nan")
    except Exception:
        return float("nan")


def default_v2_threshold() -> float:
    try:
        if _V2_THR_JSON.is_file():
            o = json.loads(_V2_THR_JSON.read_text(encoding="utf-8"))
            if isinstance(o, dict) and o.get("holdout_probability_threshold") is not None:
                return float(o["holdout_probability_threshold"])
    except Exception:
        pass
    return float(_DEFAULT_V2_THR)


def default_v3_threshold() -> float:
    try:
        if _V3_THR_JSON.is_file():
            o = json.loads(_V3_THR_JSON.read_text(encoding="utf-8"))
            if isinstance(o, dict) and o.get("holdout_probability_threshold") is not None:
                return float(o["holdout_probability_threshold"])
    except Exception:
        pass
    return 0.0


def _load_pair(model_path: Path, meta_path: Path, key: str) -> Tuple[Optional[Any], Optional[dict], Optional[str]]:
    err_key = f"{key}_err"
    if _CACHE.get(err_key):
        return None, None, str(_CACHE.get(err_key))
    cached = _CACHE.get(key)
    if isinstance(cached, tuple) and len(cached) == 3:
        return cached  # type: ignore[return-value]
    if not model_path.is_file() or not meta_path.is_file():
        e = f"missing_model_or_meta model={model_path} meta={meta_path}"
        _CACHE[err_key] = e
        return None, None, e
    try:
        import xgboost as xgb  # type: ignore

        bst = xgb.Booster()
        bst.load_model(str(model_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        tup = (bst, meta, None)
        _CACHE[key] = tup
        _CACHE.pop(err_key, None)
        return tup
    except Exception as e:  # pragma: no cover
        _CACHE[err_key] = str(e)
        return None, None, str(e)


def _vec_for_order(
    feature_order: List[str],
    row: Dict[str, float],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
) -> "np.ndarray":
    vec: Dict[str, float] = {}
    for k in feature_order:
        vec[k] = float(row.get(k, float("nan")))
    vec["symbol_enc"] = _symbol_code(symbol, symbol_classes)
    vec["side_enc"] = _side_code(side, side_classes)
    hraw = float(vec.get("hour_of_day", float("nan")))
    if (not math.isfinite(hraw)) and "hour_of_day" in feature_order:
        try:
            from zoneinfo import ZoneInfo

            et = ZoneInfo("America/New_York")
            vec["hour_of_day"] = float(datetime.now(et).hour)
        except Exception:
            vec["hour_of_day"] = float(datetime.now(timezone.utc).hour)
    return np.array(
        [float(vec.get(f, float("nan"))) for f in feature_order],
        dtype=np.float32,
    ).reshape(1, -1)


def predict_v2_probability(
    feature_order: List[str],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
    row: Dict[str, float],
) -> Tuple[Optional[float], Optional[str]]:
    bst, meta, err = _load_pair(_V2_MODEL, _V2_META, "v2")
    if bst is None or err:
        return None, err
    try:
        import xgboost as xgb  # type: ignore

        x = _vec_for_order(feature_order, row, symbol, side, symbol_classes, side_classes)
        d = xgb.DMatrix(x, feature_names=feature_order)
        p = bst.predict(d)
        p0 = float(p[0]) if len(p) else float("nan")
        if not math.isfinite(p0):
            return None, "non_finite_v2_proba"
        return p0, None
    except Exception as e:
        return None, str(e)[:400]


def predict_v3_probability(
    feature_order: List[str],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
    row: Dict[str, float],
) -> Tuple[Optional[float], Optional[str]]:
    bst, meta, err = _load_pair(_V3_MODEL, _V3_FEATURES, "v3")
    if bst is None or err:
        return None, err
    try:
        import xgboost as xgb  # type: ignore

        x = _vec_for_order(feature_order, row, symbol, side, symbol_classes, side_classes)
        d = xgb.DMatrix(x, feature_names=feature_order)
        p = bst.predict(d)
        p0 = float(p[0]) if len(p) else float("nan")
        if not math.isfinite(p0):
            return None, "non_finite_v3_proba"
        return p0, None
    except Exception as e:
        return None, str(e)[:400]


def enrich_shadow_v2_v3_fields(
    rec: Dict[str, Any],
    *,
    symbol: str,
    side: str,
    row: Dict[str, float],
) -> None:
    """Set ``ai_approved_v2`` / ``ai_approved_v3_shadow`` on a trade_intent record (best-effort)."""
    rec.setdefault("ai_approved_v2", None)
    rec.setdefault("ai_approved_v3_shadow", None)
    v2_thr = default_v2_threshold()
    v3_thr = default_v3_threshold()
    b2, m2, _e2 = _load_pair(_V2_MODEL, _V2_META, "v2")
    if b2 and isinstance(m2, dict) and m2.get("feature_names"):
        fo = list(m2["feature_names"])
        sc = [str(x) for x in (m2.get("symbol_classes") or [])]
        sdc = [str(x) for x in (m2.get("side_classes") or [])]
        p2, err2 = predict_v2_probability(fo, symbol, side, sc, sdc, row)
        if p2 is not None:
            rec["ai_approved_v2"] = bool(float(p2) >= float(v2_thr))
            rec["v2_shadow_proba"] = float(p2)
        elif err2:
            rec["ai_approved_v2_error"] = str(err2)[:200]
    b3, m3, _e3 = _load_pair(_V3_MODEL, _V3_FEATURES, "v3")
    if b3 and isinstance(m3, dict) and m3.get("feature_names"):
        fo3 = list(m3["feature_names"])
        sc3 = [str(x) for x in (m3.get("symbol_classes") or [])]
        sdc3 = [str(x) for x in (m3.get("side_classes") or [])]
        p3, err3 = predict_v3_probability(fo3, symbol, side, sc3, sdc3, row)
        if p3 is not None:
            rec["ai_approved_v3_shadow"] = bool(float(p3) >= float(v3_thr))
            rec["v3_shadow_proba"] = float(p3)
        elif err3:
            rec["ai_approved_v3_shadow_error"] = str(err3)[:200]


def evaluate_v2_live_gate(
    *,
    symbol: str,
    side: str,
    row: Dict[str, float],
    threshold: Optional[float] = None,
) -> Tuple[bool, Optional[float], str]:
    """
    Returns (allowed, proba, reason_code).
    Fail-closed (not allowed) when model missing or inference fails, unless V2_LIVE_GATE_FAIL_OPEN=1.
    """
    import os

    thr = float(threshold) if threshold is not None else default_v2_threshold()
    bst, meta, err = _load_pair(_V2_MODEL, _V2_META, "v2")
    if bst is None or not isinstance(meta, dict) or not meta.get("feature_names"):
        if os.environ.get("V2_LIVE_GATE_FAIL_OPEN", "0").strip().lower() in ("1", "true", "yes"):
            return True, None, "v2_gate_fail_open_no_model"
        return False, None, "v2_agent_veto_no_model"
    fo = list(meta["feature_names"])
    sc = [str(x) for x in (meta.get("symbol_classes") or [])]
    sdc = [str(x) for x in (meta.get("side_classes") or [])]
    proba, perr = predict_v2_probability(fo, symbol, side, sc, sdc, row)
    if proba is None:
        if os.environ.get("V2_LIVE_GATE_FAIL_OPEN", "0").strip().lower() in ("1", "true", "yes"):
            return True, None, "v2_gate_fail_open_inference_error"
        return False, None, "v2_agent_veto_inference_error"
    if float(proba) < float(thr):
        return False, float(proba), "v2_agent_veto"
    return True, float(proba), "v2_gate_pass"
