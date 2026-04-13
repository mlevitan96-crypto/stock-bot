"""
Live inference for Alpha-10 / live_whale XGBoost (JSON booster).

Maps websocket-era feature dicts into the model's fixed column order; missing
columns impute to 0.0 to match training (``train_xgboost_brain`` / cohort prep).

Self-healing: ``predict_proba_sync`` hot-reloads the booster once on inference failure;
repeated failure sets ``status == \"CRITICAL_FAILURE\"`` and notifies operators (Telegram).
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL = _REPO_ROOT / "models" / "live_whale_v1.json"

logger = logging.getLogger(__name__)


def _flatten_leaves(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Nested dicts -> underscore paths; scalars at leaves (same contract as training flattener)."""
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


def _numeric_flat_from_nested(obj: Any, prefix: str) -> Dict[str, float]:
    """Match ``prepare_training_data._numeric_flat_from_nested`` (numeric leaves only)."""
    raw = _flatten_leaves(obj, prefix) if isinstance(obj, dict) and obj else {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            try:
                x = float(v)
            except (TypeError, ValueError):
                continue
            if math.isfinite(x):
                out[str(k)] = x
            continue
        if v is not None and str(v).strip() != "":
            try:
                x = float(v)
            except (TypeError, ValueError):
                continue
            if math.isfinite(x):
                out[str(k)] = x
    return out


def build_live_whale_feature_dict(
    entry_components: Any,
    *,
    entry_uw: Optional[Mapping[str, Any]] = None,
    exit_uw: Optional[Mapping[str, Any]] = None,
) -> Dict[str, float]:
    """
    Flatten live snapshots into training-style keys (snap_*, euw_*, xuw_*).

    At entry, ``exit_uw`` is omitted; ``xuw_*`` impute to 0.0 at inference time.
    """
    feats: Dict[str, float] = {}
    feats.update(_numeric_flat_from_nested(entry_components, "snap"))
    if entry_uw is not None:
        feats.update(_numeric_flat_from_nested(dict(entry_uw), "euw"))
    if exit_uw is not None:
        feats.update(_numeric_flat_from_nested(dict(exit_uw), "xuw"))
    return feats


class LiveModelEngine:
    """
    Loads ``live_whale_v1.json`` (XGBoost JSON). Probabilities clipped to [0, 1].

    ``status``: ``OK`` | ``CRITICAL_FAILURE`` (inference exhausted retries).

    Use ``predict_proba_sync`` from synchronous trading code; ``predict_async`` wraps
    the same work in ``asyncio.to_thread`` for async call sites.
    """

    def __init__(self, model_path: Optional[Path] = None) -> None:
        self._model_path = Path(model_path) if model_path is not None else _DEFAULT_MODEL
        self._booster: Any = None
        self._feature_names: List[str] = []
        self.load_error: Optional[str] = None
        self.status: str = "OK"
        self._last_inference_error: Optional[str] = None
        self._critical_telegram_sent: bool = False
        self._load()

    def _load(self) -> None:
        try:
            import xgboost as xgb  # type: ignore
        except ImportError as e:
            self.load_error = f"xgboost_import:{e}"
            self._booster = None
            self._feature_names = []
            return
        p = self._model_path
        if not p.is_file():
            self.load_error = f"missing_model:{p}"
            self._booster = None
            self._feature_names = []
            return
        try:
            booster = xgb.Booster()
            booster.load_model(str(p))
            names = list(booster.feature_names or [])
            if not names:
                self.load_error = "empty_feature_names"
                self._booster = None
                self._feature_names = []
                return
            self._booster = booster
            self._feature_names = names
            self.load_error = None
        except Exception as e:
            self.load_error = str(e)
            self._booster = None
            self._feature_names = []

    def hot_reload(self) -> bool:
        """
        Re-initialize the XGBoost booster from ``models/live_whale_v1.json`` (or configured path).

        Returns True if the model is loaded and usable. Resets ``CRITICAL_FAILURE`` when successful.
        """
        self._load()
        if self.available:
            self.status = "OK"
            self._critical_telegram_sent = False
            self._last_inference_error = None
            return True
        return False

    @property
    def available(self) -> bool:
        return self._booster is not None and bool(self._feature_names)

    @property
    def feature_count(self) -> int:
        return len(self._feature_names)

    def _row_vector(self, features: Mapping[str, Any]) -> Any:
        import numpy as np

        row = np.zeros((1, len(self._feature_names)), dtype=np.float64)
        for j, name in enumerate(self._feature_names):
            v = features.get(name)
            if v is None:
                continue
            try:
                x = float(v)
            except (TypeError, ValueError):
                continue
            if math.isfinite(x):
                row[0, j] = x
        return row

    def _predict_once(self, features: Mapping[str, Any]) -> float:
        import xgboost as xgb  # type: ignore

        row = self._row_vector(features)
        dm = xgb.DMatrix(row, feature_names=self._feature_names)
        raw = self._booster.predict(dm)
        p = float(raw[0]) if hasattr(raw, "__len__") else float(raw)
        if not math.isfinite(p):
            raise ValueError("non_finite_prediction")
        return max(0.0, min(1.0, p))

    def _set_critical_failure(self, detail: str) -> None:
        self.status = "CRITICAL_FAILURE"
        self._last_inference_error = (detail or "")[:2000]
        self._booster = None
        self._feature_names = []
        if not self._critical_telegram_sent:
            self._critical_telegram_sent = True
            try:
                from telemetry.alpaca_ml_shadow_alerts import notify_ml_engine_critical_failure

                notify_ml_engine_critical_failure(detail)
            except Exception:
                pass

    def predict_proba_sync(self, features: Mapping[str, Any]) -> Optional[float]:
        """
        Return P(positive class) in [0, 1], or None if the engine is unavailable.

        On inference error: log, ``hot_reload()``, retry once; on second failure
        set ``status`` to ``CRITICAL_FAILURE`` and return None.

        Missing model columns are treated as 0.0 (``_row_vector`` only sets known keys).
        """
        if self.status == "CRITICAL_FAILURE":
            if self.hot_reload() and self.available:
                pass
            else:
                return None

        if not self.available:
            return None

        try:
            return self._predict_once(features)
        except Exception as e1:
            logger.warning("ML Inference failed. Attempting hot-reload... (%s)", e1)
            self.hot_reload()
            if not self.available:
                self._set_critical_failure(str(e1))
                return None
            try:
                return self._predict_once(features)
            except Exception as e2:
                self._set_critical_failure(f"{e1!s}; after_reload:{e2!s}")
                return None

    async def predict_async(self, features: Mapping[str, Any]) -> Optional[float]:
        return await asyncio.to_thread(self.predict_proba_sync, features)
