#!/usr/bin/env python3
"""
Analyze Unusual Whales (UW) API usage from quota logs.

This repo logs UW calls to `data/uw_api_quota.jsonl` (see `CacheFiles.UW_API_QUOTA`).
Each line is JSON like:
  {"ts": 1730000000, "url": "https://api.unusualwhales.com/api/...", "params": {...}, "source": "..."}

This script summarizes:
- Total calls in a time window
- Utilization vs a configurable daily limit (default 15,000)
- Calls by endpoint (with ticker path segments normalized to {ticker})
- Calls by ticker (best-effort from params / URL)
- Calls per minute (to spot bursts)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


ET_TZ_NAME = "America/New_York"


def _dt_from_ts(ts: int) -> datetime:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def _to_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _safe_json_loads(line: str) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(line)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _normalize_endpoint(path: str) -> str:
    """
    Collapse per-ticker endpoints into a stable label so counts group correctly.
    """
    # Common UW per-ticker patterns used in this repo.
    patterns: List[Tuple[str, str]] = [
        ("/api/darkpool/", "/api/darkpool/{ticker}"),
        ("/api/insider/", "/api/insider/{ticker}"),
        ("/api/calendar/", "/api/calendar/{ticker}"),
        ("/api/congress/", "/api/congress/{ticker}"),
        ("/api/institutional/", "/api/institutional/{ticker}"),
        ("/api/shorts/", "/api/shorts/{ticker}/..."),
        ("/api/etfs/", "/api/etfs/{ticker}/..."),
        ("/api/stock/", "/api/stock/{ticker}/..."),
    ]
    for prefix, replacement in patterns:
        if path.startswith(prefix):
            # Keep more specificity for stock paths when possible.
            if prefix == "/api/stock/":
                parts = path.split("/")
                # /api/stock/{ticker}/{rest...}
                if len(parts) >= 5:
                    rest = "/".join(parts[4:])
                    return f"/api/stock/{{ticker}}/{rest}"
                return "/api/stock/{ticker}"
            if prefix == "/api/shorts/":
                parts = path.split("/")
                if len(parts) >= 5:
                    rest = "/".join(parts[4:])
                    return f"/api/shorts/{{ticker}}/{rest}"
                return "/api/shorts/{ticker}"
            if prefix == "/api/etfs/":
                parts = path.split("/")
                if len(parts) >= 5:
                    rest = "/".join(parts[4:])
                    return f"/api/etfs/{{ticker}}/{rest}"
                return "/api/etfs/{ticker}"
            return replacement
    return path


def _extract_path(url: str) -> str:
    # Lightweight parse without importing urllib (keeps this script tiny & robust)
    # URL formats seen in logs are standard: https://host/path?query
    try:
        no_proto = url.split("://", 1)[1]
        path_part = no_proto.split("/", 1)[1] if "/" in no_proto else ""
        path = "/" + path_part.split("?", 1)[0]
        return path
    except Exception:
        return url


def _extract_ticker(path: str, params: Dict[str, Any]) -> Optional[str]:
    # Params-based (most common for option flow)
    for k in ("symbol", "ticker"):
        v = params.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()

    # Path-based (darkpool / stock / etfs / shorts / insider / calendar)
    parts = [p for p in path.split("/") if p]
    # Examples:
    # - api darkpool AAPL
    # - api stock AAPL greeks
    # - api etfs SPY in-outflow
    # - api shorts TSLA ftds
    if len(parts) >= 3 and parts[0] == "api":
        if parts[1] in ("darkpool", "stock", "etfs", "shorts", "insider", "calendar", "congress", "institutional"):
            return parts[2].strip().upper()
    return None


@dataclass(frozen=True)
class UWCall:
    ts: int
    dt_utc: datetime
    path: str
    endpoint: str
    ticker: Optional[str]
    source: str


def _iter_calls(path: Path) -> Iterable[UWCall]:
    if not path.exists():
        raise FileNotFoundError(f"Quota log not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            obj = _safe_json_loads(line)
            if not obj:
                continue
            ts = _to_int(obj.get("ts", 0), 0)
            if ts <= 0:
                continue
            url = str(obj.get("url", ""))
            params = obj.get("params", {}) if isinstance(obj.get("params", {}), dict) else {}
            src = str(obj.get("source", "unknown"))
            p = _extract_path(url)
            ep = _normalize_endpoint(p)
            tkr = _extract_ticker(p, params)
            yield UWCall(ts=ts, dt_utc=_dt_from_ts(ts), path=p, endpoint=ep, ticker=tkr, source=src)


def _as_et(dt_utc: datetime) -> datetime:
    if ZoneInfo is None:
        return dt_utc
    try:
        return dt_utc.astimezone(ZoneInfo(ET_TZ_NAME))
    except Exception:
        return dt_utc


def _fmt_pct(n: int, d: int) -> str:
    if d <= 0:
        return "0.0%"
    return f"{(n / d * 100.0):.1f}%"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Summarize UW API usage from data/uw_api_quota.jsonl")
    ap.add_argument("--path", default="data/uw_api_quota.jsonl", help="Path to UW quota log (JSONL).")
    ap.add_argument("--hours", type=float, default=24.0, help="Lookback window in hours.")
    ap.add_argument("--daily-limit", type=int, default=15000, help="Daily request limit for utilization display.")
    ap.add_argument("--top", type=int, default=15, help="How many rows to show for tables.")
    args = ap.parse_args(argv)

    quota_path = Path(args.path)
    lookback = timedelta(hours=float(args.hours))
    now_utc = datetime.now(timezone.utc)
    cutoff_utc = now_utc - lookback

    calls = [c for c in _iter_calls(quota_path) if c.dt_utc >= cutoff_utc]
    if not calls:
        print(f"No UW calls found in last {args.hours:g}h (cutoff UTC {cutoff_utc.isoformat()}).")
        return 0

    total = len(calls)
    by_endpoint = Counter(c.endpoint for c in calls)
    by_ticker = Counter(c.ticker for c in calls if c.ticker)
    by_source = Counter(c.source for c in calls if c.source)

    # Daily utilization display (by ET calendar day)
    by_day_et: Dict[str, int] = defaultdict(int)
    for c in calls:
        day = _as_et(c.dt_utc).strftime("%Y-%m-%d")
        by_day_et[day] += 1

    # Calls per minute (UTC buckets)
    by_minute: Dict[str, int] = defaultdict(int)
    for c in calls:
        key = c.dt_utc.replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M UTC")
        by_minute[key] += 1
    peak_minute = max(by_minute.values()) if by_minute else 0

    print(f"UW usage summary (last {args.hours:g}h)")
    print(f"- Quota log: {quota_path}")
    print(f"- Calls observed: {total:,}")
    print(f"- Peak calls/min (UTC): {peak_minute}")
    print("")

    print("Calls by day (ET):")
    for day in sorted(by_day_et.keys()):
        n = by_day_et[day]
        print(f"- {day}: {n:,}  (util { _fmt_pct(n, args.daily_limit) } of {args.daily_limit:,}/day)")
    print("")

    print(f"Top endpoints (normalized) (top {args.top}):")
    for ep, n in by_endpoint.most_common(args.top):
        print(f"- {n:>7,}  {ep}")
    print("")

    if by_ticker:
        print(f"Top tickers (best-effort) (top {args.top}):")
        for tkr, n in by_ticker.most_common(args.top):
            print(f"- {n:>7,}  {tkr}")
        print("")

    if by_source:
        print("Sources:")
        for src, n in by_source.most_common():
            print(f"- {n:>7,}  {src}")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

