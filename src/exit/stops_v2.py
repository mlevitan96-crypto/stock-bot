#!/usr/bin/env python3
"""
Dynamic Stops (v2, shadow-only)
==============================

Best-effort stop calculator. If prices/vol inputs are missing, returns None stop.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def compute_stop_price(
    *,
    entry_price: Optional[float],
    realized_vol_20d: Optional[float],
    flow_reversal: bool,
    regime_label: str,
    sector_collapse: bool,
    direction: str,
) -> Tuple[Optional[float], Dict[str, Any]]:
    if entry_price is None or entry_price <= 0:
        return None, {"reason": "missing_entry_price"}

    vol = float(realized_vol_20d or 0.0)
    # Base stop percent: 1.5%–4% based on vol
    base_pct = 0.015 + max(0.0, min(0.025, (vol - 0.20) * 0.06))

    # Tighten on flow reversal / regime risk-off / sector collapse
    tighten = 1.0
    if flow_reversal:
        tighten *= 0.75
    if sector_collapse:
        tighten *= 0.80
    r = str(regime_label or "NEUTRAL").upper()
    if r in ("RISK_OFF", "BEAR"):
        tighten *= 0.80

    pct = base_pct * tighten
    pct = max(0.005, min(0.08, pct))

    d = str(direction or "").lower()
    if d == "bullish":
        stop = float(entry_price) * (1.0 - pct)
    elif d == "bearish":
        stop = float(entry_price) * (1.0 + pct)
    else:
        return None, {"reason": "neutral_direction"}

    return float(stop), {
        "base_pct": round(base_pct, 4),
        "pct": round(pct, 4),
        "tighten_mult": round(tighten, 4),
        "flow_reversal": bool(flow_reversal),
        "sector_collapse": bool(sector_collapse),
        "regime_label": r,
    }

