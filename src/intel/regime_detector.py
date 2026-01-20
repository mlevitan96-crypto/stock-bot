#!/usr/bin/env python3
"""
Regime detection engine (additive, v2-oriented)
===============================================

This is intentionally conservative: it consumes already-produced context/state and
produces a stable `state/regime_state.json` snapshot for v2 scoring and dashboards.

Contract:
- Must never crash the engine (safe defaults).
- Output written to `state/regime_state.json`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from utils.state_io import read_json_self_heal


OUT_PATH = Path("state/regime_state.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        return


def _classify(market_context: Dict[str, Any], posture_state: Dict[str, Any]) -> Tuple[str, float]:
    # Use existing posture/regime confidence as primary.
    posture = str((posture_state or {}).get("posture", "neutral") or "neutral").lower()
    conf = float((posture_state or {}).get("regime_confidence", 0.0) or 0.0)
    vol_regime = str((market_context or {}).get("volatility_regime", "mid") or "mid").lower()

    if posture in ("short", "bear"):
        return ("RISK_OFF" if vol_regime in ("high", "elevated") else "BEAR"), conf
    if posture in ("long", "bull"):
        return ("RISK_ON" if vol_regime in ("low", "mid") else "MIXED"), conf
    return ("NEUTRAL", max(0.25, conf))


def compute_regime_state() -> Dict[str, Any]:
    market = read_json_self_heal("state/market_context_v2.json", default={}, heal=True, mkdir=True)
    posture = read_json_self_heal("state/regime_posture_state.json", default={}, heal=True, mkdir=True)
    label, conf = _classify(market if isinstance(market, dict) else {}, posture if isinstance(posture, dict) else {})
    return {
        "_meta": {"ts": _now_iso(), "version": "2026-01-20_regime_v1"},
        "regime_label": label,
        "regime_confidence": round(float(conf), 4),
        "inputs": {
            "volatility_regime": str((market or {}).get("volatility_regime", "")),
            "market_trend": str((market or {}).get("market_trend", "")),
            "posture": str((posture or {}).get("posture", "")),
            "posture_confidence": round(float((posture or {}).get("regime_confidence", 0.0) or 0.0), 4),
        },
    }


def write_regime_state() -> Dict[str, Any]:
    doc = compute_regime_state()
    _atomic_write(OUT_PATH, doc)
    return doc


def read_regime_state() -> Dict[str, Any]:
    d = read_json_self_heal(OUT_PATH, default={}, heal=True, mkdir=True)
    return d if isinstance(d, dict) else {}


def regime_alignment_score(regime_label: str, direction: str) -> float:
    """
    Returns alignment in [-1, +1] for direction vs regime.
    direction: bullish|bearish|neutral
    """
    r = str(regime_label or "").upper()
    d = str(direction or "").lower()
    if d not in ("bullish", "bearish"):
        return 0.0
    if r in ("RISK_ON",) and d == "bullish":
        return 1.0
    if r in ("RISK_OFF", "BEAR") and d == "bearish":
        return 1.0
    if r in ("NEUTRAL", "MIXED"):
        return 0.25
    return -1.0

