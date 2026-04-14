"""
Alpha 10 live inference: RandomForestRegressor trained on strict cohort (exit_mfe_pct target).

Bundle format (joblib): see ``scripts/research/alpha_arena_trainer.py`` ``--export-alpha10``.
Feature order is fixed; missing live keys use training-column medians from the bundle.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_BUNDLE = REPO_ROOT / "models" / "alpha10_rf_mfe.joblib"

_bundle_cache: Optional[Dict[str, Any]] = None


def _flatten_leaves(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Nested dicts -> underscore paths (mirrors ``scripts/telemetry/alpaca_ml_flattener``)."""
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            safe = str(k).replace(".", "_")
            p = f"{prefix}_{safe}" if prefix else safe
            out.update(_flatten_leaves(v, p))
    elif isinstance(obj, list):
        key = prefix or "list"
        try:
            out[key] = json.dumps(obj, separators=(",", ":"), default=str)[:4000]
        except TypeError:
            out[key] = str(obj)[:4000]
    elif obj is None:
        out[prefix] = ""
    elif isinstance(obj, bool):
        out[prefix] = obj
    elif isinstance(obj, (int, float, str)):
        out[prefix] = obj
    else:
        out[prefix] = str(obj)
    return out


def _prefix_mlf(flat: Dict[str, Any], stem: str) -> Dict[str, Any]:
    return {f"mlf_{stem}_{k}": v for k, v in flat.items()}


def _finite_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    if isinstance(x, (int, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def default_bundle_path() -> Path:
    raw = os.environ.get("ALPHA10_MODEL_PATH", "").strip()
    return Path(raw).resolve() if raw else _DEFAULT_BUNDLE.resolve()


def load_bundle(path: Optional[Path] = None, *, force_reload: bool = False) -> Dict[str, Any]:
    global _bundle_cache
    if _bundle_cache is not None and not force_reload:
        return _bundle_cache
    p = (path or default_bundle_path()).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Alpha10 bundle missing: {p}")
    try:
        import joblib  # type: ignore
    except ImportError as e:
        raise RuntimeError("joblib required to load Alpha10 bundle") from e
    raw = joblib.load(p)
    if not isinstance(raw, dict) or raw.get("model") is None:
        raise ValueError("Invalid Alpha10 bundle (expected dict with 'model')")
    feats = raw.get("feature_names")
    if not isinstance(feats, list) or not feats:
        raise ValueError("Invalid Alpha10 bundle (feature_names)")
    meds = raw.get("impute_medians")
    if not isinstance(meds, list) or len(meds) != len(feats):
        raise ValueError("Invalid Alpha10 bundle (impute_medians length mismatch)")
    raw["_path"] = str(p)
    _bundle_cache = raw
    return raw


def clear_bundle_cache() -> None:
    global _bundle_cache
    _bundle_cache = None


def build_direction_intel_embed_pre_submit(
    *,
    api: Any,
    symbol: str,
    market_context: Optional[Dict[str, Any]],
    regime_posture: Optional[Dict[str, Any]],
    symbol_risk: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a direction_intel_embed-shaped dict (exit attribution style) from current intel,
    without persisting entry snapshots (avoids conflicting entry_ts with post-fill capture).
    """
    try:
        from src.intelligence.direction_intel import (
            build_direction_components_from_snapshot,
            build_embed_payload_for_exit,
            compute_intel_deltas,
        )
        from src.intelligence.intel_sources import build_full_intel_snapshot

        snap = build_full_intel_snapshot(
            api=api,
            symbol=symbol,
            market_context=market_context if isinstance(market_context, dict) else None,
            regime_posture=regime_posture if isinstance(regime_posture, dict) else None,
            symbol_risk=symbol_risk if isinstance(symbol_risk, dict) else None,
        )
        if not isinstance(snap, dict) or not snap:
            return {}
        exit_components = build_direction_components_from_snapshot(snap)
        deltas = compute_intel_deltas(snap, snap)
        return build_embed_payload_for_exit(snap, snap, exit_components, deltas)
    except Exception:
        return {}


def build_entry_telemetry_row(
    *,
    symbol: str,
    side: str,
    score: float,
    comps: Mapping[str, Any],
    cluster: Mapping[str, Any],
    market_context: Mapping[str, Any],
    regime_posture: Mapping[str, Any],
    symbol_risk: Mapping[str, Any],
    api: Any,
    strict_open_epoch_utc: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Flatten live entry-time blobs into the same ``mlf_*`` / ``strict_open_epoch_utc`` namespace
    as ``alpaca_ml_flattener`` (subset; missing model features fall back to medians at predict).
    """
    row: Dict[str, Any] = {}
    t0 = float(strict_open_epoch_utc) if strict_open_epoch_utc is not None else time.time()
    if math.isfinite(t0):
        row["strict_open_epoch_utc"] = t0

    row["mlf_scoreflow_total_score"] = float(score)
    row["mlf_scoreflow_total_score_imputed"] = 0
    try:
        from telemetry.ml_scoreflow_contract import normalize_composite_components_for_ml

        comp_norm = normalize_composite_components_for_ml(dict(comps) if comps else {})
    except Exception:
        comp_norm = {str(k): float(v) for k, v in dict(comps).items() if _finite_float(v) is not None} if comps else {}
    row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
    row["mlf_scoreflow_snapshot_age_sec"] = 0.0

    embed = build_direction_intel_embed_pre_submit(
        api=api,
        symbol=str(symbol).upper().strip(),
        market_context=dict(market_context) if market_context else {},
        regime_posture=dict(regime_posture) if regime_posture else {},
        symbol_risk=dict(symbol_risk) if symbol_risk else {},
    )
    if embed:
        row.update(_prefix_mlf(_flatten_leaves(embed), "direction_intel_embed"))

    eu = cluster.get("entry_uw") if isinstance(cluster, dict) else None
    if isinstance(eu, dict) and eu:
        row.update(_prefix_mlf(_flatten_leaves(eu), "entry_uw"))

    if "mlf_entry_uw_flow_strength" not in row and isinstance(cluster, dict):
        for key in ("uw_flow_strength", "flow_strength"):
            fv = _finite_float(cluster.get(key))
            if fv is not None:
                row["mlf_entry_uw_flow_strength"] = fv
                break

    return row


def row_to_feature_matrix(
    telemetry: Mapping[str, Any],
    feature_names: Sequence[str],
    impute_medians: Sequence[float],
) -> Any:
    import numpy as np

    vec = np.zeros((1, len(feature_names)), dtype=np.float64)
    for j, name in enumerate(feature_names):
        med = float(impute_medians[j]) if j < len(impute_medians) else 0.0
        if not math.isfinite(med):
            med = 0.0
        raw = telemetry.get(name)
        v = _finite_float(raw)
        vec[0, j] = float(v) if v is not None else med
    return vec


def predict_mfe(telemetry: Mapping[str, Any], *, bundle: Optional[Dict[str, Any]] = None) -> float:
    b = bundle or load_bundle()
    model = b["model"]
    names: List[str] = list(b["feature_names"])
    meds: List[float] = [float(x) for x in b["impute_medians"]]
    X = row_to_feature_matrix(telemetry, names, meds)
    pred = model.predict(X)
    out = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
    return out if math.isfinite(out) else float("nan")


def describe_bundle(bundle: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    b = bundle or load_bundle()
    return {
        "path": b.get("_path"),
        "n_features": len(b.get("feature_names", [])),
        "target": b.get("target"),
        "feature_names": list(b.get("feature_names", [])),
    }
