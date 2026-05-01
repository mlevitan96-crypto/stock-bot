"""Tests for congressional regime watchlist (Parquet-backed)."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src.market_intelligence.regime_watchlist import RegimeWatchlist, reset_regime_watchlist_for_tests


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_regime_watchlist_for_tests()
    yield
    reset_regime_watchlist_for_tests()


def test_is_congressional_buy_top_quartile_in_window(tmp_path) -> None:
    today = date.today()
    rows = []
    for i, (sym, amt, txn) in enumerate(
        [
            ("ZZTOP", 5000.0, "Buy"),
            ("ZZTOP", 8000.0, "Buy"),
            ("OTHER", 100_000.0, "Buy"),
            ("OTHER", 200_000.0, "Buy"),
            ("SELLR", 200_000.0, "Sell"),
        ]
    ):
        rows.append(
            {
                "ticker": sym,
                "filing_date": (today - timedelta(days=i)).isoformat(),
                "txn_type": txn,
                "amount_mid_usd": amt,
            }
        )
    p = tmp_path / "m.parquet"
    pd.DataFrame(rows).to_parquet(p, index=False)
    rw = RegimeWatchlist(parquet_path=p, lookback_days=90)
    assert rw.is_congressional_buy("OTHER") is True
    assert rw.is_congressional_buy("ZZTOP") is False
    assert rw.is_congressional_buy("SELLR") is False


def test_regime_watchlist_disabled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("REGIME_WATCHLIST_ENABLED", "0")
    p = tmp_path / "m.parquet"
    pd.DataFrame(
        [{"ticker": "X", "filing_date": date.today().isoformat(), "txn_type": "Buy", "amount_mid_usd": 1e9}]
    ).to_parquet(p, index=False)
    rw = RegimeWatchlist(parquet_path=p)
    assert rw.is_congressional_buy("X") is False
