"""
Canonical trade_key for Alpaca attribution join.
trade_key = "{symbol}|{side}|{entry_time_iso}" (UTC, second precision).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def normalize_symbol(symbol: Any) -> str:
    """Normalize ticker: upper, strip. Empty -> '?'."""
    if symbol is None:
        return "?"
    s = str(symbol).strip().upper()
    return s if s else "?"


def normalize_side(side: Any) -> str:
    """LONG or SHORT. buy/long -> LONG; sell/short -> SHORT. Default LONG."""
    if side is None:
        return "LONG"
    s = str(side).strip().upper()
    if s in ("BUY", "LONG"):
        return "LONG"
    if s in ("SELL", "SHORT"):
        return "SHORT"
    return "LONG"


def normalize_time(entry_time: Any) -> str:
    """UTC ISO to second precision (no subsecond)."""
    if entry_time is None:
        return ""
    if isinstance(entry_time, datetime):
        dt = entry_time
    else:
        try:
            ts = str(entry_time).strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
        except (TypeError, ValueError):
            return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    # Second precision: strip microseconds
    dt = dt.replace(microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def build_trade_key(symbol: Any, side: Any, entry_time: Any) -> str:
    """Canonical join key: symbol|side|entry_time_iso (UTC, second precision)."""
    sym = normalize_symbol(symbol)
    sid = normalize_side(side)
    ts = normalize_time(entry_time)
    return f"{sym}|{sid}|{ts}"
