#!/usr/bin/env python3
"""
Options wheel — UW + Alpaca decision helpers (institutional put wall, IV rank, earnings, SP100, dust floor).

UW traffic uses ``src.uw.uw_client.uw_http_get`` (allow-listed endpoints, cache, quota).
Fail-closed semantics when UW returns blocked/empty data for gates that require fresh intelligence.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.uw.oi_change_aggregate import _side_from_option_symbol
from src.uw.uw_client import UwCachePolicy, uw_http_get

def _norm_sp100(sym: str) -> str:
    """Alpaca-style hyphen vs dot tickers (BRK.B / BRK-B) normalized to hyphen."""
    return (sym or "").strip().upper().replace(".", "-")


# S&P 100 constituents (101 tickers: dual-class Alphabet). Source: Wikipedia "S&P 100" components as of 2025-09-22.
# Rebalance: update this set when S&P Dow Jones changes the index.
SP100_CONSTITUENTS: frozenset[str] = frozenset(
    _norm_sp100(x)
    for x in """
    AAPL ABBV ABT ACN ADBE AMAT AMD AMGN AMT AMZN AVGO AXP BA BAC BK BKNG BLK BMY BRK-B C CAT CL CMCSA COF COP
    COST CRM CSCO CVS CVX DE DHR DIS DUK EMR FDX GD GE GEV GILD GM GOOG GOOGL GS HD HON IBM INTC INTU ISRG JNJ
    JPM KO LIN LLY LMT LOW LRCX MA MCD MDLZ MDT META MMM MO MRK MS MSFT MU NEE NFLX NKE NOW NVDA ORCL PEP PFE PG
    PLTR PM QCOM RTX SBUX SCHW SO SPG T TMO TMUS TSLA TXN UBER UNH UNP UPS USB V VZ WFC WMT XOM
    """.split()
)

DEFAULT_MIN_IV_RANK = 50.0
DEFAULT_PUT_WALL_MIN_OI = int(os.getenv("WHEEL_PUT_WALL_MIN_OI", "5000") or "5000")
DEFAULT_DUST_MIN_CREDIT_USD = float(os.getenv("WHEEL_MIN_CREDIT_USD", "200") or "200")
UW_WHEEL_CACHE_OI = UwCachePolicy(ttl_seconds=120, key_prefix="wheel_oi", endpoint_name="wheel_oi_change")
UW_WHEEL_CACHE_IV = UwCachePolicy(ttl_seconds=300, key_prefix="wheel_iv", endpoint_name="wheel_iv_rank")
UW_WHEEL_CACHE_EARN = UwCachePolicy(ttl_seconds=600, key_prefix="wheel_er", endpoint_name="wheel_earnings")
UW_WHEEL_CACHE_VOL = UwCachePolicy(ttl_seconds=300, key_prefix="wheel_vol", endpoint_name="wheel_volatility_realized")


def _uw_mock_soft() -> bool:
    return str(os.getenv("UW_MOCK", "")).strip().lower() in ("1", "true", "yes", "on") and str(
        os.getenv("UW_MOCK_ENFORCE_LIMITS", "")
    ).strip().lower() not in ("1", "true", "yes", "on")


_OCC_STRIKE = re.compile(r"[CP](\d{8})$", re.IGNORECASE)


def normalize_equity_symbol(sym: str) -> str:
    """UW / Alpaca common normalization for equity roots."""
    return _norm_sp100(sym) if sym else ""


def uw_ticker_for_rest(sym: str) -> str:
    """UW REST paths historically use dotted class tickers (e.g. BRK.B)."""
    return (sym or "").strip().upper().replace("-", ".")


def is_sp100_wheel_eligible(underlying: str) -> bool:
    """Hard asset gate: underlying must be an S&P 100 constituent (no env bypass)."""
    return _norm_sp100(underlying) in SP100_CONSTITUENTS


def occ_strike_price(option_symbol: str) -> Optional[float]:
    """OCC 8-digit strike suffix (price * 1000) -> float strike."""
    if not option_symbol:
        return None
    m = _OCC_STRIKE.search(option_symbol.strip().upper())
    if not m:
        return None
    try:
        return int(m.group(1)) / 1000.0
    except (TypeError, ValueError):
        return None


def _scalar_iv_rank(body: Dict[str, Any]) -> Optional[float]:
    data = body.get("data")
    if isinstance(data, dict):
        for k in ("iv_rank", "iv_rank_1y", "rank", "ivRank"):
            v = data.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
    if isinstance(data, list) and data:
        row = data[0]
        if isinstance(row, dict):
            for k in ("iv_rank", "iv_rank_1y", "rank"):
                v = row.get(k)
                if v is not None:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
    return None


def fetch_iv_rank(underlying: str) -> Tuple[Optional[float], str]:
    """
    Returns (iv_rank_0_to_100_or_none, reason).
    None + reason on failure, blocked, or non-finite payload — treat as **fail** for premium selling.
    """
    sym = uw_ticker_for_rest(underlying)
    if not sym:
        return None, "bad_symbol"
    if _uw_mock_soft():
        return 55.0, "uw_mock_soft"
    status, body, _ = uw_http_get(f"/api/stock/{sym}/iv-rank", cache_policy=UW_WHEEL_CACHE_IV)
    if status != 200 or not isinstance(body, dict) or body.get("_blocked"):
        return None, "uw_blocked_or_http"
    rank = _scalar_iv_rank(body)
    if rank is None:
        return None, "missing_iv_rank"
    return rank, "ok"


def iv_rank_at_least(underlying: str, min_rank: float) -> bool:
    """True if IV rank is available and >= min_rank (default policy: fail closed if UW missing)."""
    r, why = fetch_iv_rank(underlying)
    if r is None:
        return False
    return r >= float(min_rank)


def _next_earnings_date_from_payload(body: Dict[str, Any]) -> Optional[date]:
    data = body.get("data")
    rows: List[dict] = []
    if isinstance(data, list):
        rows = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict):
        rows = [data]
    best: Optional[date] = None
    today = datetime.now(timezone.utc).date()
    for row in rows:
        for k in ("report_date", "reportDate", "date", "earnings_date", "earningsDate", "event_date", "eventDate"):
            raw = row.get(k)
            if raw is None:
                continue
            try:
                if isinstance(raw, str):
                    d0 = datetime.strptime(raw[:10], "%Y-%m-%d").date()
                else:
                    continue
            except ValueError:
                continue
            if d0 >= today and (best is None or d0 < best):
                best = d0
    return best


def should_skip_for_earnings(underlying: str, avoid_within_calendar_days: int) -> bool:
    """
    True => skip CSP (earnings too soon). Uses UW /api/stock/{t}/earnings; fail-closed if avoid window > 0 and UW unusable.
    """
    days = int(avoid_within_calendar_days or 0)
    if days <= 0:
        return False
    if _uw_mock_soft():
        return False
    sym = uw_ticker_for_rest(underlying)
    if not sym:
        return True
    status, body, _ = uw_http_get(f"/api/stock/{sym}/earnings", cache_policy=UW_WHEEL_CACHE_EARN)
    if status != 200 or not isinstance(body, dict) or body.get("_blocked"):
        return True
    nxt = _next_earnings_date_from_payload(body)
    if nxt is None:
        return False
    today = datetime.now(timezone.utc).date()
    return (nxt - today).days <= days


@dataclass
class PutWallSnapshot:
    wall_strike: Optional[float]
    wall_oi: int
    spot: float
    ok_data: bool
    reason: str
    rows_used: int


def compute_put_wall_from_oi_change(
    underlying: str,
    spot: float,
    *,
    min_wall_oi: int = DEFAULT_PUT_WALL_MIN_OI,
) -> PutWallSnapshot:
    """
    Put wall = strike at or below spot with maximum put ``curr_oi`` from UW oi-change list (institutional deck proxy).

    ``ok_data`` is False when UW is blocked/empty — callers must **not** sell on silent failure.
    """
    sym = uw_ticker_for_rest(underlying)
    if not sym or spot <= 0:
        return PutWallSnapshot(None, 0, spot, False, "bad_inputs", 0)
    if _uw_mock_soft():
        ws = round(float(spot) * 0.97, 2)
        oi = max(min_wall_oi, 10_000)
        return PutWallSnapshot(ws, oi, spot, True, "uw_mock_soft", 0)
    status, body, _ = uw_http_get(
        f"/api/stock/{sym}/oi-change",
        params={"limit": 200, "order": "desc"},
        cache_policy=UW_WHEEL_CACHE_OI,
    )
    if status != 200 or not isinstance(body, dict) or body.get("_blocked"):
        return PutWallSnapshot(None, 0, spot, False, "uw_blocked_or_http", 0)
    rows = body.get("data")
    if not isinstance(rows, list) or not rows:
        return PutWallSnapshot(None, 0, spot, False, "empty_oi_change", 0)

    best_strike: Optional[float] = None
    best_oi = 0
    used = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        osym = str(row.get("option_symbol") or "")
        if _side_from_option_symbol(osym) != "P":
            continue
        strike = occ_strike_price(osym)
        if strike is None or strike > spot:
            continue
        try:
            oi = int(row.get("curr_oi") or 0)
        except (TypeError, ValueError):
            oi = 0
        used += 1
        if oi > best_oi:
            best_oi = oi
            best_strike = strike

    if best_strike is None or best_oi < min_wall_oi:
        return PutWallSnapshot(best_strike, best_oi, spot, False, "no_put_wall_meets_min_oi", used)

    return PutWallSnapshot(best_strike, best_oi, spot, True, "ok", used)


def institutional_put_floor_ok(
    underlying: str,
    spot: float,
    candidate_put_strike: float,
    *,
    min_wall_oi: int = DEFAULT_PUT_WALL_MIN_OI,
) -> Tuple[bool, PutWallSnapshot]:
    """
    Only sell CSP when a significant put wall exists **at or below** the candidate strike.

    Condition: ``wall_strike <= candidate_put_strike`` and wall OI >= min_wall_oi.
    """
    snap = compute_put_wall_from_oi_change(underlying, spot, min_wall_oi=min_wall_oi)
    if not snap.ok_data or snap.wall_strike is None:
        return False, snap
    if snap.wall_strike > candidate_put_strike + 1e-9:
        return False, snap
    return True, snap


def premium_meets_min_credit(limit_price_per_share: float, min_credit_usd: float) -> bool:
    """Per-contract credit = limit * 100 (short premium convention)."""
    if min_credit_usd <= 0:
        return True
    try:
        credit = float(limit_price_per_share) * 100.0
    except (TypeError, ValueError):
        return False
    return credit >= float(min_credit_usd)


def circuit_breaker_gap_down(spot: float, prev_close: Optional[float], threshold: float = 0.35) -> bool:
    """True => halt new CSP writes (e.g. >=35% gap from prev close). prev_close None => do not trip."""
    if prev_close is None or prev_close <= 0 or spot <= 0:
        return False
    return (prev_close - spot) / prev_close >= threshold


def circuit_breaker_illiquid_chain(open_interest: int, volume: int, min_oi: int, min_vol: int) -> bool:
    """True => skip strike (illiquid chain)."""
    return open_interest < min_oi or volume < min_vol


def circuit_breaker_pin_risk(dte: int, hours_to_close: float, max_dte_for_pin: int = 2) -> bool:
    """True => elevated pin risk (very short DTE into last hours) — skip opening new gamma-heavy legs."""
    return dte <= max_dte_for_pin and hours_to_close < 2.0


def fetch_uw_iv_atm_and_rv20d(underlying: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Single UW call: implied (ATM) and realized (20d proxy) annualized vols as decimals (e.g. 0.32 = 32%).

    Uses ``/api/stock/{ticker}/volatility/realized`` (see main._normalize_realized_vol).
    """
    sym = uw_ticker_for_rest(underlying)
    if not sym:
        return None, None, "bad_symbol"
    if _uw_mock_soft():
        return 0.35, 0.22, "uw_mock_soft"
    status, body, _ = uw_http_get(f"/api/stock/{sym}/volatility/realized", cache_policy=UW_WHEEL_CACHE_VOL)
    if status != 200 or not isinstance(body, dict) or body.get("_blocked"):
        return None, None, "uw_blocked_or_http"
    data = body.get("data")
    row: Dict[str, Any] = {}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        row = data[0]
    elif isinstance(data, dict):
        row = data
    try:
        iv = float(row.get("iv_atm") or row.get("ivAtm") or 0)
    except (TypeError, ValueError):
        iv = 0.0
    try:
        rv = float(row.get("rv_20d") or row.get("rv20d") or row.get("realized_vol_20d") or 0)
    except (TypeError, ValueError):
        rv = 0.0
    if iv <= 0 and rv <= 0:
        return None, None, "missing_iv_rv"
    iv_f = iv if iv > 0 else None
    rv_f = rv if rv > 0 else None
    return iv_f, rv_f, "ok"


