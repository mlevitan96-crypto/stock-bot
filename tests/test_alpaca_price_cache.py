"""Unit tests for SIP bar ring buffer (no live WebSocket)."""
from __future__ import annotations

import time

import pytest

from src.alpaca.stream_manager import PriceCache


def test_price_cache_ring_and_freshness():
    c = PriceCache(maxlen_per_symbol=5)
    base = "2026-04-07T15:00:00Z"
    for i in range(6):
        c.record_minute_bar(
            "TEST",
            o=100 + i,
            h=101 + i,
            l=99 + i,
            c=100.5 + i,
            v=1000,
            vw=100.2 + i,
            n=10,
            t_iso=f"2026-04-07T15:{i:02d}:00Z",
        )
    df = c.get_fresh_bars_df("TEST", 3, max_age_sec=300.0)
    assert df is not None
    assert len(df) == 3
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_price_cache_stale_when_no_recent_rx():
    c = PriceCache(maxlen_per_symbol=10)
    c.record_minute_bar(
        "ZZ",
        o=1,
        h=1,
        l=1,
        c=1,
        v=1,
        vw=1,
        n=1,
        t_iso="2026-04-07T16:00:00Z",
    )
    # Simulate age by clearing last_rx — use private structure via new cache + manual hack
    with c._lock:
        c._last_bar_rx_mono["ZZ"] = time.monotonic() - 999.0
    assert c.get_fresh_bars_df("ZZ", 1, max_age_sec=60.0) is None
