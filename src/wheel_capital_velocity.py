#!/usr/bin/env python3
"""
Capital velocity: premium capture quick-exit, gamma shield, roll-vs-assignment advisory.

Logs ``wheel_quick_exit``, ``wheel_gamma_shield_exit``, ``wheel_roll_evaluation`` to system_events.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


def _hours_to_option_expiry(expiry_str: Optional[str]) -> Optional[float]:
    if not expiry_str or len(str(expiry_str)) < 10:
        return None
    try:
        exp_date = datetime.strptime(str(expiry_str)[:10], "%Y-%m-%d").date()
        # Approximate equity option expiry: 21:00 UTC on expiry Friday (simplified).
        exp_dt = datetime(exp_date.year, exp_date.month, exp_date.day, 21, 0, 0, tzinfo=timezone.utc)
        return (exp_dt - datetime.now(timezone.utc)).total_seconds() / 3600.0
    except ValueError:
        return None


def _option_buy_limit_per_share(api, occ_symbol: str) -> Optional[float]:
    """Conservative limit to buy-to-close (short leg): prefer ask, then last."""
    if not occ_symbol or not api:
        return None
    try:
        from strategies.wheel_strategy import fetch_alpaca_latest_quote, normalize_alpaca_quote

        raw = fetch_alpaca_latest_quote(api, occ_symbol)
        n = normalize_alpaca_quote(raw) or {}
        ask = n.get("ask")
        lt = n.get("last_trade")
        for v in (ask, lt):
            if v is not None:
                try:
                    x = float(v)
                    if x > 0:
                        return round(x * 1.02, 2)
                except (TypeError, ValueError):
                    continue
    except Exception as e:
        log.warning("Wheel velocity: pricing failed for %s: %s", occ_symbol, e)
    return None


def _csp_premium_capture_ratio(open_credit: float, buy_limit_per_share: float) -> Optional[float]:
    """Fraction of entry credit kept as profit when buying to close at limit (per-share prices)."""
    if open_credit <= 0 or buy_limit_per_share is None or buy_limit_per_share < 0:
        return None
    cost_to_close = buy_limit_per_share * 100.0
    captured = open_credit - cost_to_close
    return captured / open_credit if open_credit > 1e-6 else None


def evaluate_roll_vs_assignment(
    *,
    underlying: str,
    strike: float,
    spot: float,
    dte: Optional[int],
    expiry: Optional[str],
) -> Dict[str, Any]:
    """
    Advisory only: CSP ITM near expiry → prefer human/system review for roll vs assignment.

    Full roll execution (debit/credit calendar) requires chain pricing; not auto-submitted here.
    """
    put_itm = spot > 0 and strike > 0 and spot < strike - 1e-6
    near = dte is not None and int(dte) <= 5
    if not (put_itm and near):
        return {"recommendation": "hold", "reason": "not_itm_or_not_near_expiry", "underlying": underlying.upper()}
    hrs = _hours_to_option_expiry(expiry)
    return {
        "recommendation": "review_roll_or_assignment",
        "reason": "csp_itm_near_expiry",
        "underlying": underlying.upper(),
        "strike": strike,
        "spot": round(spot, 4),
        "dte": dte,
        "hours_to_exp_approx": round(hrs, 2) if hrs is not None else None,
        "note": "Evaluate roll for net credit vs taking assignment; no auto-roll order.",
    }


def apply_wheel_capital_velocity(
    api,
    state: Dict[str, Any],
    velocity_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Buy-to-close CSP legs when premium capture >= quick_exit threshold, or gamma shield triggers.

    Mutates ``state`` (``open_csps``, ``csp_history``) and persists via ``_save_wheel_state``.
    """
    import strategies.wheel_strategy as ws

    if not velocity_cfg or not bool(velocity_cfg.get("enabled", True)):
        return {"closed": 0, "skipped": "velocity_disabled"}

    q_pct = float(velocity_cfg.get("quick_exit_premium_capture", 0.90) or 0.90)
    gamma_h = float(velocity_cfg.get("gamma_shield_hours_to_expiry", 48) or 48)
    gamma_p = float(velocity_cfg.get("gamma_shield_min_profit_capture", 0.80) or 0.80)

    open_csps = state.get("open_csps") or {}
    changed = False
    closed = 0
    alpha_delta = 0.0
    csp_history = list(state.get("csp_history") or [])

    for und, legs in list(open_csps.items()):
        if not isinstance(legs, list):
            continue
        uu = str(und).upper()
        kept: List[Dict[str, Any]] = []
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            occ = str(leg.get("option_symbol") or leg.get("symbol") or "")
            credit = float(leg.get("open_credit") or 0)
            exp = leg.get("expiry") or leg.get("expiration_date")
            dte = None
            if exp and len(str(exp)) >= 10:
                try:
                    exp_d = datetime.strptime(str(exp)[:10], "%Y-%m-%d").date()
                    dte = max(0, (exp_d - datetime.now(timezone.utc).date()).days)
                except ValueError:
                    pass
            strike = float(leg.get("strike") or 0)

            buy_px = _option_buy_limit_per_share(api, occ)
            cap_ratio = _csp_premium_capture_ratio(credit, buy_px) if buy_px is not None else None
            hrs = _hours_to_option_expiry(str(exp) if exp else None)

            if dte is not None and int(dte) <= 5:
                try:
                    spot_roll, _ = ws._resolve_spot(api, uu)
                except Exception:
                    spot_roll = 0.0
                roll_hint = evaluate_roll_vs_assignment(
                    underlying=uu, strike=strike, spot=float(spot_roll or 0), dte=dte, expiry=str(exp) if exp else None
                )
                if roll_hint.get("recommendation") != "hold":
                    ws._wheel_system_event("wheel_roll_evaluation", **roll_hint)

            do_close = False
            reason = ""
            if credit > 0 and cap_ratio is not None:
                if cap_ratio >= q_pct:
                    do_close = True
                    reason = "quick_exit_90pct"
                elif hrs is not None and hrs <= gamma_h and hrs >= 0 and cap_ratio >= gamma_p:
                    do_close = True
                    reason = "gamma_shield_48h"

            if not do_close or not occ:
                kept.append(leg)
                continue

            try:
                limit_px = buy_px if buy_px is not None else 0.01
                order = api.submit_order(
                    symbol=occ,
                    qty=1,
                    side="buy",
                    type="limit",
                    time_in_force="day",
                    limit_price=float(limit_px),
                )
                oid = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else None)
            except Exception as e:
                log.warning("wheel velocity close failed %s: %s", occ, e)
                ws._wheel_system_event(
                    "wheel_velocity_close_failed",
                    symbol=uu,
                    option_symbol=occ,
                    reason=str(e)[:200],
                )
                kept.append(leg)
                continue

            est_capture = credit - (float(limit_px) * 100.0) if credit > 0 else 0.0
            alpha_delta += max(0.0, est_capture)
            csp_history.append(
                {
                    **leg,
                    "status": "closed_" + reason,
                    "closed_at": datetime.now(timezone.utc).isoformat(),
                    "close_order_id": str(oid) if oid else None,
                    "close_limit": float(limit_px),
                    "premium_capture_ratio_est": round(cap_ratio, 4) if cap_ratio is not None else None,
                }
            )
            evt = "wheel_quick_exit" if reason.startswith("quick") else "wheel_gamma_shield_exit"
            ws._wheel_system_event(
                evt,
                symbol=uu,
                phase="CSP",
                option_symbol=occ,
                reason=reason,
                open_credit=round(credit, 2),
                limit_price=float(limit_px),
                order_id=str(oid) if oid else None,
                dte=dte,
                hours_to_expiry=round(hrs, 2) if hrs is not None else None,
            )
            changed = True
            closed += 1

        if kept:
            open_csps[uu] = kept
        else:
            del open_csps[uu]
            changed = True

    if changed:
        state["open_csps"] = open_csps
        state["csp_history"] = csp_history
        ws._save_wheel_state(state, change_type="velocity_exit", symbol=None)
    if alpha_delta > 0:
        try:
            from src.telemetry.epoch_manager import bump_wheel_realized_alpha

            bump_wheel_realized_alpha(alpha_delta)
        except Exception as e:
            log.debug("epoch alpha bump skipped: %s", e)

    return {"closed": closed, "alpha_usd_est": round(alpha_delta, 2)}
