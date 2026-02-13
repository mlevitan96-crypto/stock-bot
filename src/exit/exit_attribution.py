#!/usr/bin/env python3
"""
Exit Attribution Engine (v2)
============================

Contract:
- Additive only; MUST NOT affect execution decisions.
- Append-only output: logs/exit_attribution.jsonl
- Must never raise inside execution paths.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.signal_normalization import normalize_signals

from src.exit.exit_attribution_enrich import enrich_exit_row


# Allow regression runs to isolate log outputs (prevents polluting droplet logs).
OUT = Path(os.environ.get("EXIT_ATTRIBUTION_LOG_PATH", "logs/exit_attribution.jsonl"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_exit_attribution(rec: Dict[str, Any]) -> None:
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        # Defensive: if signals are ever passed through, ensure schema correctness.
        if isinstance(rec, dict) and "signals" in rec:
            rec = dict(rec)
            rec["signals"] = normalize_signals(rec.get("signals"))
        # MODE/STRATEGY/REGIME ENRICHMENT (governance-grade bucketing)
        try:
            rec = enrich_exit_row(rec, position=None, order=None, context=None)
        except Exception:
            pass
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def build_exit_attribution_record(
    *,
    symbol: str,
    entry_timestamp: str,
    exit_reason: str,
    pnl: Optional[float],
    pnl_pct: Optional[float] = None,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    qty: Optional[float] = None,
    time_in_trade_minutes: Optional[float],
    entry_uw: Dict[str, Any],
    exit_uw: Dict[str, Any],
    entry_regime: str,
    exit_regime: str,
    entry_sector_profile: Dict[str, Any],
    exit_sector_profile: Dict[str, Any],
    score_deterioration: float,
    relative_strength_deterioration: float,
    v2_exit_score: float,
    v2_exit_components: Dict[str, Any],
    replacement_candidate: Optional[str] = None,
    replacement_reasoning: Optional[Dict[str, Any]] = None,
    exit_timestamp: Optional[str] = None,
    variant_id: Optional[str] = None,
    exit_regime_decision: str = "normal",
    exit_regime_reason: str = "",
    exit_regime_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "symbol": str(symbol).upper(),
        "timestamp": exit_timestamp or _now_iso(),
        "entry_timestamp": str(entry_timestamp),
        "exit_reason": str(exit_reason),
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "qty": qty,
        "time_in_trade_minutes": time_in_trade_minutes,
        "entry_uw": dict(entry_uw or {}),
        "exit_uw": dict(exit_uw or {}),
        "entry_regime": str(entry_regime or ""),
        "exit_regime": str(exit_regime or ""),
        "entry_sector_profile": dict(entry_sector_profile or {}),
        "exit_sector_profile": dict(exit_sector_profile or {}),
        "score_deterioration": float(score_deterioration),
        "relative_strength_deterioration": float(relative_strength_deterioration),
        "v2_exit_score": float(v2_exit_score),
        "v2_exit_components": dict(v2_exit_components or {}),
        "replacement_candidate": replacement_candidate,
        "replacement_reasoning": dict(replacement_reasoning or {}) if replacement_reasoning else None,
        "composite_version": "v2",
    }
    if variant_id is not None:
        rec["variant_id"] = str(variant_id)
    rec["exit_regime_decision"] = str(exit_regime_decision or "normal")
    rec["exit_regime_reason"] = str(exit_regime_reason or "")
    rec["exit_regime_context"] = dict(exit_regime_context or {})
    return rec

