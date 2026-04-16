"""
Alpaca Shadow Brain — telemetry-only EOD return estimate from paper ML gate bundle.

Lazy-loads ``models/paper_ml_gate/alpaca_eod_model.joblib`` (RandomForest bundle).
Rebuilds ``mlx_*`` UW×macro interaction columns on the fly (same semantics as
``scripts/telemetry/alpaca_ml_interaction_expand.py``) before ``predict``.

Env:
  ALPACA_SHADOW_ML_TELEMETRY_ONLY — callers should gate on this; helpers are no-ops if unset.
  ALPACA_PAPER_ML_GATE_MODEL — optional override path to the joblib bundle.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_UW_COLS = ("uw_gamma_skew", "uw_tide_score")


def _finite_float(x: Any) -> float:
    if x is None:
        return 0.0
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return 0.0
    try:
        v = float(s)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def _slug_header(h: str, *, max_len: int = 72) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", h).strip("_")
    if len(s) > max_len:
        s = s[-max_len:].lstrip("_")
    return s or "macro"


def _resolve_macro_columns(headers: Sequence[str]) -> List[Tuple[str, str]]:
    hset = list(headers)
    found: List[Tuple[str, str]] = []
    if "mlf_scoreflow_total_score" in hset:
        found.append(("mlf_scoreflow_total_score", "mlf_scoreflow_total_score"))
    for h in hset:
        if "vxx_vxz_ratio" in h:
            found.append(("vxx_vxz_ratio", h))
            break
    for h in hset:
        if "futures_direction_delta" in h:
            found.append(("futures_direction_delta", h))
            break
    return found


def _load_flattener_module() -> Any:
    path = REPO_ROOT / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    spec = importlib.util.spec_from_file_location("_alpaca_ml_flattener_dyn", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load alpaca_ml_flattener")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_fl: Any = None


def _flattener() -> Any:
    global _fl
    if _fl is None:
        _fl = _load_flattener_module()
    return _fl


_bundle: Optional[Dict[str, Any]] = None


def _default_model_path() -> Path:
    raw = (os.environ.get("ALPACA_PAPER_ML_GATE_MODEL") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (REPO_ROOT / "models" / "paper_ml_gate" / "alpaca_eod_model.joblib").resolve()


def load_paper_ml_gate_bundle(force_reload: bool = False) -> Optional[Dict[str, Any]]:
    global _bundle
    if _bundle is not None and not force_reload:
        return _bundle
    path = _default_model_path()
    if not path.is_file():
        _bundle = None
        return None
    try:
        import joblib  # type: ignore

        _bundle = joblib.load(path)
    except Exception:
        _bundle = None
        return None
    if not isinstance(_bundle, dict) or "model" not in _bundle:
        _bundle = None
        return None
    return _bundle


def _prefix_mlf(flat: Dict[str, Any], stem: str) -> Dict[str, Any]:
    return {f"mlf_{stem}_{k}": v for k, v in flat.items()}


def _flatten_leaves(obj: Any, prefix: str = "") -> Dict[str, Any]:
    fl = _flattener()
    fn = getattr(fl, "_flatten_leaves", None)
    if callable(fn):
        return fn(obj, prefix)
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
    elif isinstance(obj, (int, float, str)):
        out[prefix] = obj
    else:
        out[prefix] = str(obj)
    return out


def _uw_gamma_skew_and_tide(entry_uw: Any) -> Tuple[float, float]:
    fl = _flattener()
    fn = getattr(fl, "_uw_gamma_skew_and_tide", None)
    if callable(fn):
        return fn(entry_uw)
    return 0.0, 0.0


def _build_direction_embed_row(api: Any, symbol: str) -> Dict[str, Any]:
    """
    Flatten direction intel like exit_attribution: entry/exit snapshot identical at submit time
    yields zero intel_deltas (matches no-move baseline until exit refreshes).
    """
    row: Dict[str, Any] = {}
    try:
        from src.intelligence.direction_intel import (
            build_direction_components_from_snapshot,
            build_embed_payload_for_exit,
            compute_intel_deltas,
        )
        from src.intelligence.intel_sources import build_full_intel_snapshot

        market_context = None
        regime_posture = None
        try:
            from structural_intelligence.market_context_v2 import read_market_context_v2

            market_context = read_market_context_v2()
        except Exception:
            pass
        try:
            from structural_intelligence.regime_posture_v2 import read_regime_posture_state

            regime_posture = read_regime_posture_state()
        except Exception:
            pass
        snapshot = build_full_intel_snapshot(
            api=api,
            symbol=symbol,
            market_context=market_context if isinstance(market_context, dict) else None,
            regime_posture=regime_posture if isinstance(regime_posture, dict) else None,
        )
        if not isinstance(snapshot, dict):
            return row
        components = build_direction_components_from_snapshot(snapshot)
        embed = build_embed_payload_for_exit(
            snapshot,
            snapshot,
            components,
            compute_intel_deltas(snapshot, snapshot),
        )
        flat = _flatten_leaves(embed if isinstance(embed, dict) else {})
        row.update(_prefix_mlf(flat, "direction_intel_embed"))
    except Exception:
        pass
    return row


def build_live_feature_row(
    *,
    symbol: str,
    entry_components: Mapping[str, Any],
    entry_score: float,
    market_regime: str,
    api: Any = None,
) -> Dict[str, Any]:
    """Assemble mlf_/uw_/mlx_* fields aligned with flattened cohort + interaction expand."""
    from telemetry.ml_scoreflow_contract import normalize_composite_components_for_ml

    row: Dict[str, Any] = {}

    comp_norm = normalize_composite_components_for_ml(
        dict(entry_components) if isinstance(entry_components, Mapping) else {}
    )
    row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
    try:
        tot = float(entry_score)
    except (TypeError, ValueError):
        tot = float("nan")
    if math.isfinite(tot):
        row["mlf_scoreflow_total_score"] = tot
    else:
        row["mlf_scoreflow_total_score"] = round(sum(comp_norm.values()), 6)

    try:
        from src.exit.entry_uw_backfill import try_backfill_v2_uw_inputs

        entry_uw = try_backfill_v2_uw_inputs(symbol, str(market_regime or "unknown"))
    except Exception:
        entry_uw = {}
    if isinstance(entry_uw, dict) and entry_uw:
        row.update(_prefix_mlf(_flatten_leaves(entry_uw), "entry_uw"))
    g_skew, t_score = _uw_gamma_skew_and_tide(entry_uw if isinstance(entry_uw, dict) else {})
    row["uw_gamma_skew"] = g_skew
    row["uw_tide_score"] = t_score

    row.update(_build_direction_embed_row(api, symbol))

    headers = list(row.keys())
    macros = _resolve_macro_columns(headers)
    seen_col: set[str] = set()
    for uw in _UW_COLS:
        u = _finite_float(row.get(uw))
        for logical, macro_h in macros:
            stem = _slug_header(logical)
            col = f"mlx_{uw}_x_{stem}"
            base = col
            n = 0
            while col in seen_col:
                n += 1
                col = f"{base}_{n}"
            seen_col.add(col)
            m = _finite_float(row.get(macro_h))
            row[col] = u * m
    return row


def predict_expected_eod_return(
    *,
    symbol: str,
    entry_components: Mapping[str, Any],
    entry_score: float,
    market_regime: str,
    api: Any = None,
) -> Optional[float]:
    bundle = load_paper_ml_gate_bundle()
    if not bundle:
        return None
    model = bundle.get("model")
    names: List[str] = list(bundle.get("feature_names") or [])
    medians: List[float] = list(bundle.get("impute_medians") or [])
    if model is None or not names:
        return None
    if len(medians) != len(names):
        medians = [0.0] * len(names)
    row = build_live_feature_row(
        symbol=symbol,
        entry_components=entry_components,
        entry_score=entry_score,
        market_regime=market_regime,
        api=api,
    )
    import numpy as np

    x = np.zeros((1, len(names)), dtype=np.float64)
    for j, name in enumerate(names):
        if name in row:
            x[0, j] = _finite_float(row.get(name))
        else:
            x[0, j] = float(medians[j]) if j < len(medians) else 0.0
    try:
        pred = model.predict(x)
        out = float(pred[0]) if pred is not None and len(pred) else float("nan")
    except Exception:
        return None
    return out if math.isfinite(out) else None


def try_log_shadow_ml_eod_prediction(
    executor: Any,
    symbol: str,
    side: str,
    entry_components: Any,
    entry_score: float,
    market_regime: str,
    *,
    log_event: Callable[..., None],
    jsonl_write: Callable[..., None],
) -> None:
    """Telemetry-only: log ml_expected_eod_return to run.jsonl + submit_entry stream."""
    flag = (os.environ.get("ALPACA_SHADOW_ML_TELEMETRY_ONLY") or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return
    comps = entry_components if isinstance(entry_components, dict) else {}
    api = getattr(executor, "api", None)
    try:
        yhat = predict_expected_eod_return(
            symbol=symbol,
            entry_components=comps,
            entry_score=float(entry_score),
            market_regime=str(market_regime or ""),
            api=api,
        )
    except Exception as e:
        log_event("submit_entry", "alpaca_shadow_ml_error", symbol=symbol, error=str(e)[:400])
        return
    if yhat is None:
        return
    try:
        jsonl_write(
            "run",
            {
                "msg": "alpaca_shadow_ml",
                "symbol": symbol,
                "side": side,
                "ml_expected_eod_return": float(yhat),
                "shadow_only": True,
                "market_regime": str(market_regime or ""),
            },
        )
    except Exception:
        pass
    try:
        log_event(
            "submit_entry",
            "alpaca_shadow_ml_telemetry",
            symbol=symbol,
            side=side,
            ml_expected_eod_return=float(yhat),
            shadow_only=True,
            market_regime=str(market_regime or ""),
        )
    except Exception:
        pass
