#!/usr/bin/env python3
"""
Wheel portfolio discipline: sector concentration, dividend/ex-div no-fly, cash-secured (no margin) checks.

Uses existing UW client paths; fail-closed where configured and data is missing.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from src.uw.uw_client import UwCachePolicy, uw_http_get

UW_DIV_CACHE = UwCachePolicy(ttl_seconds=600, key_prefix="wheel_div", endpoint_name="wheel_company_dividends")


def _sector_key_for_cap(symbol: str, sector: str) -> str:
    """Avoid lumping all unknowns into one bucket (would hide concentration)."""
    s = (sector or "Unknown").strip() or "Unknown"
    if s == "Unknown":
        return f"Unknown.{(symbol or '').upper()}"
    return s


def wheel_open_csp_notional_by_sector(
    open_csps: Dict[str, Any],
    get_sector: Callable[[str], str],
) -> Dict[str, float]:
    """Strike * 100 * qty per sector bucket (CSP collateral proxy)."""
    out: Dict[str, float] = {}
    for sym, legs in (open_csps or {}).items():
        if not isinstance(legs, list):
            legs = [legs] if legs else []
        sk = _sector_key_for_cap(str(sym), get_sector(str(sym)))
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            try:
                strike = float(leg.get("strike") or 0)
                qty = int(leg.get("qty") or 1)
            except (TypeError, ValueError):
                continue
            out[sk] = out.get(sk, 0.0) + strike * 100.0 * max(1, qty)
    return out


def sector_cap_allows_new_csp(
    open_csps: Dict[str, Any],
    candidate_symbol: str,
    candidate_notional: float,
    account_equity: float,
    max_sector_fraction: float,
    get_sector: Callable[[str], str],
) -> Tuple[bool, str, Dict[str, float]]:
    """
    True if adding candidate_notional to candidate_symbol's sector keeps sector wheel notional
    at or below max_sector_fraction * account_equity.
    """
    if account_equity <= 0 or max_sector_fraction <= 0:
        return True, "no_equity_or_cap_disabled", {}
    by_sec = wheel_open_csp_notional_by_sector(open_csps, get_sector)
    sk = _sector_key_for_cap(candidate_symbol, get_sector(candidate_symbol))
    projected = by_sec.get(sk, 0.0) + float(candidate_notional)
    cap_usd = float(max_sector_fraction) * float(account_equity)
    if projected > cap_usd + 1e-6:
        return False, f"sector_cap:{sk}:{projected:.0f}>{cap_usd:.0f}", by_sec
    return True, "ok", by_sec


def strict_cash_secured_put_ok(
    *,
    cash: float,
    multiplier: float,
    csp_notional: float,
    allow_margin_account: bool,
    cash_buffer: float = 0.99,
) -> Tuple[bool, str]:
    """
    Require cash collateral ~= full CSP notional when strict mode is on.
    ``allow_margin_account`` bypasses multiplier>1 block (paper only — set via env/config).
    """
    m = float(multiplier or 1.0)
    if m > 1.0 + 1e-9 and not allow_margin_account:
        return False, "margin_multiplier_gt_1"
    need = float(csp_notional) / max(float(cash_buffer), 0.01)
    if float(cash or 0) + 1e-6 < need:
        return False, f"insufficient_cash_need_{need:.0f}_have_{float(cash or 0):.0f}"
    return True, "ok"


def should_skip_dividend_ex_zone(underlying: str, avoid_within_calendar_days: int) -> bool:
    """
    True => skip CSP (ex-dividend too soon). Uses UW /api/companies/{t}/dividends.
    Fail-closed when avoid_within > 0 and UW is blocked or payload unusable.
    """
    days = int(avoid_within_calendar_days or 0)
    if days <= 0:
        return False
    sym = (underlying or "").strip().upper().replace("-", ".")
    if not sym:
        return True
    if str(os.getenv("UW_MOCK", "")).strip().lower() in ("1", "true", "yes", "on") and str(
        os.getenv("UW_MOCK_ENFORCE_LIMITS", "")
    ).strip().lower() not in ("1", "true", "yes", "on"):
        return False
    status, body, _ = uw_http_get(f"/api/companies/{sym}/dividends", cache_policy=UW_DIV_CACHE)
    if status != 200 or not isinstance(body, dict) or body.get("_blocked"):
        return True
    rows = body.get("data")
    if not isinstance(rows, list) or not rows:
        return False
    today = datetime.now(timezone.utc).date()
    horizon = today + timedelta(days=days)
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = row.get("ex_date") or row.get("exDate") or row.get("date")
        if raw is None:
            continue
        try:
            if isinstance(raw, str):
                exd = datetime.strptime(raw[:10], "%Y-%m-%d").date()
            else:
                continue
        except ValueError:
            continue
        if today <= exd <= horizon:
            return True
    return False