def sitter_iv_minus_rv_bonus(underlying: str) -> float:
    """
    Non-negative score bump when IV (ATM) > RV (20d) — for wheel universe sitter ranking on SP100.

    Returns ``max(0, iv - rv) * 100`` (typical scale 0–5) or 0.0 when data missing (no penalty).
    """
    iv, rv, ok = fetch_uw_iv_atm_and_rv20d(underlying)
    if iv is None or rv is None or ok != "ok":
        return 0.0
    return max(0.0, (iv - rv)) * 100.0


def compute_rsi_wilder(closes: List[float], period: int = 14) -> Optional[float]:
    """Wilder RSI on closing prices; needs len >= period + 1."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    if len(deltas) < period:
        return None
    gains = [max(d, 0.0) for d in deltas[:period]]
    losses = [max(-d, 0.0) for d in deltas[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period, len(deltas)):
        g = max(deltas[i], 0.0)
        l = max(-deltas[i], 0.0)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss <= 1e-12:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def rsi_from_alpaca_daily(api, underlying: str, period: int = 14) -> Tuple[Optional[float], str]:
    """RSI(period) from last ~40 daily closes. Returns (rsi, reason)."""
    sym = normalize_equity_symbol(underlying)
    if not sym or api is None:
        return None, "no_symbol_or_api"
    try:
        bars = api.get_bars(sym, "1Day", limit=min(period + 30, 60))
        closes: List[float] = []
        if hasattr(bars, "df") and bars.df is not None and not bars.df.empty:
            df = bars.df
            col = "close" if "close" in df.columns else "c"
            if col in df.columns:
                closes = [float(x) for x in df[col].tolist() if x is not None]
        elif isinstance(bars, list) and bars:
            for b in bars:
                if isinstance(b, dict):
                    v = b.get("c") or b.get("close")
                    if v is not None:
                        closes.append(float(v))
        if len(closes) < period + 1:
            return None, "insufficient_bars"
        rsi = compute_rsi_wilder(closes, period=period)
        return rsi, "ok" if rsi is not None else "rsi_undef"
    except Exception as e:
        return None, str(e)[:80]


def should_veto_csp_rsi_overbought(api, underlying: str, max_rsi: float = 70.0) -> Tuple[bool, str]:
    """
    True => skip CSP (overextended / sell into resistance).

    ``max_rsi`` <= 0 disables the gate (always allow).
    """
    if float(max_rsi or 0) <= 0:
        return False, "disabled"
    rsi, why = rsi_from_alpaca_daily(api, underlying)
    if rsi is None:
        return False, f"no_rsi:{why}"
    if rsi > float(max_rsi):
        return True, f"rsi_overbought:{rsi:.1f}>{max_rsi}"
    return False, "ok"
