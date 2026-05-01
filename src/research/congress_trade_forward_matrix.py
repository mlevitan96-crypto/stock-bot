"""
Congressional-trade forward returns anchored on **filing date** (public knowledge date).

Data sources (caller-supplied via env / existing project config):
- Unusual Whales: ``/api/congress/recent-trades`` (see ``uw_get``).
- Alpaca Data API v2: ``GET /v2/stocks/bars`` (daily closes).

Market-cap filter uses UW ``/api/stock/{ticker}/info`` (``marketcap`` / ``marketcap_size``).
That reflects *contemporary* cap at build time, not point-in-time at ``filing_date`` (documented limitation).
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Hardcoded endpoints (reproducibility / audit trail)
# ---------------------------------------------------------------------------
UW_ENDPOINT_CONGRESS_RECENT = "/api/congress/recent-trades"
UW_ENDPOINT_STOCK_INFO_TMPL = "/api/stock/{ticker}/info"
ALPACA_BARS_PATH = "/v2/stocks/bars"

# Small / mid-cap band (USD) when numeric ``marketcap`` is available
CAP_SMALL_MID_MIN_USD = 300_000_000.0
CAP_SMALL_MID_MAX_USD = 10_000_000_000.0

# STOCK Act reporting window (House PTR cadence; flag laggards)
STOCK_ACT_LAG_FLAG_DAYS = 45

CONGRESS_API_MAX_LIMIT = 200


@dataclass(frozen=True)
class TradeRow:
    ticker: str
    transaction_date: date
    filing_date: date
    amounts_raw: str
    amount_mid_usd: float
    txn_type: str
    member_name: str
    politician_id: str
    raw: Dict[str, Any]


def _parse_iso_date(s: Any) -> Optional[date]:
    if s is None:
        return None
    if isinstance(s, date) and not isinstance(s, datetime):
        return s
    text = str(s).strip()[:10]
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_amount_range_midpoint_usd(amounts: Any) -> Optional[float]:
    """
    Midpoint of a disclosure range, e.g. ``$15,001 - $50,000``.
    Handles open-ended styles best-effort (``Over $50,000`` -> use lower bound * 1.25 heuristic
    only if a single number; otherwise None).
    """
    if amounts is None:
        return None
    s = str(amounts).strip()
    if not s:
        return None
    # Strip currency noise, keep digits and separators for pairs
    nums = re.findall(r"[\d,]+(?:\.\d+)?", s)
    vals: List[float] = []
    for n in nums:
        try:
            vals.append(float(n.replace(",", "")))
        except ValueError:
            continue
    if len(vals) >= 2:
        return (vals[0] + vals[1]) / 2.0
    if len(vals) == 1:
        return vals[0]
    return None


def reporting_lag_days(transaction_date: date, filing_date: date) -> int:
    return (filing_date - transaction_date).days


def parse_marketcap_usd(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        s = str(raw).strip().replace(",", "")
        if not s:
            return None
        return float(s)
    except ValueError:
        return None


def is_small_mid_equity(
    *,
    marketcap_usd: Optional[float],
    marketcap_size: Optional[str],
    issue_type: Optional[str],
) -> bool:
    """Exclude mega/large; keep common stock small/mid by numeric band or UW size tag."""
    it = (issue_type or "").strip().lower()
    if it and it != "common stock":
        return False
    sz = (marketcap_size or "").strip().lower()
    if sz in ("big", "large", "mega"):
        return False
    if sz in ("small", "mid", "medium"):
        return True
    if marketcap_usd is not None and marketcap_usd > 0:
        return CAP_SMALL_MID_MIN_USD <= marketcap_usd < CAP_SMALL_MID_MAX_USD
    return False


def close_on_or_after(sorted_day_closes: List[Tuple[date, float]], target: date) -> Tuple[Optional[date], Optional[float]]:
    """First bar with session date >= ``target``."""
    for d, c in sorted_day_closes:
        if d >= target and c and c > 0:
            return d, float(c)
    return None, None


def load_dotenv_research_then_default(repo_root: str) -> None:
    """Match ``scripts/fetch_alpaca_bars.py`` precedence."""
    try:
        from pathlib import Path

        root = Path(repo_root)
        for path, override in [(root / ".env.research", True), (root / ".env", False)]:
            if not path.exists():
                continue
            try:
                from dotenv import load_dotenv

                load_dotenv(path, override=override)
            except Exception:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and (override or k not in os.environ):
                        os.environ[k] = v
    except Exception:
        pass


def _alpaca_data_base_url() -> str:
    base = os.getenv("ALPACA_BASE_URL", "")
    if "sandbox" in base.lower() or "paper" in base.lower():
        return os.getenv("ALPACA_DATA_URL", "https://data.sandbox.alpaca.markets").rstrip("/")
    return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets").rstrip("/")


def _alpaca_headers() -> Dict[str, str]:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def _alpaca_bars_feed() -> str:
    return (os.getenv("ALPACA_BARS_FEED") or os.getenv("ALPACA_DATA_FEED") or "iex").strip() or "iex"


def fetch_alpaca_daily_bars(
    symbol: str,
    start: date,
    end: date,
    *,
    sleep_s: float = 0.15,
    max_retries: int = 5,
) -> List[Tuple[date, float]]:
    """
    Paginated daily bars for ``symbol`` between ``start`` and ``end`` (inclusive window on dates).
    Returns sorted (date, close). Empty on persistent failure / missing symbol.
    """
    base = _alpaca_data_base_url()
    sym = symbol.strip().upper()
    start_s = start.isoformat() + "T00:00:00Z"
    end_s = end.isoformat() + "T23:59:59Z"
    out: List[Tuple[date, float]] = []
    page_token: Optional[str] = None
    for _ in range(500):
        params: Dict[str, Any] = {
            "symbols": sym,
            "timeframe": "1Day",
            "start": start_s,
            "end": end_s,
            "limit": 10000,
            "sort": "asc",
            "adjustment": "raw",
            "feed": _alpaca_bars_feed(),
        }
        if page_token:
            params["page_token"] = page_token
        url = base + ALPACA_BARS_PATH + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=_alpaca_headers(), method="GET")
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read().decode("utf-8")
                j = json.loads(raw)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 503) and attempt < max_retries:
                    time.sleep(sleep_s * (2**attempt))
                    continue
                return out
            except Exception:
                if attempt < max_retries:
                    time.sleep(sleep_s * (2**attempt))
                    continue
                return out
        else:
            return out

        bars_map = j.get("bars") or {}
        arr = bars_map.get(sym) or []
        for b in arr:
            t = b.get("t")
            if not t:
                continue
            ds = str(t).split("T")[0][:10]
            try:
                d = date.fromisoformat(ds)
            except ValueError:
                continue
            c = float(b.get("c", 0) or 0)
            if c > 0:
                out.append((d, c))
        page_token = j.get("next_page_token")
        time.sleep(sleep_s)
        if not page_token:
            break
    out.sort(key=lambda x: x[0])
    # de-dupe by date (keep last)
    dedup: Dict[date, float] = {}
    for d, c in out:
        dedup[d] = c
    return sorted(dedup.items(), key=lambda x: x[0])


def compute_forward_returns_from_filing(
    sorted_day_closes: List[Tuple[date, float]],
    filing_date: date,
    horizons_calendar_days: Tuple[int, ...] = (30, 90, 180),
) -> Dict[str, Any]:
    """
    R_k = (P(t+h) - P(t)) / P(t) with P on first trading day on/after calendar anchors.
    ``t`` = first trading day on/after ``filing_date``.
    """
    t_date, p0 = close_on_or_after(sorted_day_closes, filing_date)
    row: Dict[str, Any] = {
        "price_anchor_date": t_date.isoformat() if t_date else None,
        "p_filing_anchor": p0,
    }
    if p0 is None or p0 <= 0:
        for h in horizons_calendar_days:
            row[f"p_plus_{h}d_calendar_date"] = None
            row[f"p_plus_{h}d"] = None
            label_m = {30: "1m", 90: "3m", 180: "6m"}.get(h, f"{h}d")
            row[f"r_{label_m}"] = None
        return row

    for h in horizons_calendar_days:
        target = filing_date + timedelta(days=int(h))
        d_h, p_h = close_on_or_after(sorted_day_closes, target)
        label_m = {30: "1m", 90: "3m", 180: "6m"}.get(h, f"{h}d")
        row[f"p_plus_{h}d_calendar_date"] = d_h.isoformat() if d_h else None
        row[f"p_plus_{h}d"] = p_h
        if p_h is not None and p_h > 0:
            row[f"r_{label_m}"] = (p_h - p0) / p0
        else:
            row[f"r_{label_m}"] = None
    return row


def normalize_congress_item(it: Dict[str, Any]) -> Optional[TradeRow]:
    if not isinstance(it, dict):
        return None
    tkr = (it.get("ticker") or it.get("symbol") or "").strip().upper()
    if not tkr or len(tkr) > 10:
        return None
    tx = _parse_iso_date(it.get("transaction_date"))
    fd = _parse_iso_date(it.get("filed_at_date") or it.get("filing_date"))
    if tx is None or fd is None:
        return None
    mid = parse_amount_range_midpoint_usd(it.get("amounts"))
    if mid is None or mid <= 0:
        return None
    return TradeRow(
        ticker=tkr,
        transaction_date=tx,
        filing_date=fd,
        amounts_raw=str(it.get("amounts") or ""),
        amount_mid_usd=float(mid),
        txn_type=str(it.get("txn_type") or ""),
        member_name=str(it.get("name") or it.get("reporter") or ""),
        politician_id=str(it.get("politician_id") or ""),
        raw=dict(it),
    )


def trade_dedupe_key(tr: TradeRow) -> Tuple:
    return (tr.politician_id, tr.ticker, tr.transaction_date.isoformat(), tr.txn_type, tr.amounts_raw, tr.filing_date.isoformat())


def collect_congress_trades_date_walk(
    *,
    end: date,
    days_back: int,
    uw_get_fn: Any,
    limit: int = CONGRESS_API_MAX_LIMIT,
    pause_s: float = 0.35,
) -> List[TradeRow]:
    """
    Walk ``date`` parameter day-by-day to deepen history within UW ``limit`` per call.
    ``uw_get_fn`` must match ``src.uw.uw_client.uw_get`` signature.
    """
    seen: set[Tuple] = set()
    out: List[TradeRow] = []
    d = end
    stop = end - timedelta(days=max(1, int(days_back)))
    cache_policy = {
        "ttl_seconds": 0,
        "endpoint_name": "congress_forward_matrix",
        "max_calls_per_day": 50000,
    }
    while d >= stop:
        resp = uw_get_fn(UW_ENDPOINT_CONGRESS_RECENT, params={"limit": int(limit), "date": d.isoformat()}, cache_policy=cache_policy)
        items = resp.get("data") if isinstance(resp, dict) else None
        if not isinstance(items, list):
            items = []
        for it in items:
            tr = normalize_congress_item(it if isinstance(it, dict) else {})
            if tr is None:
                continue
            k = trade_dedupe_key(tr)
            if k in seen:
                continue
            seen.add(k)
            out.append(tr)
        time.sleep(pause_s)
        d -= timedelta(days=1)
    return out


def fetch_uw_ticker_info(ticker: str, uw_get_fn: Any) -> Dict[str, Any]:
    path = UW_ENDPOINT_STOCK_INFO_TMPL.format(ticker=urllib.parse.quote(ticker.strip().upper()))
    cache_policy = {"ttl_seconds": 3600, "endpoint_name": "stock_info_forward_matrix", "max_calls_per_day": 50000}
    resp = uw_get_fn(path, params=None, cache_policy=cache_policy)
    data = resp.get("data") if isinstance(resp, dict) else None
    return data if isinstance(data, dict) else {}


def summarize_returns(series: pd.Series) -> Dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"n": 0.0, "mean": float("nan"), "median": float("nan"), "win_rate": float("nan")}
    pos = float((s > 0).sum())
    return {
        "n": float(len(s)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "win_rate": pos / float(len(s)),
    }


def build_matrix_dataframe(
    trades: List[TradeRow],
    uw_get_fn: Any,
    *,
    alpaca_pause_s: float = 0.12,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply filters, join UW cap info, Alpaca prices, forward returns."""
    rows_out: List[Dict[str, Any]] = []
    # Adversarial: filing before transaction
    clean: List[TradeRow] = [t for t in trades if t.filing_date >= t.transaction_date]
    dropped_bad_dates = len(trades) - len(clean)

    tickers = sorted({t.ticker for t in clean})
    cap_by_ticker: Dict[str, Dict[str, Any]] = {}
    for sym in tickers:
        info = fetch_uw_ticker_info(sym, uw_get_fn)
        cap_by_ticker[sym] = info
        time.sleep(0.2)

    sm: List[TradeRow] = []
    for t in clean:
        info = cap_by_ticker.get(t.ticker) or {}
        mc = parse_marketcap_usd(info.get("marketcap") or info.get("market_cap"))
        if is_small_mid_equity(
            marketcap_usd=mc,
            marketcap_size=str(info.get("marketcap_size") or "") or None,
            issue_type=str(info.get("issue_type") or "") or None,
        ):
            sm.append(t)

    if not sm:
        meta: Dict[str, Any] = {"dropped_bad_dates": dropped_bad_dates, "after_small_mid": 0}
        return pd.DataFrame(), meta

    mids = [x.amount_mid_usd for x in sm]
    p75 = float(pd.Series(mids).quantile(0.75))
    hi = [t for t in sm if t.amount_mid_usd >= p75]

    # Alpaca: one range per ticker
    min_f = min(t.filing_date for t in hi)
    max_f = max(t.filing_date for t in hi)
    end_bars = max_f + timedelta(days=200)
    bars_cache: Dict[str, List[Tuple[date, float]]] = {}
    for sym in sorted({t.ticker for t in hi}):
        bars_cache[sym] = fetch_alpaca_daily_bars(sym, min_f - timedelta(days=5), end_bars, sleep_s=alpaca_pause_s)

    for t in hi:
        info = cap_by_ticker.get(t.ticker) or {}
        mc = parse_marketcap_usd(info.get("marketcap") or info.get("market_cap"))
        lag = reporting_lag_days(t.transaction_date, t.filing_date)
        bars = bars_cache.get(t.ticker) or []
        fwd = compute_forward_returns_from_filing(bars, t.filing_date)
        rows_out.append(
            {
                "ticker": t.ticker,
                "transaction_date": t.transaction_date.isoformat(),
                "filing_date": t.filing_date.isoformat(),
                "reporting_lag_days": lag,
                "stale_filing_over_45d": bool(lag > STOCK_ACT_LAG_FLAG_DAYS),
                "amounts_raw": t.amounts_raw,
                "amount_mid_usd": t.amount_mid_usd,
                "amount_p75_gate_usd": p75,
                "txn_type": t.txn_type,
                "member_name": t.member_name,
                "politician_id": t.politician_id,
                "uw_marketcap_usd": mc,
                "uw_marketcap_size": info.get("marketcap_size"),
                "uw_issue_type": info.get("issue_type"),
                **fwd,
            }
        )

    df = pd.DataFrame(rows_out)
    meta = {
        "dropped_bad_dates": dropped_bad_dates,
        "after_small_mid": len(sm),
        "amount_p75_usd": p75,
        "rows_after_amount_gate": len(hi),
    }
    return df, meta


def print_summary_report(df: pd.DataFrame, meta: Dict[str, Any]) -> None:
    print("=== Congressional trade forward-return matrix (filing-date anchored) ===")
    print(json.dumps(meta, indent=2, sort_keys=True))
    if df is None or df.empty:
        print("No rows in output dataset; skipping distribution summary.")
        return
    if "stale_filing_over_45d" in df.columns:
        stale = int(df["stale_filing_over_45d"].fillna(False).astype(bool).sum())
        print(f"\nStale filings (reporting lag > {STOCK_ACT_LAG_FLAG_DAYS} calendar days): {stale} / {len(df)}")
    for col, label in [("r_1m", "R_1m"), ("r_3m", "R_3m"), ("r_6m", "R_6m")]:
        if col not in df.columns:
            continue
        st = summarize_returns(df[col])
        print(f"\n-- {label} (fractional; e.g. 0.05 = +5%) --")
        print(f"  n (finite):     {int(st['n'])}")
        print(f"  mean:           {st['mean']:.6f}" if st["n"] else "  mean:           n/a")
        print(f"  median:         {st['median']:.6f}" if st["n"] else "  median:         n/a")
        print(f"  win_rate (>0): {st['win_rate']:.4f}" if st["n"] else "  win_rate:       n/a")
