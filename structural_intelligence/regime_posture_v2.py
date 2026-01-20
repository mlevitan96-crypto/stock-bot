#!/usr/bin/env python3
"""
Regime + Posture V2 (Structural Upgrade)
=======================================

Goal:
- Provide a robust, explicit regime label + directional posture layer that is:
  - separate from scoring and gating (log-only for now)
  - persisted to state/regime_posture_state.json
  - observable via logs/system_events.jsonl

This module MUST NOT change risk posture by itself (no surprise shorting, no size changes).
It only produces context that other layers may consume when explicitly enabled.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    from utils.system_events import global_failure_wrapper, log_system_event
except Exception:  # pragma: no cover
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d

    def log_system_event(*args, **kwargs):  # type: ignore
        return None

try:
    from config.registry import StateFiles, atomic_write_json, read_json
except Exception:  # pragma: no cover
    StateFiles = None  # type: ignore
    atomic_write_json = None  # type: ignore
    read_json = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _read_json(path, default):
    try:
        if read_json is None:
            return default
        d = read_json(path, default=default)
        return d if isinstance(d, dict) else default
    except Exception:
        return default


def read_regime_posture_state(default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if default is None:
        default = {}
    try:
        if StateFiles is None or not hasattr(StateFiles, "REGIME_POSTURE_STATE") or read_json is None:
            return dict(default)
        return _read_json(StateFiles.REGIME_POSTURE_STATE, dict(default))  # type: ignore[attr-defined]
    except Exception:
        return dict(default)


def _infer_regime_label(
    *,
    structural_regime: str,
    structural_conf: float,
    market_context: Dict[str, Any],
) -> Tuple[str, float, str]:
    """
    Map existing inputs into a v2 label set:
    - bull, bear, chop, crash
    """
    sr = (structural_regime or "").upper()
    sc = max(0.0, min(1.0, _safe_float(structural_conf, 0.0)))
    trend = str(market_context.get("market_trend", "flat") or "flat").lower()
    volr = str(market_context.get("volatility_regime", "mid") or "mid").lower()
    risk = str(market_context.get("risk_on_off", "neutral") or "neutral").lower()

    # Primary: structural intelligence regime detector when confident.
    if sr == "PANIC" and sc >= 0.6:
        return "crash", min(1.0, max(sc, 0.75)), "structural_regime:PANIC"
    if sr == "RISK_OFF" and sc >= 0.6:
        # Differentiate bear vs crash using vol proxy
        if volr == "high":
            return "crash", min(1.0, max(sc, 0.7)), "structural_regime:RISK_OFF+high_vol"
        return "bear", sc, "structural_regime:RISK_OFF"
    if sr == "RISK_ON" and sc >= 0.6:
        return "bull", sc, "structural_regime:RISK_ON"

    # Secondary: market context heuristics (tradeable proxies).
    if risk == "risk_off" and volr == "high":
        return "crash", 0.6, "market_context:risk_off+high_vol"
    if risk == "risk_off":
        return "bear", 0.55, "market_context:risk_off"
    if risk == "risk_on" and trend == "up" and volr in ("low", "mid"):
        return "bull", 0.55, "market_context:risk_on"

    # Otherwise chop/neutral
    return "chop", 0.45, "default_chop"


def _infer_posture(regime_label: str, confidence: float) -> Tuple[str, Dict[str, Any]]:
    """
    Posture is directional bias (for downstream gates/scoring), but not enforced here.
    """
    conf = max(0.0, min(1.0, _safe_float(confidence, 0.0)))
    rl = (regime_label or "chop").lower()

    # Conservative defaults: do not recommend short bias unless strong bear/crash.
    posture = "neutral"
    allow_new_longs = True
    tighten_long_exits = False
    prefer_shorts = False

    if rl in ("bear", "crash") and conf >= 0.65:
        posture = "short"
        allow_new_longs = False
        tighten_long_exits = True
        prefer_shorts = True
    elif rl == "bull" and conf >= 0.55:
        posture = "long"
        allow_new_longs = True
        tighten_long_exits = False
        prefer_shorts = False
    else:
        posture = "neutral"

    return posture, {
        "allow_new_longs": bool(allow_new_longs),
        "tighten_long_exits": bool(tighten_long_exits),
        "prefer_shorts": bool(prefer_shorts),
    }


@global_failure_wrapper("regime")
def update_regime_posture_v2(api=None, *, market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compute + persist v2 regime + posture snapshot.
    """
    if market_context is None:
        market_context = {}

    # Try to use structural regime detector (already in codebase), but never require it.
    structural_regime = "NEUTRAL"
    structural_conf = 0.0
    try:
        from structural_intelligence.regime_detector import get_regime_detector

        det = get_regime_detector()
        structural_regime, structural_conf = det.detect_regime()
    except Exception:
        structural_regime, structural_conf = "NEUTRAL", 0.0

    regime_label, regime_conf, regime_source = _infer_regime_label(
        structural_regime=structural_regime,
        structural_conf=structural_conf,
        market_context=market_context,
    )
    posture, posture_flags = _infer_posture(regime_label, regime_conf)

    snapshot: Dict[str, Any] = {
        "ts": _now_iso(),
        "regime_label": regime_label,
        "regime_confidence": round(_safe_float(regime_conf), 4),
        "regime_source": regime_source,
        "structural_regime": structural_regime,
        "structural_confidence": round(_safe_float(structural_conf), 4),
        "posture": posture,
        "posture_flags": posture_flags,
        "market_context": {
            # Keep bounded + stable.
            "market_trend": market_context.get("market_trend"),
            "volatility_regime": market_context.get("volatility_regime"),
            "risk_on_off": market_context.get("risk_on_off"),
            "spy_overnight_ret": market_context.get("spy_overnight_ret"),
            "qqq_overnight_ret": market_context.get("qqq_overnight_ret"),
            "vxx_vxz_ratio": market_context.get("vxx_vxz_ratio"),
            "stale_1m": market_context.get("stale_1m"),
        },
    }

    # Persist
    try:
        if StateFiles is not None and hasattr(StateFiles, "REGIME_POSTURE_STATE") and atomic_write_json is not None:
            atomic_write_json(StateFiles.REGIME_POSTURE_STATE, snapshot)  # type: ignore[attr-defined]
    except Exception as e:
        try:
            log_system_event(
                subsystem="regime",
                event_type="posture_persist_failed",
                severity="ERROR",
                details={"error": str(e)},
            )
        except Exception:
            pass

    # Emit system events (posture update)
    try:
        log_system_event(
            subsystem="regime",
            event_type="posture_update",
            severity="INFO",
            details={
                "regime_label": regime_label,
                "regime_confidence": round(_safe_float(regime_conf), 4),
                "posture": posture,
                "flags": posture_flags,
                "source": regime_source,
            },
        )
    except Exception:
        pass

    return snapshot

