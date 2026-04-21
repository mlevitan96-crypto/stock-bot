"""
Tick-aware quantization for Alpaca equity telemetry (logging / attribution), not order limits.

Sub-$5 names use 4 decimal places on prices (Alpaca 2026-style minimum increment context).
$5+ names keep finer price decimals and matching PnL precision so bps-level moves are not
zeroed by blanket ``round(..., 4)``.
"""

from __future__ import annotations

PENNY_PRICE_THRESHOLD_USD = 5.0


def _finite(x: float) -> bool:
    return x == x and abs(x) < 1e308


def quantize_telemetry_price(price: float | int | None) -> float | None:
    if price is None:
        return None
    try:
        x = float(price)
    except (TypeError, ValueError):
        return None
    if not _finite(x):
        return x
    ax = abs(x)
    if ax < PENNY_PRICE_THRESHOLD_USD:
        return round(x, 4)
    return round(x, 6)


def quantize_telemetry_pnl_pct(pnl_pct: float | int | None, *, ref_price: float | int | None) -> float | None:
    if pnl_pct is None:
        return None
    try:
        p = float(pnl_pct)
    except (TypeError, ValueError):
        return None
    if not _finite(p):
        return p
    tier_px = PENNY_PRICE_THRESHOLD_USD
    try:
        if ref_price is not None:
            rp = float(ref_price)
            if _finite(rp) and rp > 0:
                tier_px = abs(rp)
    except (TypeError, ValueError):
        pass
    if tier_px < PENNY_PRICE_THRESHOLD_USD:
        return round(p, 4)
    return round(p, 6)


def quantize_telemetry_pnl_usd(pnl_usd: float | int | None, *, ref_price: float | int | None) -> float | None:
    if pnl_usd is None:
        return None
    try:
        u = float(pnl_usd)
    except (TypeError, ValueError):
        return None
    if not _finite(u):
        return u
    tier_px = PENNY_PRICE_THRESHOLD_USD
    try:
        if ref_price is not None:
            rp = float(ref_price)
            if _finite(rp) and rp > 0:
                tier_px = abs(rp)
    except (TypeError, ValueError):
        pass
    if tier_px < PENNY_PRICE_THRESHOLD_USD:
        return round(u, 4)
    return round(u, 2)
