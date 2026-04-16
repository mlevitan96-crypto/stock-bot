"""Unit tests for RTH-capped unmanaged labels (ALP-ML-001)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.ml.alpaca_unmanaged_labels import compute_unmanaged_rth_labels

_ET = ZoneInfo("America/New_York")


def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _synthetic_session_bars(day_et: datetime) -> list[dict]:
    """One minute bars 9:30–15:59 ET with close increasing by 1 cent per bar."""
    d = day_et.date()
    rth_open = datetime(d.year, d.month, d.day, 9, 30, tzinfo=_ET)
    bars = []
    t = rth_open
    i = 0
    while t <= datetime(d.year, d.month, d.day, 15, 59, tzinfo=_ET):
        bars.append({"t": _utc_iso(t), "o": 100.0, "h": 100.5, "l": 99.5, "c": 100.0 + i * 0.01, "v": 1000})
        t += timedelta(minutes=1)
        i += 1
    return bars


def test_target_60m_capped_before_rth_close():
    # 2026-04-16 14:00 ET = entry; +60m = 15:00 ET still inside RTH
    ent_et = datetime(2026, 4, 16, 14, 0, 0, tzinfo=_ET)
    ent_utc = ent_et.astimezone(timezone.utc)
    bars = _synthetic_session_bars(ent_et)
    out = compute_unmanaged_rth_labels(symbol="TEST", entry_ts_utc=ent_utc, entry_price=100.0, bars=bars)
    assert out["label_60m_reason"] == "ok"
    assert out["label_eod_reason"] == "ok"
    # 60m forward: 15:00 bar close = 100 + (minutes from 9:30 to 15:00) * 0.01
    # 9:30->15:00 = 330 minutes -> close 100 + 330*0.01 = 103.3
    assert abs(out["target_ret_60m_rth"] - math.log(103.3 / 100.0)) < 1e-6


def test_target_60m_caps_at_4pm_et_same_day():
    # Entry 15:10 ET, raw +60m = 16:10 -> capped to 16:00 ET (last bar 15:59)
    ent_et = datetime(2026, 4, 16, 15, 10, 0, tzinfo=_ET)
    ent_utc = ent_et.astimezone(timezone.utc)
    bars = _synthetic_session_bars(ent_et)
    out = compute_unmanaged_rth_labels(symbol="TEST", entry_ts_utc=ent_utc, entry_price=100.0, bars=bars)
    assert out["label_60m_reason"] == "ok"
    last_c = bars[-1]["c"]
    assert abs(out["target_ret_60m_rth"] - math.log(last_c / 100.0)) < 1e-6


def test_after_rth_close_returns_nan():
    ent_et = datetime(2026, 4, 16, 16, 1, 0, tzinfo=_ET)
    ent_utc = ent_et.astimezone(timezone.utc)
    bars = _synthetic_session_bars(ent_et)
    out = compute_unmanaged_rth_labels(symbol="TEST", entry_ts_utc=ent_utc, entry_price=100.0, bars=bars)
    assert out["label_60m_reason"] == "after_rth_close"
