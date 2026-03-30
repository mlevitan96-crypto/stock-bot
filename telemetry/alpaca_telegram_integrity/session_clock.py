"""US regular-session open (NYSE 09:30 ET), weekday-aware — no holiday calendar."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def _et() -> "ZoneInfo":
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo required")
    return ZoneInfo("America/New_York")


def effective_regular_session_open_utc(now: Optional[datetime] = None) -> datetime:
    """
    Last US weekday regular open at 09:30 America/New_York at or before `now` (in ET sense).

    - Weekend -> Friday 09:30 ET (same week if Sat/Sun).
    - Weekday before 09:30 ET -> previous weekday 09:30 ET.
    """
    now = now or datetime.now(timezone.utc)
    et = now.astimezone(_et())
    d: date = et.date()

    def prev_weekday(dd: date) -> date:
        dd = dd - timedelta(days=1)
        while dd.weekday() >= 5:
            dd = dd - timedelta(days=1)
        return dd

    while d.weekday() >= 5:
        d = prev_weekday(d)

    open_local = datetime(d.year, d.month, d.day, 9, 30, tzinfo=_et())
    if et < open_local:
        d = prev_weekday(d)
        open_local = datetime(d.year, d.month, d.day, 9, 30, tzinfo=_et())

    return open_local.astimezone(timezone.utc)


def session_anchor_date_et_iso(now: Optional[datetime] = None) -> str:
    """Calendar date (ET) of the session used for milestone idempotency."""
    open_utc = effective_regular_session_open_utc(now)
    return open_utc.astimezone(_et()).date().isoformat()
