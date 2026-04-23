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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
_MODEL_PATH = REPO_ROOT / "models" / "vanguard_entry_filter_v1.json"
_META_PATH = REPO_ROOT / "models" / "vanguard_entry_filter_v1_features.json"

_CACHED: Dict[str, Any] = {
    "booster": None,
    "meta": None,
    "err": None,
}
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
        return float(classes.index(s2)) if s2 in classes else float("nan")
    except Exception:
        return float("nan")


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
    vec: Dict[str, float] = {}
    for k in feature_order:
        vec[k] = float(row.get(k, float("nan")))
    vec["symbol_enc"] = _symbol_code(symbol, symbol_classes)
    vec["side_enc"] = _side_code(side, side_classes)
    hraw = float(vec.get("hour_of_day", float("nan")))
    if (not math.isfinite(hraw)) and "hour_of_day" in feature_order:
        vec["hour_of_day"] = (
            float(datetime.now(_ET).hour)  # type: ignore[union-attr]
            if _ET
            else float(datetime.now(timezone.utc).hour)
        )
    x = np.array(
        [float(vec.get(f, float("nan"))) for f in feature_order],
        dtype=np.float32,
    ).reshape(1, -1)
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
    rec["shadow_chop_block"] = bool(shadow_chop_block_now())
    rec["ai_approved_v1"] = None
    rec["ai_approved_v2"] = None
    rec["ai_approved_v3_shadow"] = None
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
