#!/usr/bin/env python3
"""
Shadow PnL Reconstruction (OPTIONAL, additive)
=============================================

Goal:
- Maintain a hypothetical shadow position ledger (v2) and compute unrealized/realized PnL.
- Emit PnL and exit events to:
  - logs/shadow.jsonl
  - logs/system_events.jsonl (subsystem="shadow_pnl")

Constraints:
- Must NEVER submit real orders.
- Must NEVER modify v1 decisions or live trading logic.
- Must be defensive: never raise, never block.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from config.registry import StateFiles, atomic_write_json, read_json, Thresholds
except Exception:  # pragma: no cover
    StateFiles = None  # type: ignore
    atomic_write_json = None  # type: ignore
    read_json = None  # type: ignore
    Thresholds = None  # type: ignore

try:
    from telemetry.shadow_ab import log_shadow_event
except Exception:  # pragma: no cover
    def log_shadow_event(*args, **kwargs):  # type: ignore
        return None

try:
    from utils.system_events import global_failure_wrapper, log_system_event
except Exception:  # pragma: no cover
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d

    def log_system_event(*args, **kwargs):  # type: ignore
        return None


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


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _parse_iso(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        s = str(ts).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _ledger_default() -> Dict[str, Any]:
    return {"positions": []}


def load_shadow_ledger() -> Dict[str, Any]:
    """
    Read shadow position ledger from state/shadow_positions.json.
    Never raises.
    """
    try:
        if StateFiles is None or not hasattr(StateFiles, "SHADOW_POSITIONS") or read_json is None:
            return _ledger_default()
        data = read_json(StateFiles.SHADOW_POSITIONS, default=_ledger_default())  # type: ignore[attr-defined]
        if isinstance(data, dict) and isinstance(data.get("positions"), list):
            return data
        return _ledger_default()
    except Exception:
        return _ledger_default()


def save_shadow_ledger(ledger: Dict[str, Any]) -> None:
    """
    Persist ledger atomically. Never raises.
    """
    try:
        if StateFiles is None or not hasattr(StateFiles, "SHADOW_POSITIONS") or atomic_write_json is None:
            return
        if not isinstance(ledger, dict):
            return
        if "positions" not in ledger or not isinstance(ledger.get("positions"), list):
            return
        atomic_write_json(StateFiles.SHADOW_POSITIONS, ledger)  # type: ignore[attr-defined]
    except Exception:
        return


def _normalize_side(side: Any) -> str:
    s = str(side or "").strip().lower()
    if s in ("long", "buy"):
        return "long"
    if s in ("short", "sell"):
        return "short"
    return "long"


def _merge_or_add_position(
    positions: List[Dict[str, Any]],
    *,
    symbol: str,
    qty: int,
    entry_price: float,
    entry_ts: str,
    side: str,
) -> None:
    """
    Merge into existing symbol+side position (weighted avg entry), otherwise append.
    """
    sym = str(symbol).upper()
    s = _normalize_side(side)
    q = max(0, int(qty))
    if q <= 0:
        return
    ep = _safe_float(entry_price, 0.0)
    if ep <= 0:
        return

    for p in positions:
        try:
            if str(p.get("symbol", "")).upper() != sym:
                continue
            if _normalize_side(p.get("side")) != s:
                continue
            old_qty = _safe_int(p.get("qty"), 0)
            old_ep = _safe_float(p.get("entry_price"), 0.0)
            new_qty = old_qty + q
            if new_qty <= 0:
                continue
            # weighted average entry
            if old_qty > 0 and old_ep > 0:
                new_ep = ((old_qty * old_ep) + (q * ep)) / float(new_qty)
            else:
                new_ep = ep
            p["qty"] = int(new_qty)
            p["entry_price"] = float(new_ep)
            # Keep earliest entry_ts (for stale-alpha time exits)
            try:
                old_ts = _parse_iso(p.get("entry_ts"))
                new_ts = _parse_iso(entry_ts)
                if old_ts and new_ts and new_ts < old_ts:
                    p["entry_ts"] = entry_ts
            except Exception:
                pass
            return
        except Exception:
            continue

    positions.append(
        {
            "symbol": sym,
            "qty": int(q),
            "entry_price": float(ep),
            "entry_ts": str(entry_ts),
            "side": s,
        }
    )


def compute_unrealized_pnl(position: Dict[str, Any], current_price: float) -> float:
    qty = _safe_int(position.get("qty"), 0)
    entry = _safe_float(position.get("entry_price"), 0.0)
    cur = _safe_float(current_price, 0.0)
    side = _normalize_side(position.get("side"))
    if qty <= 0 or entry <= 0 or cur <= 0:
        return 0.0
    if side == "short":
        return (entry - cur) * qty
    return (cur - entry) * qty


def compute_realized_pnl(position: Dict[str, Any], exit_price: float) -> float:
    return compute_unrealized_pnl(position, exit_price)


@global_failure_wrapper("shadow_pnl")
def record_shadow_executed(
    *,
    symbol: str,
    qty: int,
    entry_price: float,
    side: str,
    entry_ts: Optional[str] = None,
) -> None:
    """
    Update ledger when a hypothetical shadow order is marked executed.
    """
    ts = entry_ts or _now_iso()
    ledger = load_shadow_ledger()
    positions = ledger.get("positions", [])
    if not isinstance(positions, list):
        positions = []
        ledger["positions"] = positions

    _merge_or_add_position(
        positions,
        symbol=symbol,
        qty=qty,
        entry_price=entry_price,
        entry_ts=ts,
        side=side,
    )
    save_shadow_ledger(ledger)

    # Observability
    try:
        log_shadow_event(
            "shadow_ledger_update",
            symbol=str(symbol).upper(),
            action="add",
            qty=int(qty),
            entry_price=float(entry_price),
            side=_normalize_side(side),
            entry_ts=ts,
            ledger_positions=len(positions),
        )
    except Exception:
        pass
    try:
        log_system_event(
            subsystem="shadow_pnl",
            event_type="shadow_position_opened",
            severity="INFO",
            symbol=str(symbol).upper(),
            details={"qty": int(qty), "entry_price": float(entry_price), "side": _normalize_side(side), "entry_ts": ts},
        )
    except Exception:
        pass


def _fetch_latest_price(api, symbol: str) -> Optional[float]:
    """
    Best-effort latest price fetch using existing bar fetchers.
    """
    try:
        bars = api.get_bars(symbol, "1Min", limit=1)
        df = getattr(bars, "df", None)
        if df is None or df.empty:
            return None
        row = df.iloc[-1]
        px = _safe_float(row.get("close"), 0.0)
        return px if px > 0 else None
    except Exception:
        return None


def _direction_from_ctx(ctx: Dict[str, Any]) -> Optional[str]:
    d = str(ctx.get("direction") or "").strip().lower()
    if d in ("bullish", "bearish"):
        return d
    return None


def _posture_from_state(posture_state: Dict[str, Any]) -> Optional[str]:
    p = str(posture_state.get("posture") or "").strip().lower()
    if p in ("long", "short", "neutral"):
        return p
    return None


@global_failure_wrapper("shadow_pnl")
def shadow_pnl_tick(
    api,
    *,
    signal_context: Optional[Dict[str, Dict[str, Any]]] = None,
    posture_state: Optional[Dict[str, Any]] = None,
    enable_exits: bool = True,
) -> None:
    """
    Compute per-position PnL and optionally trigger hypothetical exits.

    - Reads `state/shadow_positions.json`
    - Fetches latest price for each symbol
    - Logs `shadow_pnl_update` and `shadow_exit` events
    """
    ledger = load_shadow_ledger()
    positions = ledger.get("positions", [])
    if not isinstance(positions, list) or not positions:
        return

    # Lightweight heartbeat for observability (one line per tick).
    try:
        log_shadow_event("shadow_pnl_tick", positions=len(positions))
    except Exception:
        pass
    try:
        log_system_event(
            subsystem="shadow_pnl",
            event_type="tick",
            severity="INFO",
            details={"positions": len(positions)},
        )
    except Exception:
        pass

    sig_ctx = signal_context or {}
    ps = posture_state or {}
    posture = _posture_from_state(ps)

    # Mirror key exit timing defaults from v1 risk thresholds (shadow-only).
    time_exit_min = 240
    stale_pnl_thresh = 0.03
    try:
        if Thresholds is not None:
            time_exit_min = int(getattr(Thresholds, "TIME_EXIT_MINUTES", time_exit_min))
            stale_pnl_thresh = float(getattr(Thresholds, "TIME_EXIT_STALE_PNL_THRESH_PCT", stale_pnl_thresh))
    except Exception:
        pass

    updated_positions: List[Dict[str, Any]] = []
    for p in positions:
        try:
            sym = str(p.get("symbol", "")).upper()
            if not sym:
                continue
            qty = _safe_int(p.get("qty"), 0)
            if qty <= 0:
                continue
            entry_px = _safe_float(p.get("entry_price"), 0.0)
            if entry_px <= 0:
                continue

            cur_px = _fetch_latest_price(api, sym)
            if cur_px is None:
                try:
                    log_shadow_event("shadow_pnl_price_missing", symbol=sym, severity="WARN")
                except Exception:
                    pass
                try:
                    log_system_event(
                        subsystem="shadow_pnl",
                        event_type="price_missing",
                        severity="WARN",
                        symbol=sym,
                        details={"note": "missing_latest_price_skip"},
                    )
                except Exception:
                    pass
                updated_positions.append(p)
                continue

            pnl_usd = compute_unrealized_pnl(p, float(cur_px))
            denom = abs(entry_px * qty) if entry_px > 0 and qty > 0 else 0.0
            pnl_pct = (pnl_usd / denom) if denom > 0 else 0.0

            # Age minutes
            age_min = None
            try:
                dt = _parse_iso(p.get("entry_ts"))
                if dt:
                    age_min = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 60.0)
            except Exception:
                age_min = None

            # Always log PnL update
            try:
                log_shadow_event(
                    "shadow_pnl_update",
                    symbol=sym,
                    qty=int(qty),
                    side=_normalize_side(p.get("side")),
                    entry_price=float(entry_px),
                    entry_ts=p.get("entry_ts"),
                    current_price=float(cur_px),
                    unrealized_pnl_usd=float(round(pnl_usd, 4)),
                    unrealized_pnl_pct=float(round(pnl_pct, 6)),
                    age_min=float(round(age_min, 2)) if age_min is not None else None,
                )
            except Exception:
                pass
            try:
                log_system_event(
                    subsystem="shadow_pnl",
                    event_type="unrealized_update",
                    severity="INFO",
                    symbol=sym,
                    details={
                        "qty": int(qty),
                        "side": _normalize_side(p.get("side")),
                        "entry_price": float(entry_px),
                        "current_price": float(cur_px),
                        "unrealized_pnl_usd": float(round(pnl_usd, 4)),
                        "unrealized_pnl_pct": float(round(pnl_pct, 6)),
                    },
                )
            except Exception:
                pass

            if not enable_exits:
                updated_positions.append(p)
                continue

            # Hypothetical exit logic (shadow-only):
            exit_reason = None

            # 1) Counter-signal: if current signal direction opposes position
            ctx = sig_ctx.get(sym) or {}
            direction = _direction_from_ctx(ctx)
            pos_side = _normalize_side(p.get("side"))
            if direction == "bearish" and pos_side == "long":
                exit_reason = "counter_signal"
            elif direction == "bullish" and pos_side == "short":
                exit_reason = "counter_signal"

            # 2) Regime/posture-based: if posture strongly opposes position
            if exit_reason is None and posture in ("long", "short"):
                if posture == "short" and pos_side == "long":
                    exit_reason = "posture_risk_off"
                elif posture == "long" and pos_side == "short":
                    exit_reason = "posture_risk_on"

            # 3) Stale-alpha (time-based) mirror
            if exit_reason is None and age_min is not None and age_min >= float(time_exit_min):
                if abs(float(pnl_pct)) <= float(stale_pnl_thresh):
                    exit_reason = "stale_alpha"

            if exit_reason is None:
                updated_positions.append(p)
                continue

            # Execute hypothetical exit
            realized = compute_realized_pnl(p, float(cur_px))
            realized_pct = (realized / denom) if denom > 0 else 0.0
            try:
                log_shadow_event(
                    "shadow_exit",
                    symbol=sym,
                    reason=str(exit_reason),
                    qty=int(qty),
                    side=pos_side,
                    entry_price=float(entry_px),
                    entry_ts=p.get("entry_ts"),
                    exit_price=float(cur_px),
                    exit_ts=_now_iso(),
                    realized_pnl_usd=float(round(realized, 4)),
                    realized_pnl_pct=float(round(realized_pct, 6)),
                )
            except Exception:
                pass
            try:
                log_system_event(
                    subsystem="shadow_pnl",
                    event_type="shadow_exit",
                    severity="INFO",
                    symbol=sym,
                    details={
                        "reason": str(exit_reason),
                        "qty": int(qty),
                        "side": pos_side,
                        "entry_price": float(entry_px),
                        "exit_price": float(cur_px),
                        "realized_pnl_usd": float(round(realized, 4)),
                        "realized_pnl_pct": float(round(realized_pct, 6)),
                    },
                )
            except Exception:
                pass

            # Position removed (full close)
            try:
                log_shadow_event("shadow_ledger_update", symbol=sym, action="remove", qty=int(qty), reason=str(exit_reason))
            except Exception:
                pass
        except Exception:
            # Keep existing position on any failure
            try:
                updated_positions.append(p)
            except Exception:
                pass

    ledger["positions"] = updated_positions
    save_shadow_ledger(ledger)

