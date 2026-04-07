"""
Alpaca attribution emitter — entry and exit.
Additive only; MUST NOT affect execution. Never raise in hot paths.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.telemetry.alpaca_attribution_schema import (
    SCHEMA_VERSION,
    entry_attribution_shape,
    exit_attribution_shape,
    validate_entry_attribution,
    validate_exit_attribution,
)
from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side, normalize_symbol

REPO = Path(__file__).resolve().parents[2]
LOG_DIR = REPO / "logs"


def _entry_log_path() -> Path:
    return Path(os.environ.get("ALPACA_ENTRY_ATTRIBUTION_PATH", str(LOG_DIR / "alpaca_entry_attribution.jsonl")))


def _exit_log_path() -> Path:
    return Path(os.environ.get("ALPACA_EXIT_ATTRIBUTION_PATH", str(LOG_DIR / "alpaca_exit_attribution.jsonl")))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(
    path: Path,
    rec: Dict[str, Any],
    *,
    symbol: str = "",
    purpose: str = "",
) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception as ex:
        try:
            from telemetry.learning_blocker_emit import emit_learning_blocker

            emit_learning_blocker(
                "alpaca_jsonl_append_failed",
                str(symbol or ""),
                path=str(path),
                purpose=str(purpose or ""),
                error=str(ex)[:500],
            )
        except Exception:
            pass


def _maybe_diag_unified_exit_emit(trade_id: str, unified_path: Path, ok: bool, detail: str = "") -> None:
    """Optional run.jsonl line when ALPACA_UNIFIED_EXIT_EMIT_DIAG=1 (additive diagnostics)."""
    if os.environ.get("ALPACA_UNIFIED_EXIT_EMIT_DIAG", "").strip() != "1":
        return
    try:
        runp = REPO / "logs" / "run.jsonl"
        runp.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "event_type": "alpaca_unified_exit_emit_attempt",
            "trade_id": str(trade_id),
            "unified_path": str(unified_path),
            "ok": bool(ok),
            "detail": (detail or "")[:800],
            "ts": _now_iso(),
        }
        with runp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except Exception:
        pass


def _to_float(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _entry_dominant_and_margin(
    contributions: Dict[str, float],
    composite_score: Optional[float],
    entry_threshold: Optional[float],
) -> tuple[Optional[str], Optional[float], Optional[float]]:
    """Return (dominant_component_name, dominant_value, margin_to_threshold)."""
    dominant_name, dominant_value = None, None
    if contributions:
        by_abs = sorted(contributions.items(), key=lambda kv: abs(_to_float(kv[1])), reverse=True)
        if by_abs:
            dominant_name = by_abs[0][0]
            dominant_value = _to_float(by_abs[0][1])
    margin = None
    if composite_score is not None and entry_threshold is not None:
        margin = round(_to_float(composite_score) - _to_float(entry_threshold), 6)
    return dominant_name, dominant_value, margin


def emit_entry_attribution(
    trade_id: str,
    symbol: str,
    side: str,
    decision: str,
    decision_reason: str = "",
    *,
    trade_key: Optional[str] = None,
    raw_signals: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None,
    contributions: Optional[Dict[str, float]] = None,
    composite_score: Optional[float] = None,
    entry_threshold: Optional[float] = None,
    gates: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    schema_role: Optional[str] = None,
    is_repair_row: bool = False,
) -> None:
    """Emit one entry_attribution event. Truth: contributions = weight*raw_signal; composite_score asserted; trade_key for join. Never raises."""
    ts = timestamp or _now_iso()
    if trade_key:
        key = trade_key
    else:
        try:
            key = build_trade_key(symbol, side, ts)
        except Exception:
            key = f"{normalize_symbol(symbol)}|{normalize_side(side or 'LONG')}|0"
    raw = dict(raw_signals or {})
    w = dict(weights or {})
    contrib = dict(contributions or {})
    if not contrib and raw and w:
        for k in raw:
            if k in w:
                contrib[k] = round(_to_float(w[k]) * _to_float(raw[k]), 6)
            else:
                contrib[k] = round(_to_float(raw[k]), 6)
    elif not contrib and raw:
        for k, v in raw.items():
            contrib[k] = round(_to_float(v), 6)
    comp_score = composite_score
    if comp_score is None and contrib:
        comp_score = round(sum(contrib.values()), 6)
    dom_name, dom_val, margin = _entry_dominant_and_margin(contrib, comp_score, entry_threshold)
    base = entry_attribution_shape()
    base["trade_id"] = str(trade_id)
    base["trade_key"] = str(key)
    base["symbol"] = str(symbol).upper()
    base["side"] = str(side).upper() if side else "LONG"
    base["decision"] = str(decision)
    base["decision_reason"] = str(decision_reason or "")
    base["timestamp"] = ts
    base["canonical_trade_id"] = str(key)
    base["fees_usd"] = 0.0
    base["raw_signals"] = raw
    base["weights"] = w
    base["contributions"] = contrib
    base["composite_score"] = comp_score
    base["entry_dominant_component"] = dom_name
    base["entry_dominant_component_value"] = dom_val
    base["entry_margin_to_threshold"] = margin
    if gates is not None:
        base["gates"] = {k: {"pass": v.get("pass"), "reason": str(v.get("reason", ""))} for k, v in (gates or {}).items()}
    if schema_role:
        base["schema_role"] = str(schema_role)
    if is_repair_row:
        base["is_repair_row"] = True
    base["schema_version"] = SCHEMA_VERSION
    entry_issues = validate_entry_attribution(base)
    if entry_issues:
        try:
            from telemetry.learning_blocker_emit import emit_learning_blocker

            emit_learning_blocker(
                "alpaca_entry_validation_blocked",
                str(symbol),
                issues=entry_issues[:12],
            )
        except Exception:
            pass
        return
    _append_jsonl(_entry_log_path(), base, symbol=str(symbol), purpose="dedicated_entry_attribution")
    if LOG_DIR.exists():
        unified_rec = {"event_type": "alpaca_entry_attribution", **base}
        _append_jsonl(
            LOG_DIR / "alpaca_unified_events.jsonl",
            unified_rec,
            symbol=str(symbol),
            purpose="alpaca_unified_entry",
        )


def _exit_dominant_and_margins(
    exit_contributions: Dict[str, float],
    pressure: Optional[float],
    threshold_normal: Optional[float],
    threshold_urgent: Optional[float],
) -> tuple[Optional[str], Optional[float], Optional[float], Optional[float]]:
    """Return (dominant_name, dominant_value, margin_exit_now, margin_exit_soon)."""
    dom_name, dom_val = None, None
    if exit_contributions:
        by_abs = sorted(exit_contributions.items(), key=lambda kv: abs(_to_float(kv[1])), reverse=True)
        if by_abs:
            dom_name = by_abs[0][0]
            dom_val = _to_float(by_abs[0][1])
    margin_now = (round(_to_float(pressure) - _to_float(threshold_normal), 6) if pressure is not None and threshold_normal is not None else None)
    margin_soon = (round(_to_float(pressure) - _to_float(threshold_urgent), 6) if pressure is not None and threshold_urgent is not None else None)
    return dom_name, dom_val, margin_now, margin_soon


def emit_exit_attribution(
    trade_id: str,
    symbol: str,
    winner: str,
    winner_explanation: str = "",
    *,
    trade_key: Optional[str] = None,
    canonical_trade_id: Optional[str] = None,
    terminal_close: bool = False,
    realized_pnl_usd: Optional[float] = None,
    fees_usd: float = 0.0,
    exit_components_raw: Optional[Dict[str, Any]] = None,
    exit_weights: Optional[Dict[str, float]] = None,
    exit_contributions: Optional[Dict[str, float]] = None,
    exit_pressure_total: Optional[float] = None,
    thresholds_used: Optional[Dict[str, float]] = None,
    eligible_mechanisms: Optional[Dict[str, bool]] = None,
    snapshot: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    entry_time_iso: Optional[str] = None,
    side: Optional[str] = None,
) -> None:
    """Emit one exit_attribution event. Sets dominant component and pressure margins; trade_key for join. Never raises."""
    thr = dict(thresholds_used or {})
    snap = dict(snapshot or exit_attribution_shape()["snapshot"])
    snap.setdefault("pnl_unrealized", None)
    snap.setdefault("mfe_pct_so_far", None)
    snap.setdefault("mae_pct_so_far", None)
    contrib = dict(exit_contributions or {})
    dom_name, dom_val, margin_now, margin_soon = _exit_dominant_and_margins(
        contrib, exit_pressure_total, thr.get("normal"), thr.get("urgent")
    )
    if trade_key:
        key = trade_key
    else:
        et_src = entry_time_iso or timestamp or _now_iso()
        try:
            key = build_trade_key(symbol, side or "LONG", et_src)
        except Exception:
            key = f"{normalize_symbol(symbol)}|{normalize_side(side or 'LONG')}|0"
    base = exit_attribution_shape()
    base["trade_id"] = str(trade_id)
    base["trade_key"] = str(key)
    base["symbol"] = str(symbol).upper()
    base["winner"] = str(winner)
    base["winner_explanation"] = str(winner_explanation or "")
    base["timestamp"] = timestamp or _now_iso()
    base["exit_components_raw"] = dict(exit_components_raw or base["exit_components_raw"])
    base["exit_weights"] = dict(exit_weights or {})
    base["exit_contributions"] = contrib
    base["exit_pressure_total"] = exit_pressure_total
    base["exit_dominant_component"] = dom_name
    base["exit_dominant_component_value"] = dom_val
    base["exit_pressure_margin_exit_now"] = margin_now
    base["exit_pressure_margin_exit_soon"] = margin_soon
    base["thresholds_used"] = thr
    base["eligible_mechanisms"] = dict(eligible_mechanisms or base["eligible_mechanisms"])
    base["snapshot"] = snap
    base["schema_version"] = SCHEMA_VERSION
    base["canonical_trade_id"] = str(canonical_trade_id or key)
    base["terminal_close"] = bool(terminal_close)
    if realized_pnl_usd is not None:
        base["realized_pnl_usd"] = float(realized_pnl_usd)
    base["fees_usd"] = float(fees_usd)
    exit_issues = validate_exit_attribution(base)
    unified_p = LOG_DIR / "alpaca_unified_events.jsonl"
    if exit_issues:
        try:
            from telemetry.learning_blocker_emit import emit_learning_blocker

            emit_learning_blocker(
                "alpaca_exit_validation_blocked",
                str(symbol),
                issues=exit_issues[:12],
            )
        except Exception:
            pass
        _maybe_diag_unified_exit_emit(str(trade_id), unified_p, False, "validation:" + ";".join(exit_issues[:5]))
        try:
            fail_p = LOG_DIR / "alpaca_emit_failures.jsonl"
            fail_p.parent.mkdir(parents=True, exist_ok=True)
            with fail_p.open("a", encoding="utf-8") as ff:
                ff.write(
                    json.dumps(
                        {
                            "kind": "exit_validation_blocked",
                            "trade_id": str(trade_id),
                            "symbol": str(symbol),
                            "issues": exit_issues[:20],
                            "ts": _now_iso(),
                        },
                        default=str,
                    )
                    + "\n"
                )
        except Exception:
            pass
        return
    _append_jsonl(_exit_log_path(), base, symbol=str(symbol), purpose="dedicated_exit_attribution")
    if LOG_DIR.exists():
        unified_rec = {"event_type": "alpaca_exit_attribution", **base}
        _append_jsonl(unified_p, unified_rec, symbol=str(symbol), purpose="alpaca_unified_exit")
        _maybe_diag_unified_exit_emit(str(trade_id), unified_p, True, "written")
