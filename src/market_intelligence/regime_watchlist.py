"""
Shadow regime layer: congressional high-conviction buy watchlist from filing-date matrix Parquet.

``is_congressional_buy`` is True when ``ticker`` appears among **Buy** disclosures in the last
``lookback_days`` (default 90) whose ``amount_mid_usd`` is at or above the **75th percentile**
within that window (top quartile of notional among recent congressional buys in the dataset).
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Set

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PARQUET = REPO_ROOT / "data" / "research" / "congress_filing_forward_matrix.parquet"


class RegimeWatchlist:
    """Loads congressional filing matrix; exposes congressional-buy membership for gating."""

    def __init__(
        self,
        parquet_path: Optional[Path] = None,
        *,
        lookback_days: int = 90,
    ) -> None:
        raw = os.getenv("CONGRESS_REGIME_PARQUET_PATH", "").strip()
        self._path = Path(raw) if raw else (parquet_path or _DEFAULT_PARQUET)
        self._lookback_days = max(1, int(lookback_days))
        self._mtime_ns: int = -1
        self._buy_tickers_top_quartile: Set[str] = set()
        self._loaded: bool = False

    def _reload_if_needed(self) -> None:
        try:
            st = self._path.stat()
            mns = int(getattr(st, "st_mtime_ns", int(float(st.st_mtime) * 1e9)))
        except OSError:
            self._buy_tickers_top_quartile = set()
            self._loaded = True
            self._mtime_ns = -1
            return
        if self._loaded and mns == self._mtime_ns:
            return
        self._mtime_ns = mns
        self._loaded = True
        try:
            df = pd.read_parquet(self._path)
        except Exception:
            self._buy_tickers_top_quartile = set()
            return
        if df is None or df.empty:
            self._buy_tickers_top_quartile = set()
            return
        if "filing_date" not in df.columns or "ticker" not in df.columns:
            self._buy_tickers_top_quartile = set()
            return
        fd = pd.to_datetime(df["filing_date"], errors="coerce").dt.date
        today = datetime.now(timezone.utc).date()
        cutoff = today - timedelta(days=self._lookback_days)
        w = df[fd >= cutoff].copy()
        if w.empty:
            self._buy_tickers_top_quartile = set()
            return
        txn = w.get("txn_type")
        if txn is not None:
            txn_s = txn.astype(str).str.strip().str.lower()
            w = w[txn_s.isin(("buy", "purchase"))].copy()
        if w.empty or "amount_mid_usd" not in w.columns:
            self._buy_tickers_top_quartile = set()
            return
        amt = pd.to_numeric(w["amount_mid_usd"], errors="coerce")
        w = w.assign(_amt=amt).dropna(subset=["_amt"])
        if w.empty:
            self._buy_tickers_top_quartile = set()
            return
        p75 = float(w["_amt"].quantile(0.75))
        top = w[w["_amt"] >= p75]
        syms = top["ticker"].astype(str).str.upper().str.strip()
        self._buy_tickers_top_quartile = {s for s in syms if s}

    def refresh(self) -> None:
        """Force re-read from disk (file replace / ETL refresh)."""
        self._loaded = False
        self._reload_if_needed()

    def is_congressional_buy(self, ticker: str) -> bool:
        if str(os.getenv("REGIME_WATCHLIST_ENABLED", "1")).strip().lower() not in ("1", "true", "yes", "on"):
            return False
        sym = str(ticker or "").upper().strip()
        if not sym:
            return False
        self._reload_if_needed()
        return sym in self._buy_tickers_top_quartile


_watchlist_singleton: Optional[RegimeWatchlist] = None


def get_regime_watchlist() -> RegimeWatchlist:
    global _watchlist_singleton
    if _watchlist_singleton is None:
        lb = int(os.getenv("CONGRESS_REGIME_LOOKBACK_DAYS", "90") or "90")
        path = os.getenv("CONGRESS_REGIME_PARQUET_PATH", "").strip()
        p = Path(path) if path else None
        _watchlist_singleton = RegimeWatchlist(parquet_path=p, lookback_days=lb)
    return _watchlist_singleton


def reset_regime_watchlist_for_tests() -> None:
    global _watchlist_singleton
    _watchlist_singleton = None
