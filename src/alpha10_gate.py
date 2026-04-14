"""
Alpha 10 live gate: veto entries when predicted exit_mfe_pct (RF) is below a floor.

Fail-open on any load/predict error. Configure:
  ALPHA10_GATE_ENABLED   default 1  (set 0 to disable)
  ALPHA10_MIN_MFE_PCT    default 0.2  (percent points of MFE; same units as training target)
  ALPHA10_MODEL_PATH     optional override for joblib path
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional, Tuple

from utils.system_events import log_system_event


def _truthy_env(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _min_mfe_pct() -> float:
    raw = os.environ.get("ALPHA10_MIN_MFE_PCT", "0.2").strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.2
    return v


def check_alpha10_mfe_gate(
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
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Returns (allowed, block_reason_or_none, predicted_mfe_or_none).

    - If gate disabled: (True, None, None).
    - If inference fails: fail-open (True, None, None) + CRITICAL log.
    - If predicted MFE < floor: (False, 'alpha10_mfe_too_low', pred).
    """
    if not _truthy_env("ALPHA10_GATE_ENABLED", "1"):
        return True, None, None

    try:
        from src.ml.alpha10_inference import build_entry_telemetry_row, predict_mfe

        telem = build_entry_telemetry_row(
            symbol=symbol,
            side=side,
            score=float(score),
            comps=comps if isinstance(comps, dict) else {},
            cluster=cluster if isinstance(cluster, dict) else {},
            market_context=market_context if isinstance(market_context, dict) else {},
            regime_posture=regime_posture if isinstance(regime_posture, dict) else {},
            symbol_risk=symbol_risk if isinstance(symbol_risk, dict) else {},
            api=api,
        )
        pred = float(predict_mfe(telem))
        floor = _min_mfe_pct()
        if pred < floor:
            return False, "alpha10_mfe_too_low", pred
        return True, None, pred
    except Exception as e:
        log_system_event(
            "alpha10_gate",
            "inference_fail_open",
            "CRITICAL",
            symbol=str(symbol).upper(),
            details={"error": str(e)[:500]},
        )
        return True, None, None
