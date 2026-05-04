#!/usr/bin/env python3
"""
Wheel HUD JSON sink for the Flask dashboard (low-latency read of ``state/wheel_dashboard_sink.json``).

Built by ``scripts/wheel_broker_reconcile.py`` (15m) and optionally refreshed after wheel runs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.registry import StateFiles, atomic_write_json, read_json


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _dte_from_expiry(expiry: Optional[str]) -> Optional[int]:
    if not expiry or not isinstance(expiry, str) or len(expiry) < 10:
        return None
    try:
        exp = datetime.strptime(expiry[:10], "%Y-%m-%d").date()
        return max(0, (exp - datetime.now(timezone.utc).date()).days)
    except ValueError:
        return None


def _days_held(opened_at: Optional[str]) -> Optional[int]:
    dt = _parse_iso(opened_at)
    if dt is None:
        return None
    delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    return max(0, int(delta.total_seconds() // 86400))


def _estimate_put_delta_fast(strike: float, spot: float) -> float:
    if spot <= 0:
        return -0.25
    m = strike / spot
    if m >= 1.0:
        return -0.5
    if m >= 0.98:
        return -0.35
    if m >= 0.95:
        return -0.25
    return -0.15


def _estimate_call_delta_fast(strike: float, spot: float) -> float:
    if spot <= 0:
        return 0.25
    m = strike / spot
    if m <= 1.0:
        return 0.5
    if m <= 1.02:
        return 0.35
    if m <= 1.05:
        return 0.25
    return 0.15


def compute_portfolio_wheel_hud_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Proxy Greeks and premium velocity for HUD (not exchange Greeks).

    Theta proxy: OTM decay heuristic from open credit / DTE. Delta: BSM-ish fast estimates × spot × 100.
    """
    theta_proxy = 0.0
    delta_notional = 0.0
    prem_per_day = 0.0
    for r in rows:
        spot = float(r.get("spot") or 0)
        strike = float(r.get("strike") or 0)
        dte = max(int(r.get("dte") or 1), 1)
        dh = max(int(r.get("days_held") or 0), 0)
        st = r.get("stage")
        cred = float(r.get("open_leg_credit_usd") or 0)
        if st == "CSP" and spot > 0:
            dlt = _estimate_put_delta_fast(strike, spot)
            delta_notional += dlt * spot * 100.0
            if cred > 0:
                theta_proxy += cred * 0.15 / float(dte)
                prem_per_day += cred / float(max(dh, 1))
        elif st == "CC" and spot > 0:
            dlt = _estimate_call_delta_fast(strike, spot)
            delta_notional += dlt * spot * 100.0
    return {
        "portfolio_theta_proxy_per_day_usd": round(theta_proxy, 2),
        "portfolio_delta_notional_usd": round(delta_notional, 2),
        "premium_per_day_usd": round(prem_per_day, 2),
    }


def _realized_premium_for_symbol(state: Dict[str, Any], underlying: str) -> float:
    total = 0.0
    u = underlying.upper()
    wpb = state.get("wheel_premium_by_ticker") or {}
    if isinstance(wpb, dict) and u in wpb:
        try:
            return round(float(wpb[u]), 2)
        except (TypeError, ValueError):
            pass
    for row in state.get("csp_history") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("underlying_symbol") or row.get("underlying") or "").upper() != u:
            continue
        for k in ("open_credit", "premium", "credit_realized_est"):
            v = row.get(k)
            if v is not None:
                try:
                    total += float(v)
                except (TypeError, ValueError):
                    pass
    for row in state.get("cc_history") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("underlying_symbol") or row.get("symbol") or "").upper() != u:
            continue
        v = row.get("premium")
        if v is not None:
            try:
                total += float(v)
            except (TypeError, ValueError):
                pass
    return round(total, 2)


