"""
NYSE regular-session (cash) window in America/New_York → UTC epochs for strict cohorts.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Dict, Tuple, Union

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _ET = None


def market_session_bounds_utc(
    session_date: Union[date, str],
) -> Dict[str, Any]:
    """
    Regular session 09:30–16:00 America/New_York on session_date.

    Returns ISO strings and UTC epoch floats for [window_start, window_end] inclusive end.
    """
    if _ET is None:
        raise RuntimeError("zoneinfo America/New_York unavailable")
    if isinstance(session_date, str):
        y, m, d = session_date.strip().split("-", 2)
        session_date = date(int(y), int(m), int(d))
    open_et = datetime.combine(session_date, time(9, 30), tzinfo=_ET)
    close_et = datetime.combine(session_date, time(16, 0), tzinfo=_ET)
    open_utc = open_et.astimezone(timezone.utc)
    close_utc = close_et.astimezone(timezone.utc)
    start_epoch = open_utc.timestamp()
    end_epoch = close_utc.timestamp()
    return {
        "session_date_et": session_date.isoformat(),
        "session_open_et": open_et.isoformat(),
        "session_close_et": close_et.isoformat(),
        "window_start_utc": open_utc.isoformat().replace("+00:00", "Z"),
        "window_end_utc": close_utc.isoformat().replace("+00:00", "Z"),
        "window_start_epoch_utc": start_epoch,
        "window_end_epoch_utc": end_epoch,
    }


def market_session_epoch_tuple(session_date: Union[date, str]) -> Tuple[float, float]:
    b = market_session_bounds_utc(session_date)
    return float(b["window_start_epoch_utc"]), float(b["window_end_epoch_utc"])
