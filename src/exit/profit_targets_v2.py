#!/usr/bin/env python3
"""
Dynamic Profit Targets (v2)
==========================

Best-effort target calculator. If prices/vol inputs are missing, returns None target.

Contract:
- Read-only helper: target is advisory; executor decides actual orders.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def compute_profit_target(
    *,
    entry_price: Optional[float],
    realized_vol_20d: Optional[float],
    flow_strength: float,
    regime_label: str,
    sector: str,
    direction: str,
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Returns (profit_target_price, reasoning)
    """
    if entry_price is None or entry_price <= 0:
        return None, {"reason": "missing_entry_price"}

    vol = float(realized_vol_20d or 0.0)
    # Base target percent: 2%–6% based on realized vol (very conservative)
    base_pct = 0.02 + max(0.0, min(0.04, (vol - 0.20) * 0.10))

    # Flow adjustment: stronger flow => wider target
    flow_mult = 1.0 + max(0.0, min(0.50, float(flow_strength) * 0.50))

    # Regime adjustment
    r = str(regime_label or "NEUTRAL").upper()
    if r == "RISK_ON":
        reg_mult = 1.15
    elif r in ("RISK_OFF", "BEAR"):
        reg_mult = 0.85
    else:
        reg_mult = 1.0

    # Sector adjustment (small)
    s = str(sector or "UNKNOWN").upper()
    sec_mult = 1.05 if s in ("TECH", "BIOTECH") else 1.0

    pct = base_pct * flow_mult * reg_mult * sec_mult
    pct = max(0.01, min(0.10, pct))

    d = str(direction or "").lower()
    if d == "bullish":
        target = float(entry_price) * (1.0 + pct)
    elif d == "bearish":
        target = float(entry_price) * (1.0 - pct)
    else:
        return None, {"reason": "neutral_direction"}

    return float(target), {
        "base_pct": round(base_pct, 4),
        "pct": round(pct, 4),
        "flow_mult": round(flow_mult, 4),
        "regime_mult": round(reg_mult, 4),
        "sector_mult": round(sec_mult, 4),
        "regime_label": r,
        "sector": s,
    }

