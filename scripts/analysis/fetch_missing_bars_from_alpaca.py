#!/usr/bin/env python3
"""
Fetch missing bars from Alpaca for (symbol, date) list and write to bars_dir.
Uses Market Data API (https://data.alpaca.markets), NOT the trading API.
Bounded by max_days_per_symbol to avoid rate limits. Evidence-only; no trading.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone


def _data_base_url() -> str:
    """Bars come from Data API. Paper/sandbox keys must use data.sandbox.alpaca.markets or 401."""
    base = (os.getenv("ALPACA_BASE_URL") or "").strip()
    if not base or "sandbox" in base.lower() or "paper" in base.lower():
        return os.getenv("ALPACA_DATA_URL", "https://data.sandbox.alpaca.markets")
    return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")


def _headers() -> dict:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET", "")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _fetch_bars_once(base: str, symbol: str, date_str: str, timeframe: str, start_s: str, end_s: str) -> list:
    """Single request to Data API. Returns list of bar dicts or []."""
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start_s,
        "end": end_s,
        "limit": 5000,
        "sort": "asc",
    }
    url = base.rstrip("/") + "/v2/stocks/bars?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        j = json.loads(resp.read().decode("utf-8"))
    bars_map = j.get("bars") or {}
    arr = bars_map.get(symbol, [])
    return [
        {"t": b.get("t"), "o": float(b.get("o", 0)), "h": float(b.get("h", 0)), "l": float(b.get("l", 0)), "c": float(b.get("c", 0)), "v": int(b.get("v", 0))}
        for b in arr
    ]


def fetch_bars(symbol: str, date_str: str, timeframe: str = "1Min") -> list:
    """Fetch full-day bars for date_str (US session) via Data API GET /v2/stocks/bars. On 401, try other host (sandbox vs prod)."""
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")
    if not key or not secret:
        return []
    base = _data_base_url()
    try:
        y, m, d = date_str.split("-")
        day_start = datetime(int(y), int(m), int(d), 13, 30, 0, tzinfo=timezone.utc)
        day_end = datetime(int(y), int(m), int(d), 20, 0, 0, tzinfo=timezone.utc)
        start_s = _iso(day_start)
        end_s = _iso(day_end)
        out = _fetch_bars_once(base, symbol, date_str, timeframe, start_s, end_s)
        if out:
            return out
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # Try the other Data API host (paper keys work on data.sandbox only)
            alt = "https://data.sandbox.alpaca.markets" if "sandbox" not in base else "https://data.alpaca.markets"
            try:
                out = _fetch_bars_once(alt, symbol, date_str, timeframe, start_s, end_s)
                if out and alt != base:
                    print(f"[fetch_missing_bars] 401 on {base} -> succeeded on {alt}", file=sys.stderr)
                return out
            except Exception:
                pass
        print(f"[fetch_missing_bars] {symbol} {timeframe} {date_str}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[fetch_missing_bars] {symbol} {timeframe} {date_str}: {e}", file=sys.stderr)
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--missing", required=True)
    ap.add_argument("--bars_dir", required=True)
    ap.add_argument("--timeframe", default="1Min")
    ap.add_argument("--max_days_per_symbol", type=int, default=10)
    args = ap.parse_args()
    missing_path = Path(args.missing)
    bars_dir = Path(args.bars_dir)
    bars_dir.mkdir(parents=True, exist_ok=True)

    if not missing_path.exists():
        print("Missing file: no missing_bars.json", file=sys.stderr)
        return 1

    data = json.loads(missing_path.read_text(encoding="utf-8"))
    missing_list = data.get("missing", [])
    if not missing_list:
        print("No missing symbol-dates to fetch")
        return 0

    # Group by symbol, take up to max_days_per_symbol per symbol
    by_sym = defaultdict(list)
    for m in missing_list:
        by_sym[m["symbol"]].append(m["date"])
    to_fetch = []
    for sym, dates in by_sym.items():
        for d in sorted(set(dates))[: args.max_days_per_symbol]:
            to_fetch.append((sym, d))

    if not (os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")) or not (os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")):
        print("ALPACA_API_KEY/SECRET not set; cannot fetch bars", file=sys.stderr)
        return 1

    written = 0
    for symbol, date_str in to_fetch:
        bars = fetch_bars(symbol, date_str, args.timeframe)
        if not bars:
            continue
        safe = (symbol or "").replace("/", "_").strip() or "unknown"
        out_path = bars_dir / date_str / f"{safe}_{args.timeframe}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            out_path.write_text(
                json.dumps({"symbol": symbol, "date": date_str, "timeframe": args.timeframe, "bars": bars}, indent=2),
                encoding="utf-8",
            )
            written += 1
        except Exception as e:
            print(f"Write {out_path}: {e}", file=sys.stderr)
    print(f"Fetched and wrote {written}/{len(to_fetch)} symbol-dates -> {bars_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
