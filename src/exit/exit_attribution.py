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
from src.telemetry.equity_price_precision import (
    quantize_telemetry_price,
    quantize_telemetry_pnl_pct,
    quantize_telemetry_pnl_usd,
)


def merge_composite_components_at_entry(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build the entry-time UW / v2 composite component dict for exit rows and audits.

    ``metadata['v2']`` historically held only ``v2_uw_inputs`` / profiles, while
    ``greeks_gamma`` and ``market_tide`` live under ``compute_composite_score_v2``'s
    ``components`` — which were also stored at ``metadata['components']`` for ML,
    but were not copied into ``v2``. Merge top-level ``components``, optional
    ``v2['feature_snapshot']``, then ``v2['components']`` so later keys win (UW v2
    snapshot is authoritative on overlap).
    """
    meta = metadata if isinstance(metadata, dict) else {}
    v2 = meta.get("v2") if isinstance(meta.get("v2"), dict) else {}
    top = meta.get("components") if isinstance(meta.get("components"), dict) else {}
    fs = v2.get("feature_snapshot") if isinstance(v2.get("feature_snapshot"), dict) else {}
    v2c = v2.get("components") if isinstance(v2.get("components"), dict) else {}
    merged: Dict[str, Any] = {}
    merged.update(top)
    merged.update(fs)
    merged.update(v2c)
    return merged


def _telemetry_alert(subsystem: str, event_type: str, severity: str, **fields: Any) -> None:
    """SRE visibility for exit-path I/O failures; must never raise."""
    try:
        from utils.system_events import log_system_event

        log_system_event(subsystem, event_type, severity, **fields)
    except Exception:
        pass


# Allow regression runs to isolate log outputs (prevents polluting droplet logs).
OUT = Path(os.environ.get("EXIT_ATTRIBUTION_LOG_PATH", "logs/exit_attribution.jsonl"))
_EXIT_EVENT_LOG = Path(os.environ.get("EXIT_EVENT_LOG_PATH", "logs/exit_event.jsonl"))
_EXIT_SIGNAL_SNAPSHOT_LOG = Path(os.environ.get("EXIT_SIGNAL_SNAPSHOT_LOG_PATH", "logs/exit_signal_snapshot.jsonl"))

# Schema version for attribution/exit records (docs: ATTRIBUTION_SCHEMA_CANONICAL_V1, ATTRIBUTION_TRUTH_CONTRACT).
ATTRIBUTION_SCHEMA_VERSION = "1.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_exit_event(evt: Dict[str, Any]) -> None:
    """Append unified EXIT_EVENT to logs/exit_event.jsonl (replay / PnL forensics). Never raises."""
    try:
        _EXIT_EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _EXIT_EVENT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, default=str) + "\n")
    except Exception as e:
        _telemetry_alert(
            "exit_attribution",
            "append_exit_event_failed",
            "WARN",
            symbol=str((evt or {}).get("symbol") or "") or None,
            details={"error": str(e)[:400]},
        )
        return


def append_exit_signal_snapshot(rec: Dict[str, Any]) -> None:
    """Append one row to logs/exit_signal_snapshot.jsonl. Never raises."""
    try:
        _EXIT_SIGNAL_SNAPSHOT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _EXIT_SIGNAL_SNAPSHOT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception as e:
        _telemetry_alert(
            "exit_attribution",
            "append_exit_signal_snapshot_failed",
            "WARN",
            symbol=str(rec.get("symbol") or "") or None,
            details={"error": str(e)[:400]},
        )
        return


def append_exit_attribution(rec: Dict[str, Any]) -> None:
    try:
        try:
            from src.telemetry.strict_chain_guard import record_econ_close_chain_checkpoint

            record_econ_close_chain_checkpoint(rec)
        except Exception as e:
            _telemetry_alert(
                "exit_attribution",
                "econ_close_chain_checkpoint_failed",
                "WARN",
                symbol=str(rec.get("symbol") or "") or None,
                details={"error": str(e)[:400]},
            )
        OUT.parent.mkdir(parents=True, exist_ok=True)
        # Defensive: if signals are ever passed through, ensure schema correctness.
        if isinstance(rec, dict) and "signals" in rec:
            rec = dict(rec)
            rec["signals"] = normalize_signals(rec.get("signals"))
        # MODE/STRATEGY/REGIME ENRICHMENT (governance-grade bucketing)
        try:
            rec = enrich_exit_row(rec, position=None, order=None, context=None)
        except Exception as e:
            _telemetry_alert(
                "exit_attribution",
                "enrich_exit_row_failed",
                "WARN",
                symbol=str(rec.get("symbol") or "") or None,
                details={"error": str(e)[:400]},
            )
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        try:
            from src.offense.streak_breaker import register_closed_trade_pnl

            _pnl_reg = rec.get("pnl")
            if _pnl_reg is None:
                _pnl_reg = rec.get("realized_pnl_usd")
            register_closed_trade_pnl(_pnl_reg)
        except Exception:
            pass
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
            from src.telemetry.attribution_emit_keys import get_symbol_attribution_keys

            _trade_key = rec.get("trade_key") or None
            if not _trade_key and _sym and _entry_ts:
                try:
                    _trade_key = build_trade_key(_sym, _side, _entry_ts)
                except Exception:
                    _trade_key = None
            if not _trade_key:
                try:
                    _trade_key = build_trade_key(_sym or "?", _side, _entry_ts or _now_iso())
                except Exception:
                    _trade_key = f"{str(_sym).upper()}|LONG|0"
            _ak = get_symbol_attribution_keys(_sym)
            # Prefer row ``trade_key`` (entry_ts-aligned) over a stale persisted canonical.
            _canon = rec.get("trade_key") or rec.get("canonical_trade_id") or _ak.get("canonical_trade_id") or _trade_key
            _pnl = rec.get("pnl")
            _fees_raw = rec.get("fees_usd")
            if _fees_raw is None:
                _fees_raw = rec.get("fee_usd")
            if _fees_raw is None:
                _fees_raw = rec.get("commission_usd")
            try:
                _fees_emit = abs(float(_fees_raw)) if _fees_raw is not None else 0.0
            except (TypeError, ValueError):
                _fees_emit = 0.0
            emit_exit_attribution(
                trade_id=trade_id,
                symbol=_sym,
                winner=rec.get("exit_reason", ""),
                winner_explanation=rec.get("exit_regime_reason") or "",
                trade_key=_trade_key,
                canonical_trade_id=str(_canon) if _canon is not None else None,
                terminal_close=True,
                realized_pnl_usd=float(_pnl) if _pnl is not None else None,
                fees_usd=float(_fees_emit),
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
            except Exception as e2:
                _telemetry_alert(
                    "exit_attribution",
                    "unified_exit_emit_learning_blocker_failed",
                    "WARN",
                    symbol=sym_fb,
                    details={"error": str(e2)[:400]},
                )
        # CTR mirror (Phase 1: when TRUTH_ROUTER_ENABLED=1)
        try:
            from src.infra.truth_router import append_jsonl as ctr_append
            ctr_append("exits/exit_attribution.jsonl", rec, expected_max_age_sec=600)
        except Exception as e:
            _telemetry_alert(
                "exit_attribution",
                "truth_router_exit_attribution_mirror_failed",
                "WARN",
                symbol=str(rec.get("symbol") or "") or None,
                details={"error": str(e)[:400]},
            )
    except Exception as e:
        _telemetry_alert(
            "exit_attribution",
            "append_exit_attribution_outer_failed",
            "ERROR",
            symbol=str((rec or {}).get("symbol") or "") or None,
            details={"error": str(e)[:500]},
        )
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
        "pnl": quantize_telemetry_pnl_usd(pnl, ref_price=entry_price) if pnl is not None else None,
        "pnl_pct": quantize_telemetry_pnl_pct(pnl_pct, ref_price=entry_price) if pnl_pct is not None else None,
        "entry_price": quantize_telemetry_price(entry_price) if entry_price is not None else None,
        "exit_price": quantize_telemetry_price(exit_price) if exit_price is not None else None,
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

