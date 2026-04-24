"""
Compute MFE, MAE, time-to-peak, time-to-trough from bar series for a trade window.
Bars: list of dicts with t (timestamp), o, h, l, c, v.
Entry/exit as datetime; side "long" or "short"; entry_price float.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _parse_bar_time(t: Any) -> Optional[datetime]:
    if t is None:
        return None
    try:
        s = str(t).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _bars_in_window(
    bars: List[Dict[str, Any]],
    entry_time: datetime,
    exit_time: datetime,
) -> List[Dict[str, Any]]:
    entry_utc = entry_time.replace(tzinfo=entry_time.tzinfo or timezone.utc)
    exit_utc = exit_time.replace(tzinfo=exit_time.tzinfo or timezone.utc)
    out = []
    for b in bars:
        bt = _parse_bar_time(b.get("t"))
        if bt is None:
            continue
        if entry_utc <= bt <= exit_utc:
            out.append(b)
    return sorted(out, key=lambda x: _parse_bar_time(x.get("t")) or entry_utc)


def compute_mfe_mae(
    bars: List[Dict[str, Any]],
    entry_time: datetime,
    exit_time: datetime,
    entry_price: float,
    side: str,
) -> Dict[str, Any]:
    """
    Returns dict with mfe_pct, mae_pct, time_to_peak_min, time_to_trough_min.
    Side: "long" or "short" (case-insensitive).
    """
    entry_utc = entry_time.replace(tzinfo=entry_time.tzinfo or timezone.utc)
    exit_utc = exit_time.replace(tzinfo=exit_time.tzinfo or timezone.utc)
    in_window = _bars_in_window(bars, entry_utc, exit_utc)
    if not in_window or entry_price <= 0:
        return {
            "mfe_pct": None,
            "mae_pct": None,
            "time_to_peak_min": None,
            "time_to_trough_min": None,
        }
    is_long = str(side).strip().lower() in ("long", "buy")
    mfe_pct = None
    mae_pct = None
    time_to_peak_min = None
    time_to_trough_min = None
    peak_bar_ts = None
    trough_bar_ts = None
    if is_long:
        best_favorable = entry_price
        worst_adverse = entry_price
        for b in in_window:
            h, l_ = float(b.get("h", 0)), float(b.get("l", 0))
            bt = _parse_bar_time(b.get("t"))
            if h > best_favorable:
                best_favorable = h
                peak_bar_ts = bt
            if l_ < worst_adverse:
                worst_adverse = l_
                trough_bar_ts = bt
        mfe_pct = (best_favorable - entry_price) / entry_price * 100
        mae_pct = (worst_adverse - entry_price) / entry_price * 100
    else:
        best_favorable = entry_price
        worst_adverse = entry_price
        for b in in_window:
            h, l_ = float(b.get("h", 0)), float(b.get("l", 0))
            bt = _parse_bar_time(b.get("t"))
            if l_ < best_favorable:
                best_favorable = l_
                peak_bar_ts = bt
            if h > worst_adverse:
                worst_adverse = h
                trough_bar_ts = bt
        mfe_pct = (entry_price - best_favorable) / entry_price * 100
        mae_pct = (entry_price - worst_adverse) / entry_price * 100
    if peak_bar_ts:
        delta = (peak_bar_ts - entry_utc).total_seconds() / 60
        time_to_peak_min = round(delta, 2)
    if trough_bar_ts:
        delta = (trough_bar_ts - entry_utc).total_seconds() / 60
        time_to_trough_min = round(delta, 2)
    return {
        "mfe_pct": round(mfe_pct, 4) if mfe_pct is not None else None,
        "mae_pct": round(mae_pct, 4) if mae_pct is not None else None,
        "time_to_peak_min": time_to_peak_min,
        "time_to_trough_min": time_to_trough_min,
    }
