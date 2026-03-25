"""
Canonical trade_key for Alpaca attribution join.
trade_key = "{symbol}|{side}|{entry_epoch_utc}" (UTC, integer Unix seconds, floored).
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
    """UTC ISO to second precision (no subsecond). Display / legacy interchange."""
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
    dt = dt.replace(microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def normalize_entry_ts_to_utc_second(x: Any) -> int:
    """
    Single canonical rule: interpret x as an instant in UTC, floor to whole seconds, return Unix epoch int.

    Accepts:
    - datetime (naive treated as UTC)
    - int/float (epoch seconds; fractional part truncated toward zero after float)
    - ISO8601 str (Z or offset)
    """
    if x is None:
        raise ValueError("entry time is None")
    if isinstance(x, (int, float)):
        return int(float(x))
    if isinstance(x, datetime):
        dt = x
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        dt = dt.replace(microsecond=0)
        return int(dt.timestamp())
    s = str(x).strip()
    if not s:
        raise ValueError("entry time string empty")
    try:
        ts = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError) as e:
        raise ValueError(f"unparseable entry time: {s!r}") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    dt = dt.replace(microsecond=0)
    return int(dt.timestamp())


def build_trade_key(symbol: Any, side: Any, entry_time: Any) -> str:
    """Canonical join key: symbol|side|entry_epoch_utc (UTC second floor, Unix int)."""
    sym = normalize_symbol(symbol)
    sid = normalize_side(side)
    epoch = normalize_entry_ts_to_utc_second(entry_time)
    return f"{sym}|{sid}|{epoch}"