def build_wheel_hud_rows(
    state: Dict[str, Any],
    spot_by_underlying: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Flatten open_csps + assigned (CC-eligible stock) into dashboard rows."""
    spots = spot_by_underlying or {}
    rows: List[Dict[str, Any]] = []
    open_csps = state.get("open_csps") or {}
    for und, legs in open_csps.items():
        if not isinstance(legs, list):
            legs = [legs] if legs else []
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            u = str(und).upper()
            strike = float(leg.get("strike") or 0)
            spot = float(spots.get(u) or leg.get("spot_at_open") or 0)
            exp = leg.get("expiry") or leg.get("expiration_date")
            oc = leg.get("open_credit")
            try:
                oc_f = float(oc) if oc is not None else 0.0
            except (TypeError, ValueError):
                oc_f = 0.0
            rows.append(
                {
                    "ticker": u,
                    "stage": "CSP",
                    "strike": strike,
                    "spot": round(spot, 4) if spot else None,
                    "strike_vs_spot": round(strike - spot, 4) if spot else None,
                    "dte": _dte_from_expiry(str(exp) if exp else None),
                    "days_held": _days_held(leg.get("opened_at")),
                    "realized_premium_usd": _realized_premium_for_symbol(state, u),
                    "open_leg_credit_usd": round(oc_f, 2) if oc_f else None,
                    "adjusted_cost_basis": strike,
                    "option_symbol": leg.get("option_symbol") or leg.get("symbol"),
                    "opened_at": leg.get("opened_at"),
                }
            )
    assigned = state.get("assigned_shares") or {}
    for und, lots in assigned.items():
        if not isinstance(lots, list):
            lots = [lots] if lots else []
        u = str(und).upper()
        spot = float(spots.get(u) or 0)
        for lot in lots:
            if not isinstance(lot, dict):
                continue
            cb = float(lot.get("cost_basis") or 0)
            qty = int(lot.get("qty") or 0)
            rows.append(
                {
                    "ticker": u,
                    "stage": "CC_STOCK",
                    "strike": cb,
                    "spot": round(spot, 4) if spot else None,
                    "strike_vs_spot": round(cb - spot, 4) if spot else None,
                    "dte": None,
                    "days_held": _days_held(lot.get("assigned_at")),
                    "realized_premium_usd": _realized_premium_for_symbol(state, u),
                    "adjusted_cost_basis": cb,
                    "option_symbol": None,
                    "qty_shares": qty,
                }
            )
    open_ccs = state.get("open_ccs") or {}
    for und, legs in open_ccs.items():
        if not isinstance(legs, list):
            legs = [legs] if legs else []
        u = str(und).upper()
        spot = float(spots.get(u) or 0)
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            strike = float(leg.get("strike") or 0)
            exp_cc = leg.get("expiry") or leg.get("expiration_date")
            rows.append(
                {
                    "ticker": u,
                    "stage": "CC",
                    "strike": strike,
                    "spot": round(spot, 4) if spot else None,
                    "strike_vs_spot": round(strike - spot, 4) if spot else None,
                    "dte": _dte_from_expiry(str(exp_cc) if exp_cc else None),
                    "days_held": _days_held(leg.get("opened_at")),
                    "realized_premium_usd": _realized_premium_for_symbol(state, u),
                    "adjusted_cost_basis": strike,
                    "option_symbol": leg.get("symbol"),
                }
            )
    return rows


def write_wheel_dashboard_sink(
    payload: Dict[str, Any],
    path: Optional[Path] = None,
) -> None:
    p = path or getattr(StateFiles, "WHEEL_DASHBOARD_SINK", Path("state") / "wheel_dashboard_sink.json")
    atomic_write_json(p, payload)


def minimal_sink_from_files(
    *,
    drift_alerts: Optional[List[Dict[str, Any]]] = None,
    spot_by_underlying: Optional[Dict[str, float]] = None,
    nav_usd: Optional[float] = None,
    cash: Optional[float] = None,
    multiplier: Optional[float] = None,
) -> Dict[str, Any]:
    state = read_json(StateFiles.WHEEL_STATE, default={}) or {}
    epoch = read_json(StateFiles.EPOCH_STATE, default={}) or {}
    rows = build_wheel_hud_rows(state, spot_by_underlying=spot_by_underlying)
    greeks = compute_portfolio_wheel_hud_metrics(rows)
    return {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "epoch_label": epoch.get("epoch_label"),
        "epoch_start_ts": epoch.get("epoch_start_ts"),
        "wheel_realized_alpha_usd": epoch.get("wheel_realized_alpha_usd"),
        "nav_usd": nav_usd,
        "cash": cash,
        "account_multiplier": multiplier,
        "rows": rows,
        "drift_alerts": drift_alerts or [],
        "schema_version": 2,
        **greeks,
    }
