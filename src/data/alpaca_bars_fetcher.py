"""
Batched Alpaca bars fetcher with backoff and optional disk cache.
Uses Data API v2; respects rate limits when rate_limit_safe=True.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]


def _data_base_url() -> str:
    base = os.getenv("ALPACA_BASE_URL", "")
    if "sandbox" in base.lower() or "paper" in base.lower():
        return os.getenv("ALPACA_DATA_URL", "https://data.sandbox.alpaca.markets").rstrip("/")
    return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets").rstrip("/")


def _headers() -> Dict[str, str]:
    key = (
        os.getenv("ALPACA_API_KEY")
        or os.getenv("APCA-API-KEY-ID")
        or os.getenv("ALPACA_KEY")
        or ""
    )
    secret = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("APCA-API-SECRET-KEY")
        or os.getenv("ALPACA_API_SECRET")
        or os.getenv("ALPACA_SECRET")
        or ""
    )
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }


def _normalize_resolution(resolution: str) -> str:
    r = (resolution or "1m").strip().lower()
    if r in ("1m", "1min"):
        return "1Min"
    if r in ("5m", "5min"):
        return "5Min"
    if r in ("1h", "1hour"):
        return "1Hour"
    if r in ("1d", "1day"):
        return "1Day"
    return "1Min"


def _bars_list_for_symbol(bars_map: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
    sym_u = (symbol or "").strip().upper()
    if sym_u in bars_map and isinstance(bars_map[sym_u], list):
        return bars_map[sym_u]
    for k, v in bars_map.items():
        if str(k).strip().upper() == sym_u and isinstance(v, list):
            return v
    return []


def fetch_bars_for_range(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str = "1Min",
    limit: int = 10000,
    rate_limit_safe: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch bars from Alpaca Data API v2 for one symbol and time range.
    Returns list of dicts with t, o, h, l, c, v.

    Tries ``feed=sip`` then ``feed=iex`` unless :envvar:`ALPACA_BARS_FEED` is set to a single feed
    (sip, iex, otc, boats). Many accounts lack SIP; without ``feed=iex`` the API can return 403
    and labels would see empty bars.
    """
    sym_upper = (symbol or "").strip().upper()
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    tf = _normalize_resolution(timeframe)
    base_url = _data_base_url() + "/v2/stocks/bars"

    env_feed = (os.getenv("ALPACA_BARS_FEED") or "").strip().lower()
    fixed_feed = env_feed in ("sip", "iex", "otc", "boats")
    if fixed_feed:
        feeds: List[str] = [env_feed]
    else:
        feeds = ["sip", "iex"]

    last_err: Optional[str] = None
    for feed in feeds:
        params = {
            "symbols": sym_upper,
            "timeframe": tf,
            "start": start_str,
            "end": end_str,
            "limit": min(limit, 10000),
            "sort": "asc",
            "feed": feed,
        }
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{base_url}?{query}", headers=_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8")
            j = json.loads(data)
            bars_map = j.get("bars") or {}
            raw_list = _bars_list_for_symbol(bars_map, sym_upper)
            out: List[Dict[str, Any]] = []
            for bar in raw_list:
                out.append(
                    {
                        "t": bar.get("t"),
                        "o": float(bar.get("o", 0)),
                        "h": float(bar.get("h", 0)),
                        "l": float(bar.get("l", 0)),
                        "c": float(bar.get("c", 0)),
                        "v": int(bar.get("v", 0)),
                    }
                )
            if rate_limit_safe:
                time.sleep(0.25)
            if out:
                return out
            # SIP-only accounts may get 403; some return 200 with an empty list — fall back to IEX.
            if not fixed_feed and feed == "sip" and "iex" in feeds:
                continue
            return out
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:400]
            last_err = f"HTTP {e.code} feed={feed} {body}"
            # SIP is subscription-gated; some accounts also see 401 on sip before iex succeeds.
            if feed == "sip" and "iex" in feeds and e.code in (401, 403):
                continue
            break
        except Exception as e:
            last_err = repr(e)
            break

    if last_err and os.getenv("ALPACA_BARS_LOG_ERRORS", "").strip() in ("1", "true", "yes"):
        print(f"alpaca_bars_fetcher: {sym_upper} {start_str}..{end_str}: {last_err}", file=sys.stderr)
    return []


def fetch_bars_cached(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str = "1Min",
    cache_dir: Optional[Path] = None,
    rate_limit_safe: bool = True,
    batch_size_days: int = 1,
) -> List[Dict[str, Any]]:
    """
    Fetch bars for [start, end], using disk cache per (symbol, date, resolution).
    Requests are batched by day when batch_size_days=1 to maximize cache hits.
    """
    from datetime import timedelta
    from src.data.alpaca_bars_cache import get_cached_bars, set_cached_bars

    cache_dir = cache_dir or REPO / "data" / "bars_cache"
    tf = _normalize_resolution(timeframe)
    start_utc = start.replace(tzinfo=start.tzinfo or timezone.utc)
    end_utc = end.replace(tzinfo=end.tzinfo or timezone.utc)
    result: List[Dict[str, Any]] = []
    day = start_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= end_utc:
        date_str = day.strftime("%Y-%m-%d")
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        cached = get_cached_bars(symbol, date_str, tf, cache_dir)
        if cached is not None:
            result.extend(cached)
        else:
            day_bars = fetch_bars_for_range(
                symbol, day, day_end, timeframe=tf, rate_limit_safe=rate_limit_safe
            )
            set_cached_bars(symbol, date_str, tf, day_bars, cache_dir)
            result.extend(day_bars)
        day = day + timedelta(days=1)
    def _bar_ts(b):
        t = b.get("t")
        if t is None:
            return start_utc
        try:
            s = str(t).replace("Z", "+00:00")
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc) if s else start_utc
        except Exception:
            return start_utc
    result.sort(key=_bar_ts)
    return [b for b in result if start_utc <= _bar_ts(b) <= end_utc]
