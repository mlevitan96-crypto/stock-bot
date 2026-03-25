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

# Schema version for attribution/exit records (docs: ATTRIBUTION_SCHEMA_CANONICAL_V1, ATTRIBUTION_TRUTH_CONTRACT).
ATTRIBUTION_SCHEMA_VERSION = "1.0.0"


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
        # Canonical exit attribution (dominant + margins + snapshot)
        try:
            from src.telemetry.alpaca_attribution_emitter import emit_exit_attribution
            trade_id = rec.get("trade_id") or f"open_{rec.get('symbol', '?')}_{rec.get('entry_timestamp', '')}"
            v2_comp = rec.get("v2_exit_components") or {}
            eq = rec.get("exit_quality_metrics") or {}
            snap = {
                "pnl": rec.get("pnl"),
                "pnl_pct": rec.get("pnl_pct"),
                "pnl_unrealized": None,
                "mfe": eq.get("mfe_pct"),
                "mae": eq.get("mae_pct"),
                "mfe_pct_so_far": eq.get("mfe_pct"),
                "mae_pct_so_far": eq.get("mae_pct"),
                "hold_minutes": rec.get("time_in_trade_minutes"),
            }
            exit_weights = rec.get("exit_weights") or {}
            exit_contributions = rec.get("exit_contributions")
            if exit_contributions is None and isinstance(rec.get("attribution_components"), list):
                exit_contributions = {c.get("signal_id", ""): c.get("contribution_to_score", 0) for c in rec.get("attribution_components") if isinstance(c, dict) and c.get("signal_id")}
            if not exit_contributions and v2_comp:
                exit_contributions = {k: float(v) if isinstance(v, (int, float)) else 0.0 for k, v in v2_comp.items()}
            thresholds_used = rec.get("thresholds_used")
            if not isinstance(thresholds_used, dict):
                thresholds_used = {"normal": rec.get("exit_pressure_threshold_normal"), "urgent": rec.get("exit_pressure_threshold_urgent")}
            _sym = rec.get("symbol", "")
            _side = rec.get("side") or rec.get("direction") or "long"
            _entry_ts = rec.get("entry_timestamp") or ""
            from src.telemetry.alpaca_trade_key import build_trade_key
            from telemetry.attribution_emit_keys import get_symbol_attribution_keys

            _trade_key = build_trade_key(_sym, _side, _entry_ts)
            _ak = get_symbol_attribution_keys(_sym)
            _canon = _ak.get("canonical_trade_id") or _trade_key
            _pnl = rec.get("pnl")
            emit_exit_attribution(
                trade_id=trade_id,
                symbol=_sym,
                winner=rec.get("exit_reason", ""),
                winner_explanation=rec.get("exit_regime_reason") or "",
                trade_key=_trade_key,
                canonical_trade_id=str(_canon) if _canon is not None else None,
                terminal_close=True,
                realized_pnl_usd=float(_pnl) if _pnl is not None else None,
                fees_usd=0.0,
                entry_time_iso=_entry_ts,
                side=_side,
                exit_components_raw=dict(v2_comp),
                exit_weights=dict(exit_weights) if exit_weights else None,
                exit_contributions=dict(exit_contributions) if exit_contributions else None,
                exit_pressure_total=rec.get("exit_pressure_total") or rec.get("v2_exit_score"),
                thresholds_used=thresholds_used if thresholds_used else None,
                snapshot=snap,
                timestamp=rec.get("timestamp"),
            )
        except Exception as ex:
            import traceback

            sym_fb = str(rec.get("symbol") or "")
            tb_tail = traceback.format_exc()[-1200:]
            try:
                from telemetry.learning_blocker_emit import emit_learning_blocker

                emit_learning_blocker(
                    "unified_exit_emit_exception",
                    sym_fb,
                    error=str(ex)[:500],
                    traceback_tail=tb_tail,
                )
            except Exception:
                pass
        # CTR mirror (Phase 1: when TRUTH_ROUTER_ENABLED=1)
        try:
            from src.infra.truth_router import append_jsonl as ctr_append
            ctr_append("exits/exit_attribution.jsonl", rec, expected_max_age_sec=600)
        except Exception:
            pass
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
    **kwargs: Any,
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
    # Caller may pass decision_id, exit_quality_metrics, exit_reason_code, trade_id, attribution_components, etc.
    for k, v in kwargs.items():
        rec[k] = v
    return rec

