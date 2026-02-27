"""
Exit Quality Metrics (Phase 4) — Observational only.
====================================================

Computes MFE, MAE, time_in_trade, profit_giveback, post_exit_excursion,
and exit_efficiency flags for closed trades. Does NOT change exit behavior.

Used for: "Was this a bad entry or a good entry exited badly?"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

EPS = 1e-9


def compute_exit_quality_metrics(
    *,
    entry_price: float,
    exit_price: float,
    entry_ts: Optional[datetime] = None,
    exit_ts: Optional[datetime] = None,
    high_water_price: Optional[float] = None,
    qty: float = 1.0,
    side: str = "long",
    bars: Optional[List[Dict[str, Any]]] = None,
    bar_entry_ts: Optional[datetime] = None,
    bar_exit_ts: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Compute exit quality metrics for a closed trade.

    - MFE (max favorable excursion): max profit in price units while in trade.
    - MAE (max adverse excursion): max loss in price units while in trade.
    - time_in_trade_sec: seconds between entry and exit.
    - profit_giveback: (MFE - realized) / max(MFE, eps) when MFE > 0 (long) or symmetric for short.
    - post_exit_excursion: None unless bars after exit_ts are provided (future work).
    - exit_efficiency: { saved_loss: bool, left_money: bool }.

    When bars are not provided, MFE is approximated from high_water_price (long: high_water - entry).
    MAE without bars is set to None unless we can infer from min(0, realized).
    """
    if entry_price <= 0 or exit_price <= 0:
        return _empty_quality()

    is_long = str(side or "long").lower() in ("long", "buy")
    mult = 1 if is_long else -1
    realized_pnl = (exit_price - entry_price) * mult

    # Time in trade
    time_in_trade_sec: Optional[float] = None
    if entry_ts and exit_ts:
        if hasattr(entry_ts, "tzinfo") and entry_ts.tzinfo is None:
            entry_ts = entry_ts.replace(tzinfo=timezone.utc)
        if hasattr(exit_ts, "tzinfo") and exit_ts.tzinfo is None:
            exit_ts = exit_ts.replace(tzinfo=timezone.utc)
        time_in_trade_sec = (exit_ts - entry_ts).total_seconds()

    # MFE / MAE from bars or high_water proxy
    mfe: Optional[float] = None
    mae: Optional[float] = None
    if bars and bar_entry_ts and bar_exit_ts:
        try:
            from data.bars_loader import mfe_mae
            mfe, mae = mfe_mae(bars, bar_entry_ts, bar_exit_ts, float(entry_price), "long" if is_long else "short")
        except Exception:
            pass
    if mfe is None and high_water_price is not None and high_water_price > 0:
        if is_long:
            mfe = max(0.0, high_water_price - entry_price)
        else:
            mfe = max(0.0, entry_price - high_water_price)

    # Profit giveback: (MFE - realized) / max(MFE, eps) when MFE > 0
    profit_giveback: Optional[float] = None
    if mfe is not None and mfe >= EPS:
        realized_in_price = realized_pnl * (1 if is_long else -1)
        giveback = (mfe - realized_in_price) / mfe
        profit_giveback = round(max(0.0, min(1.0, giveback)), 6)

    # Exit efficiency flags (observational)
    saved_loss = realized_pnl > 0 and (mae is None or (is_long and mae > 0) or (not is_long and mae > 0))
    if mae is not None and realized_pnl <= 0:
        saved_loss = False  # We gave back; didn't save loss
    left_money = False
    if mfe is not None and mfe > EPS:
        realized_in_price = (exit_price - entry_price) if is_long else (entry_price - exit_price)
        if realized_in_price < mfe * 0.5:
            left_money = True

    return {
        "mfe": round(mfe, 6) if mfe is not None else None,
        "mae": round(mae, 6) if mae is not None else None,
        "time_in_trade_sec": round(time_in_trade_sec, 2) if time_in_trade_sec is not None else None,
        "profit_giveback": profit_giveback,
        "post_exit_excursion": None,
        "exit_efficiency": {
            "saved_loss": bool(saved_loss),
            "left_money": bool(left_money),
        },
        "realized_pnl_price": round(realized_pnl, 6),
    }


def _empty_quality() -> Dict[str, Any]:
    return {
        "mfe": None,
        "mae": None,
        "time_in_trade_sec": None,
        "profit_giveback": None,
        "post_exit_excursion": None,
        "exit_efficiency": {"saved_loss": False, "left_money": False},
        "realized_pnl_price": None,
    }
