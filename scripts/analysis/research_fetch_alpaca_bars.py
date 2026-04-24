#!/usr/bin/env python3
"""
Research-only Alpaca historical bars → SQLite (does not touch live caches).

Fetches 1Min or 5Min bars via Alpaca Data API v2 for a symbol list over the last N days,
with pagination, and stores rows in ``data/research_bars.db`` (configurable).

Requires ``ALPACA_API_KEY`` / ``ALPACA_SECRET_KEY`` (or ALPACA_KEY / ALPACA_SECRET).
Optional ``ALPACA_DATA_URL``; use ``--feed iex`` if you do not have SIP entitlement.

Usage (repo root):
  PYTHONPATH=. python scripts/analysis/research_fetch_alpaca_bars.py --symbols SPY,AAPL --days 21 --timeframe 5Min
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Load .env.research first, then .env (same pattern as scripts/fetch_alpaca_bars.py)
for path, override in [(REPO / ".env.research", True), (REPO / ".env", False)]:
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


def _data_base_url() -> str:
    base = os.getenv("ALPACA_BASE_URL", "")
    if "sandbox" in base.lower() or "paper" in base.lower():
        return os.getenv("ALPACA_DATA_URL", "https://data.sandbox.alpaca.markets").rstrip("/")
    return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets").rstrip("/")


def _headers() -> dict[str, str]:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def _normalize_tf(tf: str) -> str:
    t = (tf or "5Min").strip()
    if t.lower() in ("1m", "1min"):
        return "1Min"
    if t.lower() in ("5m", "5min"):
        return "5Min"
    return t if t in ("1Min", "5Min", "15Min", "1Hour", "1Day") else "5Min"


def _fetch_bars_chunk(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str,
    *,
    feed: str | None,
) -> list[dict]:
    """One symbol, one [start,end] window; follows next_page_token until exhausted."""
    start_s = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_s = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = _data_base_url() + "/v2/stocks/bars"
    out: list[dict] = []
    page_token: str | None = None
    while True:
        params: dict[str, str] = {
            "symbols": symbol,
            "timeframe": timeframe,
            "start": start_s,
            "end": end_s,
            "limit": "10000",
            "sort": "asc",
        }
        if feed:
            params["feed"] = feed
        if page_token:
            params["page_token"] = page_token
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"HTTP {e.code} for {symbol}: {body}") from e
        j = json.loads(raw)
        bars_map = j.get("bars") or {}
        for b in bars_map.get(symbol, []):
            out.append(
                {
                    "t": b.get("t"),
                    "o": float(b.get("o", 0)),
                    "h": float(b.get("h", 0)),
                    "l": float(b.get("l", 0)),
                    "c": float(b.get("c", 0)),
                    "v": int(b.get("v", 0) or 0),
                }
            )
        page_token = j.get("next_page_token")
        if not page_token:
            break
        time.sleep(0.15)
    time.sleep(0.2)
    return out


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts_utc TEXT NOT NULL,
            o REAL NOT NULL,
            h REAL NOT NULL,
            l REAL NOT NULL,
            c REAL NOT NULL,
            v INTEGER NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, timeframe, ts_utc)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_bars_sym_tf_ts ON research_bars (symbol, timeframe, ts_utc)"
    )
    conn.commit()


def upsert_bars(
    conn: sqlite3.Connection,
    symbol: str,
    timeframe: str,
    bars: list[dict],
    fetched_at: str,
) -> int:
    n = 0
    for b in bars:
        ts = str(b.get("t") or "")
        if not ts:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO research_bars (symbol, timeframe, ts_utc, o, h, l, c, v, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol.upper(), timeframe, ts, b["o"], b["h"], b["l"], b["c"], b["v"], fetched_at),
        )
        n += 1
    conn.commit()
    return n


def fetch_symbol_range_chunked(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str,
    chunk_days: int,
    feed: str | None,
) -> list[dict]:
    """Split [start,end] into calendar chunks to reduce single-response pressure."""
    tf = _normalize_tf(timeframe)
    all_bars: list[dict] = []
    cur = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start.astimezone(timezone.utc)
    end_u = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end.astimezone(timezone.utc)
    delta = timedelta(days=max(1, chunk_days))
    while cur < end_u:
        chunk_end = min(cur + delta, end_u)
        chunk = _fetch_bars_chunk(symbol, cur, chunk_end, tf, feed=feed)
        all_bars.extend(chunk)
        cur = chunk_end
    # Dedupe by ts preserving order
    seen: set[str] = set()
    deduped: list[dict] = []
    for b in sorted(all_bars, key=lambda x: str(x.get("t") or "")):
        t = str(b.get("t") or "")
        if t and t not in seen:
            seen.add(t)
            deduped.append(b)
    return deduped


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch Alpaca bars into research SQLite DB.")
    ap.add_argument("--symbols", required=True, help="Comma-separated tickers, e.g. SPY,AAPL,MSFT")
    ap.add_argument("--days", type=int, default=21, help="Calendar days back from now (default 21)")
    ap.add_argument("--timeframe", default="5Min", help="1Min or 5Min (default 5Min)")
    ap.add_argument("--db", type=Path, default=REPO / "data" / "research_bars.db", help="SQLite output path")
    ap.add_argument("--feed", default="", help="Optional Alpaca feed, e.g. iex (empty = API default)")
    ap.add_argument("--chunk-days", type=int, default=5, help="Max calendar days per HTTP sub-range")
    args = ap.parse_args()

    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    if not key:
        print("Missing ALPACA_API_KEY / ALPACA_KEY", file=sys.stderr)
        return 1

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        print("No symbols", file=sys.stderr)
        return 1

    end = datetime.now(timezone.utc)
    nd = max(1, min(60, int(args.days)))
    start = end - timedelta(days=nd)
    tf = _normalize_tf(args.timeframe)
    feed = args.feed.strip() or None

    args.db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(args.db))
    try:
        init_db(conn)
        fetched_at = datetime.now(timezone.utc).isoformat()
        total = 0
        for sym in symbols:
            print(f"Fetching {sym} {tf} {start.date()} → {end.date()} …", flush=True)
            bars = fetch_symbol_range_chunked(sym, start, end, tf, args.chunk_days, feed)
            n = upsert_bars(conn, sym, tf, bars, fetched_at)
            total += n
            print(f"  stored {n} bars", flush=True)
    finally:
        conn.close()

    print(f"Done. Total rows upserted: {total} → {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
