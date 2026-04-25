"""
Shadow mode: chop-window flag + Vanguard XGBoost ML telemetry (v1 legacy, v2 live mirror, v3 shadow).

Attaches to trade_intent JSON in logs/run.jsonl:
  - shadow_chop_block: 11:30–13:30 US/Eastern
  - ai_approved_v1: True/False/None (None = inference failed safely)
  - ai_approved_v2: True/False/None — same threshold as live V2 gate
  - ai_approved_v3_shadow: True/False/None — V3 Alpha Hunter (runner) shadow lane
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
_MODEL_PATH = REPO_ROOT / "models" / "vanguard_entry_filter_v1.json"
_META_PATH = REPO_ROOT / "models" / "vanguard_entry_filter_v1_features.json"
_CHALLENGER_LONG_MODEL = REPO_ROOT / "models" / "vanguard_challenger_long.json"
_CHALLENGER_LONG_META = REPO_ROOT / "models" / "vanguard_challenger_long_features.json"
_CHALLENGER_LONG_THRESHOLD = REPO_ROOT / "models" / "vanguard_challenger_long_threshold.json"
_CHALLENGER_SHORT_MODEL = REPO_ROOT / "models" / "vanguard_challenger_short.json"
_CHALLENGER_SHORT_META = REPO_ROOT / "models" / "vanguard_challenger_short_features.json"
_CHALLENGER_SHORT_THRESHOLD = REPO_ROOT / "models" / "vanguard_challenger_short_threshold.json"
_SHADOW_EXECUTIONS_PATH = REPO_ROOT / "logs" / "shadow_executions.jsonl"

_CACHED: Dict[str, Any] = {
    "booster": None,
    "meta": None,
    "err": None,
}
_CHALLENGER_CACHE: Dict[str, Any] = {}
_TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


def _import_flattener():
    p = REPO_ROOT / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    if not p.is_file():
        return None
    spec = importlib.util.spec_from_file_location("alpaca_ml_flattener_dyn", p)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _import_normalize():
    try:
        from telemetry.ml_scoreflow_contract import normalize_composite_components_for_ml

        return normalize_composite_components_for_ml
    except Exception:
        return None


def _parse_open_epoch_from_trade_id(tid: Any) -> Optional[float]:
    m = _TID_RE.match(str(tid or "").strip())
    if not m:
        return None
    s = m.group(2).strip().replace("Z", "+00:00")
    try:
        from datetime import timezone as _tz

        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=_tz.utc)
        return float(d.timestamp())
    except Exception:
        return None


# Blocked trade_intent paths often omit broker entry_price; shadow TP/SL still need a reference.
_SHADOW_QUOTE_PRICE_KEYS = (
    "last_price",
    "last",
    "close",
    "vwap",
    "price",
    "current_price",
    "mark",
    "reference_price",
    "mid",
    "mid_price",
    "latest_price",
    "bar_close",
)


def _maybe_positive_price(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        x = float(v)
        if not math.isfinite(x) or x <= 0:
            return None
        return x
    except (TypeError, ValueError):
        return None


def _mid_from_bid_ask(m: Dict[str, Any]) -> Optional[float]:
    bid = _maybe_positive_price(m.get("bid"))
    ask = _maybe_positive_price(m.get("ask"))
    if bid is None or ask is None or ask < bid:
        return None
    mid = (bid + ask) / 2.0
    return mid if mid > 0 and math.isfinite(mid) else None


def _scan_mapping_for_price(m: Any) -> Tuple[Optional[float], str]:
    """Return (price, sub_key) from one dict layer; sub_key names the winning field."""
    if not isinstance(m, dict):
        return None, ""
    p = _maybe_positive_price(m.get("entry_price"))
    if p is not None:
        return p, "entry_price"
    for k in _SHADOW_QUOTE_PRICE_KEYS:
        p2 = _maybe_positive_price(m.get(k))
        if p2 is not None:
            return p2, k
    mid = _mid_from_bid_ask(m)
    if mid is not None:
        return mid, "mid_bid_ask"
    return None, ""


def resolve_shadow_entry_price(
    *,
    row: Dict[str, float],
    feature_snapshot: Any = None,
    comps: Any = None,
    cluster: Any = None,
    source_event: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[float], str]:
    """
    Resolve a positive finite reference price for shadow TP/SL simulation.

    Order: flattened ML row → feature_snapshot → comps → cluster → trade_intent rec →
    nested trade_intent.feature_snapshot. Aligns with blocked_counterfactuals intent_price keys.
    """
    pr, sub = _scan_mapping_for_price(row)
    if pr is not None:
        return pr, f"row:{sub}"

    for label, m in (
        ("feature_snapshot", feature_snapshot),
        ("comps", comps),
        ("cluster", cluster),
    ):
        pr2, sub2 = _scan_mapping_for_price(m)
        if pr2 is not None:
            return pr2, f"{label}:{sub2}"

    if isinstance(source_event, dict):
        pr3, sub3 = _scan_mapping_for_price(source_event)
        if pr3 is not None:
            return pr3, f"trade_intent:{sub3}"
        fs = source_event.get("feature_snapshot")
        pr4, sub4 = _scan_mapping_for_price(fs)
        if pr4 is not None:
            return pr4, f"trade_intent.feature_snapshot:{sub4}"
        pr5, sub5 = _deep_scan_dicts_for_price(fs, label="trade_intent.feature_snapshot_nested")
        if pr5 is not None:
            return pr5, sub5

    if isinstance(feature_snapshot, dict):
        pr6, sub6 = _deep_scan_dicts_for_price(feature_snapshot, label="feature_snapshot_nested")
        if pr6 is not None:
            return pr6, sub6

    return None, "unresolved"


def _deep_scan_dicts_for_price(obj: Any, *, label: str, depth: int = 0, max_depth: int = 6) -> Tuple[Optional[float], str]:
    """Walk nested dicts (common for market_context / bar blobs) for NBBO-style quote keys."""
    if depth > max_depth or not isinstance(obj, dict):
        return None, ""
    pr, sub = _scan_mapping_for_price(obj)
    if pr is not None:
        return pr, f"{label}:{sub}" if sub else label
    for _k, v in obj.items():
        if isinstance(v, dict):
            pr2, sub2 = _deep_scan_dicts_for_price(v, label=label, depth=depth + 1, max_depth=max_depth)
            if pr2 is not None:
                return pr2, sub2
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            for item in v[:12]:
                if isinstance(item, dict):
                    pr3, sub3 = _deep_scan_dicts_for_price(item, label=label, depth=depth + 1, max_depth=max_depth)
                    if pr3 is not None:
                        return pr3, sub3
    return None, ""


def _broker_last_trade_price(engine: Any, symbol: str) -> Tuple[Optional[float], str]:
    """Best-effort NBBO/last from live executor (one REST hop; failures are silent)."""
    try:
        ex = getattr(engine, "executor", None) or engine
        fn = getattr(ex, "get_last_trade", None)
        if not callable(fn):
            return None, ""
        px = float(fn(str(symbol or "").upper().strip()))
        if math.isfinite(px) and px > 0:
            return px, "broker_last_trade"
    except Exception:
        pass
    return None, ""


def ensure_shadow_executions_log_ready() -> None:
    """Create ``logs/shadow_executions.jsonl`` so offline labs see a file (empty tape ≠ missing file)."""
    try:
        _SHADOW_EXECUTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _SHADOW_EXECUTIONS_PATH.exists():
            _SHADOW_EXECUTIONS_PATH.touch()
    except OSError:
        pass


def shadow_chop_block_now() -> bool:
    """True during 11:30–13:30 US/Eastern (inclusive, minute precision)."""
    if _ET is None:
        return False
    n = datetime.now(_ET)
    m = n.hour * 60 + n.minute
    start = 11 * 60 + 30
    end = 13 * 60 + 30
    return start <= m <= end


def shadow_chop_block_at(when_utc: datetime) -> bool:
    """
    True when *when_utc* (UTC-aware or naive-UTC) falls in 11:30–13:30 US/Eastern, inclusive.
    Used for offline backfill of historical trade_intent rows.
    """
    if _ET is None:
        return False
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=timezone.utc)
    n = when_utc.astimezone(_ET)
    m = n.hour * 60 + n.minute
    start = 11 * 60 + 30
    end = 13 * 60 + 30
    return start <= m <= end


def _load_booster_and_meta() -> Tuple[Optional[Any], Optional[dict], Optional[str]]:
    if _CACHED.get("err"):
        return _CACHED.get("booster"), _CACHED.get("meta"), str(_CACHED.get("err"))
    if not _MODEL_PATH.is_file() or not _META_PATH.is_file():
        e = f"missing_model_or_meta path_model={_MODEL_PATH} path_meta={_META_PATH}"
        _CACHED["err"] = e
        return None, None, e
    try:
        import xgboost as xgb  # type: ignore

        bst = xgb.Booster()
        bst.load_model(str(_MODEL_PATH))
        meta = json.loads(_META_PATH.read_text(encoding="utf-8"))
        _CACHED["booster"] = bst
        _CACHED["meta"] = meta
        return bst, meta, None
    except Exception as e:  # pragma: no cover
        _CACHED["err"] = str(e)
        return None, None, str(e)


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
        normalized_classes = [str(c).upper().strip() for c in classes]
        return float(normalized_classes.index(s2)) if s2 in normalized_classes else float("nan")
    except Exception:
        return float("nan")


def _challenger_paths(side: str) -> Tuple[Path, Path, Path, str]:
    side_norm = str(side or "").strip().lower()
    if side_norm in ("sell", "short"):
        return _CHALLENGER_SHORT_MODEL, _CHALLENGER_SHORT_META, _CHALLENGER_SHORT_THRESHOLD, "short"
    return _CHALLENGER_LONG_MODEL, _CHALLENGER_LONG_META, _CHALLENGER_LONG_THRESHOLD, "long"


def _load_challenger_pair(side: str) -> Tuple[Optional[Any], Optional[dict], Optional[dict], Optional[str]]:
    model_path, meta_path, threshold_path, side_key = _challenger_paths(side)
    cache_key = f"challenger_{side_key}"
    err_key = f"{cache_key}_err"
    if _CHALLENGER_CACHE.get(err_key):
        return None, None, None, str(_CHALLENGER_CACHE.get(err_key))
    cached = _CHALLENGER_CACHE.get(cache_key)
    if isinstance(cached, tuple) and len(cached) == 3:
        booster, meta, threshold_meta = cached
        return booster, meta, threshold_meta, None
    if not model_path.is_file() or not meta_path.is_file() or not threshold_path.is_file():
        err = f"missing_challenger_artifacts side={side_key}"
        _CHALLENGER_CACHE[err_key] = err
        return None, None, None, err
    try:
        import xgboost as xgb  # type: ignore

        booster = xgb.Booster()
        booster.load_model(str(model_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        threshold_meta = json.loads(threshold_path.read_text(encoding="utf-8"))
        _CHALLENGER_CACHE[cache_key] = (booster, meta, threshold_meta)
        _CHALLENGER_CACHE.pop(err_key, None)
        return booster, meta, threshold_meta, None
    except Exception as e:  # pragma: no cover
        _CHALLENGER_CACHE[err_key] = str(e)
        return None, None, None, str(e)


def _vector_for_model(
    feature_order: List[str],
    row: Dict[str, float],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
) -> "np.ndarray":
    from src.core.ml_feature_normalization import normalize_features_for_side

    normalized_row = normalize_features_for_side(row, side)
    vec: Dict[str, float] = {}
    for key in feature_order:
        try:
            vec[key] = float(normalized_row.get(key, float("nan")))
        except (TypeError, ValueError):
            vec[key] = float("nan")
    vec["symbol_enc"] = _symbol_code(symbol, symbol_classes)
    vec["side_enc"] = _side_code(side, side_classes)
    if (not math.isfinite(float(vec.get("hour_of_day", float("nan"))))) and "hour_of_day" in feature_order:
        vec["hour_of_day"] = (
            float(datetime.now(_ET).hour)  # type: ignore[union-attr]
            if _ET
            else float(datetime.now(timezone.utc).hour)
        )
    return np.array([float(vec.get(f, float("nan"))) for f in feature_order], dtype=np.float32).reshape(1, -1)


def predict_challenger_probability(
    *,
    symbol: str,
    side: str,
    row: Dict[str, float],
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    booster, meta, threshold_meta, err = _load_challenger_pair(side)
    if booster is None or not isinstance(meta, dict) or not isinstance(threshold_meta, dict):
        return None, None, err or "missing_challenger_artifacts"
    try:
        import xgboost as xgb  # type: ignore

        feature_order = list(meta.get("feature_names") or [])
        symbol_classes = [str(x) for x in (meta.get("symbol_classes") or [])]
        side_classes = [str(x) for x in (meta.get("side_classes") or [])]
        x = _vector_for_model(feature_order, row, symbol, side, symbol_classes, side_classes)
        d = xgb.DMatrix(x, feature_names=feature_order)
        pred = booster.predict(d)
        proba = float(pred[0]) if len(pred) else float("nan")
        if not math.isfinite(proba):
            return None, None, "non_finite_challenger_proba"
        threshold = float(threshold_meta.get("holdout_probability_threshold", 0.5))
        return proba, threshold, None
    except Exception as e:
        return None, None, str(e)[:400]


def _shadow_tp_sl(entry_price: float, side: str) -> Tuple[float, float]:
    tp_pct = float(os.environ.get("CHALLENGER_SHADOW_TP_PCT", "0.015"))
    sl_pct = float(os.environ.get("CHALLENGER_SHADOW_SL_PCT", "0.008"))
    side_norm = str(side or "").strip().lower()
    if side_norm in ("sell", "short"):
        return entry_price * (1.0 - tp_pct), entry_price * (1.0 + sl_pct)
    return entry_price * (1.0 + tp_pct), entry_price * (1.0 - sl_pct)


def log_shadow_execution(
    *,
    symbol: str,
    side: str,
    proba: float,
    threshold: float,
    entry_price: Optional[float],
    source_event: Dict[str, Any],
    entry_price_source: Optional[str] = None,
) -> None:
    rec: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": "SHADOW_EXECUTION",
        "model": "vanguard_challenger",
        "symbol": str(symbol or "").upper().strip(),
        "side": str(side or "").strip().lower(),
        "challenger_proba": float(proba),
        "challenger_threshold": float(threshold),
        "primary_decision_outcome": source_event.get("decision_outcome"),
        "primary_blocked_reason": source_event.get("blocked_reason") or source_event.get("blocked_reason_code"),
        "source": "shadow_evaluator",
    }
    if entry_price is not None and math.isfinite(float(entry_price)) and float(entry_price) > 0:
        entry = float(entry_price)
        take_profit, stop_loss = _shadow_tp_sl(entry, side)
        rec["entry_price"] = entry
        rec["entry_price_source"] = entry_price_source if entry_price_source is not None else "unspecified"
        rec["shadow_take_profit_price"] = round(float(take_profit), 6)
        rec["shadow_stop_loss_price"] = round(float(stop_loss), 6)
    else:
        rec["entry_price"] = None
        rec["entry_price_source"] = entry_price_source or "unresolved"
        rec["shadow_take_profit_price"] = None
        rec["shadow_stop_loss_price"] = None
    _SHADOW_EXECUTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _SHADOW_EXECUTIONS_PATH.exists():
        _SHADOW_EXECUTIONS_PATH.touch()
    with _SHADOW_EXECUTIONS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def _merge_ml_blobs(cluster: Any, comps: Any, snap: Any, amf) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for blob_key in getattr(amf, "ML_BLOB_KEYS", ()):
        blob = None
        for root in (cluster, comps, snap):
            if not isinstance(root, dict):
                continue
            b = root.get(blob_key)
            if isinstance(b, dict) and b:
                blob = b
                break
        if isinstance(blob, dict) and blob and hasattr(amf, "_flatten_leaves") and hasattr(
            amf, "_prefix_mlf"
        ):
            flat = amf._flatten_leaves(blob)
            stem = str(blob_key).replace(".", "_")
            out.update(amf._prefix_mlf(flat, stem))
    return out


def _apply_scoreflow_row(
    out: Dict[str, Any],
    feature_snapshot: Any,
    cluster: Any,
    comps: Any,
    amf: Any,
    sym_score: str,
) -> None:
    normalize = _import_normalize()
    comp: Optional[dict] = None
    tot: Optional[float] = None
    if isinstance(feature_snapshot, dict):
        c = feature_snapshot.get("components")
        if isinstance(c, dict):
            comp = c
        ts = str(feature_snapshot.get("composite_score") or "").strip()
        if ts:
            try:
                tot = float(ts)
            except (TypeError, ValueError):
                pass
    if comp is None and isinstance(cluster, dict):
        for path in (cluster.get("composite"), cluster.get("cluster")):
            if not isinstance(path, dict):
                continue
            c2 = path.get("components")
            if isinstance(c2, dict):
                comp = c2
                break
    if normalize is None and amf and hasattr(amf, "normalize_composite_components_for_ml"):
        try:
            normalize = amf.normalize_composite_components_for_ml  # type: ignore[assignment]
        except Exception:
            pass
    if not callable(normalize):
        return
    comp_dict = comp if isinstance(comp, dict) else {}
    comp_norm = normalize(comp_dict)  # type: ignore[operator]
    if hasattr(amf, "_flatten_leaves") and hasattr(amf, "_prefix_mlf"):
        out.update(
            amf._prefix_mlf(  # type: ignore[union-attr]
                amf._flatten_leaves(comp_norm), "scoreflow_components"  # type: ignore[union-attr]
            )
        )
    if tot is not None and tot == tot:
        out["mlf_scoreflow_total_score"] = tot
    else:
        s = 0.0
        for v in comp_norm.values() if isinstance(comp_norm, dict) else []:
            try:
                s += float(v) if v is not None and not isinstance(v, bool) else 0.0
            except (TypeError, ValueError):
                pass
        if s != 0.0 or comp_norm:
            out["mlf_scoreflow_total_score"] = float(round(s, 6))
            out["mlf_scoreflow_total_score_imputed"] = 1.0
    tnow = datetime.now(timezone.utc).timestamp()
    out["mlf_scoreflow_snapshot_ts_epoch"] = float(tnow)
    if sym_score:
        out["mlf_scoreflow_snapshot_age_sec"] = 0.0


def build_vanguard_feature_map(
    *,
    symbol: str,
    side: str,
    now_utc: Optional[datetime],
    feature_snapshot: Any,
    comps: Any,
    cluster: Any,
    trade_id: Optional[str],
) -> Dict[str, float]:
    """Best-effort single-row feature dict aligned with training column names (subset filled)."""
    out: Dict[str, Any] = {}
    amf = _import_flattener()
    if amf is None:
        return {}
    fs = feature_snapshot if isinstance(feature_snapshot, dict) else {}
    out: Dict[str, Any] = _merge_ml_blobs(cluster, comps, fs, amf)
    _apply_scoreflow_row(
        out,
        feature_snapshot,
        cluster,
        comps,
        amf,
        str(symbol or "").upper().strip(),
    )
    n = now_utc or datetime.now(timezone.utc)
    n_et = n.astimezone(_ET) if _ET else n
    out["hour_of_day"] = float(n_et.hour)
    if trade_id:
        oep = _parse_open_epoch_from_trade_id(trade_id)
        if oep is not None:
            out["strict_open_epoch_utc"] = oep
    else:
        try:
            from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

            out["strict_open_epoch_utc"] = float(STRICT_EPOCH_START)
        except Exception:
            out["strict_open_epoch_utc"] = float("nan")
    for src in (comps, feature_snapshot, cluster if isinstance(cluster, dict) else {}):
        if isinstance(src, dict):
            for k in ("entry_price", "qty", "size"):
                if k in src and src[k] is not None and k not in out:
                    try:
                        out[k] = float(src[k])  # type: ignore[assignment]
                    except (TypeError, ValueError):
                        pass
    for k, v in list(out.items()):
        if isinstance(v, (list, dict)):
            del out[k]
    out2: Dict[str, float] = {}
    for k, v in out.items():
        if v is None:
            out2[str(k)] = float("nan")
            continue
        if isinstance(v, bool):
            out2[str(k)] = 1.0 if v else 0.0
        elif isinstance(v, (int, float)):
            try:
                out2[str(k)] = float(v)
            except (TypeError, ValueError):
                out2[str(k)] = float("nan")
    return out2


def predict_vanguard_ai_approved(
    feature_order: List[str],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
    row: Dict[str, float],
) -> bool:
    bst, _, err = _load_booster_and_meta()
    if bst is None or err:
        raise RuntimeError(err or "no booster")
    x = _vector_for_model(feature_order, row, symbol, side, symbol_classes, side_classes)
    import xgboost as xgb  # type: ignore

    d = xgb.DMatrix(x, feature_names=feature_order)
    p = bst.predict(d)
    p0 = float(p[0]) if len(p) else 0.0
    return p0 >= 0.5


def attach_shadow_telemetry(
    rec: Dict[str, Any],
    *,
    symbol: str,
    side: str,
    feature_snapshot: Any,
    comps: Any,
    cluster: Any,
    engine: Any = None,
) -> None:
    ensure_shadow_executions_log_ready()
    rec["shadow_chop_block"] = bool(shadow_chop_block_now())
    rec["ai_approved_v1"] = None
    rec["ai_approved_v2"] = None
    rec["ai_approved_v3_shadow"] = None
    rec["challenger_ai_approved"] = None
    tid = rec.get("trade_id")
    row: Dict[str, float] = {}
    try:
        row = build_vanguard_feature_map(
            symbol=symbol,
            side=side,
            now_utc=datetime.now(timezone.utc),
            feature_snapshot=feature_snapshot,
            comps=comps if isinstance(comps, dict) else {},
            cluster=cluster if isinstance(cluster, dict) else {},
            trade_id=str(tid) if tid else None,
        )
        if engine is not None:
            try:
                _pex = getattr(engine, "executor", None) or engine
                _pen = getattr(_pex, "_pending_entry_snapshot", None)
                if isinstance(_pen, dict):
                    for k, fk in (("entry_price", "entry_price"), ("size", "qty"), ("qty", "qty")):
                        if k in _pen and _pen[k] is not None and fk not in row:
                            try:
                                row[fk] = float(_pen[k])
                            except (TypeError, ValueError):
                                pass
            except Exception:
                pass
    except Exception as e:
        rec["ai_approved_v1_error"] = str(e)[:200]
        if "sys" in dir():
            print(f"[shadow_evaluator] feature_map_failed: {e}", file=sys.stderr)

    bst, meta, err = _load_booster_and_meta()
    if bst is None or not isinstance(meta, dict) or not meta.get("feature_names"):
        if err:
            rec["ai_approved_v1_error"] = (rec.get("ai_approved_v1_error") or "") + ("; " if rec.get("ai_approved_v1_error") else "") + str(err)[:200]
    else:
        try:
            fo: List[str] = list(meta["feature_names"])
            sc = [str(x) for x in (meta.get("symbol_classes") or [])]
            sdc = [str(x) for x in (meta.get("side_classes") or [])]
            rec["ai_approved_v1"] = bool(predict_vanguard_ai_approved(fo, symbol, side, sc, sdc, row))
        except Exception as e:
            rec["ai_approved_v1"] = None
            rec["ai_approved_v1_error"] = str(e)[:400]
            if "sys" in dir():
                print(f"[shadow_evaluator] ai_approved_v1 failed: {e}", file=sys.stderr)

    try:
        from telemetry.vanguard_ml_runtime import enrich_shadow_v2_v3_fields

        enrich_shadow_v2_v3_fields(rec, symbol=symbol, side=side, row=row)
    except Exception as e:
        rec["ai_approved_v2_error"] = str(e)[:200]
        if "sys" in dir():
            print(f"[shadow_evaluator] v2/v3 shadow enrich failed: {e}", file=sys.stderr)

    if os.environ.get("CHALLENGER_SHADOW_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on"):
        try:
            proba_c, threshold_c, err_c = predict_challenger_probability(symbol=symbol, side=side, row=row)
            if proba_c is not None and threshold_c is not None:
                approved_c = float(proba_c) >= float(threshold_c)
                rec["challenger_ai_approved"] = bool(approved_c)
                rec["challenger_shadow_proba"] = float(proba_c)
                rec["challenger_threshold"] = float(threshold_c)
                if approved_c and str(rec.get("decision_outcome") or "").lower() != "entered":
                    resolved, price_src = resolve_shadow_entry_price(
                        row=row,
                        feature_snapshot=feature_snapshot,
                        comps=comps if isinstance(comps, dict) else {},
                        cluster=cluster if isinstance(cluster, dict) else {},
                        source_event=rec,
                    )
                    if (resolved is None or not math.isfinite(float(resolved)) or float(resolved) <= 0) and engine is not None:
                        br_px, br_src = _broker_last_trade_price(engine, str(symbol))
                        if br_px is not None:
                            resolved, price_src = br_px, br_src
                    if resolved is not None and math.isfinite(float(resolved)) and float(resolved) > 0:
                        rec["challenger_shadow_entry_price_source"] = price_src
                        log_shadow_execution(
                            symbol=symbol,
                            side=side,
                            proba=float(proba_c),
                            threshold=float(threshold_c),
                            entry_price=float(resolved),
                            source_event=rec,
                            entry_price_source=price_src,
                        )
                    elif os.environ.get("CHALLENGER_SHADOW_LOG_UNPRICED", "1").strip().lower() in (
                        "1",
                        "true",
                        "yes",
                        "on",
                    ):
                        # Evidence chain: record challenger approval even when no reference price (labs join + optional bar proxy).
                        rec["challenger_shadow_entry_price_source"] = "unresolved"
                        log_shadow_execution(
                            symbol=symbol,
                            side=side,
                            proba=float(proba_c),
                            threshold=float(threshold_c),
                            entry_price=None,
                            source_event=rec,
                            entry_price_source="unresolved",
                        )
            elif err_c:
                rec["challenger_error"] = str(err_c)[:200]
        except Exception as e:
            rec["challenger_error"] = str(e)[:200]


if __name__ == "__main__":
    r: Dict[str, Any] = {}
    attach_shadow_telemetry(
        r,
        symbol="SPY",
        side="long",
        feature_snapshot={},
        comps={},
        cluster={},
        engine=None,
    )
    print(r)
