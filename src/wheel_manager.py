#!/usr/bin/env python3
"""
Wheel orchestration: broker reconciliation (assignment), single entry to run the wheel strategy.

``strategies.wheel_strategy`` remains the execution core; this module adds state hygiene and
operator-friendly facades.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger(__name__)


def _position_symbols(positions: List[Any]) -> Set[str]:
    out: Set[str] = set()
    for p in positions or []:
        sym = getattr(p, "symbol", None) or (p.get("symbol") if isinstance(p, dict) else None)
        if sym:
            out.add(str(sym).upper())
    return out


def reconcile_assignments_from_broker(api, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detect CSP assignment: short put leg gone from broker + underlying stock position >= 100 shares.

    Mutates ``state`` (``open_csps``, ``assigned_shares``, ``csp_history``) and persists via
    ``strategies.wheel_strategy._save_wheel_state`` when changes occur.
    """
    import strategies.wheel_strategy as ws

    state = state if isinstance(state, dict) else ws._load_wheel_state()
    try:
        positions = api.list_positions() or []
    except Exception as e:
        log.warning("reconcile_assignments: list_positions failed: %s", e)
        return state

    sym_set = _position_symbols(positions)
    pos_by_symbol = {}
    for p in positions or []:
        sym = getattr(p, "symbol", None) or (p.get("symbol") if isinstance(p, dict) else None)
        if not sym:
            continue
        pos_by_symbol[str(sym).upper()] = p

    open_csps = state.get("open_csps") or {}
    changed = False
    assigned = state.get("assigned_shares") or {}
    csp_history = state.get("csp_history") or []

    for underlying, legs in list(open_csps.items()):
        if not isinstance(legs, list):
            continue
        uu = str(underlying).upper()
        stock_pos = pos_by_symbol.get(uu)
        stock_qty = 0
        if stock_pos is not None:
            try:
                stock_qty = int(float(getattr(stock_pos, "qty", 0) or (stock_pos.get("qty") if isinstance(stock_pos, dict) else 0)))
            except (TypeError, ValueError):
                stock_qty = 0

        kept: List[Dict[str, Any]] = []
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            occ = str(leg.get("option_symbol") or leg.get("symbol") or "")
            still_short = occ in sym_set
            if still_short:
                kept.append(leg)
                continue
            if stock_qty >= 100 and stock_qty % 100 == 0:
                strike = float(leg.get("strike") or 0)
                lot = {
                    "qty": 100,
                    "cost_basis": strike,
                    "assigned_at": leg.get("opened_at"),
                    "from_csp": leg,
                }
                assigned.setdefault(uu, []).append(lot)
                csp_history.append({**leg, "status": "assigned", "underlying": uu})
                changed = True
                ws._wheel_system_event(
                    "wheel_assignment_detected",
                    symbol=uu,
                    phase="CSP",
                    strike=strike,
                    option_symbol=occ,
                    stock_qty=stock_qty,
                )
            else:
                changed = True
                ws._wheel_system_event(
                    "wheel_csp_leg_cleared",
                    symbol=uu,
                    phase="CSP",
                    option_symbol=occ,
                    reason="option_not_in_positions_insufficient_stock_for_assignment",
                    stock_qty=stock_qty,
                )
        if kept:
            open_csps[uu] = kept
        else:
            del open_csps[uu]
            changed = True

    if changed:
        state["open_csps"] = open_csps
        state["assigned_shares"] = assigned
        state["csp_history"] = csp_history
        ws._save_wheel_state(state, change_type="assignment_reconciled", symbol=None)
    return state


def run_wheel(api, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run one wheel cycle (CSP then CC) after broker reconciliation."""
    from strategies.wheel_strategy import _load_wheel_state, run as wheel_run

    try:
        reconcile_assignments_from_broker(api, _load_wheel_state())
    except Exception as e:
        log.warning("run_wheel: reconcile skipped: %s", e)
    return wheel_run(api, config)
