#!/usr/bin/env python3
"""
Read-only: build artifacts/market_data/alpaca_bars.jsonl for exit-timing replay.

Scans logs/exit_attribution*.jsonl for symbols and entry/exit timestamps, then
fetches 1Min bars via Alpaca Data API v2 (src.data.alpaca_bars_fetcher).

Does not touch order logic. Requires keys in environment (e.g. source .env):
  ALPACA_API_KEY + ALPACA_SECRET_KEY (or ALPACA_KEY / ALPACA_SECRET aliases).

Usage (droplet):
  cd /root/stock-bot && set -a && [ -f .env ] && . ./.env && set +a && PYTHONPATH=. python3 scripts/audit/fetch_alpaca_bars_for_counterfactuals.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import time
import urllib.parse
import urllib.request

REPO = Path(__file__).resolve().parents[2]


def _data_base_url() -> str:
    """Prefer explicit ALPACA_DATA_URL; else live data host (paper keys work per Alpaca; sandbox data URL often empty)."""
    import os

    explicit = (os.getenv("ALPACA_DATA_URL") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    return "https://data.alpaca.markets"


def _bars_headers() -> Dict[str, str]:
    import os

    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_API_SECRET")
        or os.getenv("ALPACA_SECRET", "")
    )
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def _fetch_bars_day(symbol: str, day_start: datetime, day_end: datetime) -> List[Dict[str, Any]]:
    """One GET to Alpaca v2 /stocks/bars for a single calendar day window."""
    start_str = day_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = day_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = _data_base_url() + "/v2/stocks/bars"
    params = {
        "symbols": symbol,
        "timeframe": "1Min",
        "start": start_str,
        "end": end_str,
        "limit": 10000,
        "sort": "asc",
    }
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers=_bars_headers(), method="GET")
    out: List[Dict[str, Any]] = []
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
        j = __import__("json").loads(raw)
        bars_map = j.get("bars") or {}
        for bar in bars_map.get(symbol, []) or []:
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
        time.sleep(0.25)
    except Exception:
        return []
    return out


def _fetch_bars_range(symbol: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """Day-batched fetch for ranges longer than one API window."""
    result: List[Dict[str, Any]] = []
    day = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= end:
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        result.extend(_fetch_bars_day(symbol, day, day_end))
        day = day + timedelta(days=1)

    def _bar_ts(b: Dict[str, Any]) -> datetime:
        t = b.get("t")
        if t is None:
            return start
        try:
            s = str(t).replace("Z", "+00:00")
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        except Exception:
            return start

    result.sort(key=_bar_ts)
    return [b for b in result if start <= _bar_ts(b) <= end]


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def _load_exit_windows(root: Path) -> Dict[str, Tuple[datetime, datetime]]:
    sym_bounds: Dict[str, List[Optional[datetime]]] = defaultdict(lambda: [None, None])
    for path in sorted(root.glob("logs/exit_attribution*.jsonl")):
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sym = str(r.get("symbol") or "").upper().strip()
                if not sym:
                    continue
                entry = _parse_ts(r.get("entry_ts") or r.get("entry_timestamp"))
                ex = _parse_ts(r.get("exit_ts") or r.get("timestamp"))
                lo, hi = sym_bounds[sym]
                for t in (entry, ex):
                    if t is None:
                        continue
                    if lo is None or t < lo:
                        sym_bounds[sym][0] = t
                    if hi is None or t > hi:
                        sym_bounds[sym][1] = t
    out: Dict[str, Tuple[datetime, datetime]] = {}
    for sym, pair in sym_bounds.items():
        lo, hi = pair
        if lo is not None and hi is not None:
            out[sym] = (lo, hi)
    return out


def _load_blocked_windows(root: Path) -> Dict[str, Tuple[datetime, datetime]]:
    """Union of [timestamp, timestamp+60m] per symbol from state/blocked_trades.jsonl."""
    path = root / "state" / "blocked_trades.jsonl"
    if not path.is_file():
        return {}
    sym_bounds: Dict[str, List[Optional[datetime]]] = defaultdict(lambda: [None, None])
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            sym = str(r.get("symbol") or "").upper().strip()
            ts = _parse_ts(r.get("timestamp"))
            if not sym or ts is None:
                continue
            hi = ts + timedelta(minutes=61)
            lo, cur_hi = sym_bounds[sym]
            if lo is None or ts < lo:
                sym_bounds[sym][0] = ts
            if cur_hi is None or hi > cur_hi:
                sym_bounds[sym][1] = hi
    out: Dict[str, Tuple[datetime, datetime]] = {}
    for sym, pair in sym_bounds.items():
        lo, hi = pair
        if lo is not None and hi is not None:
            out[sym] = (lo, hi)
    return out


def _merge_windows(
    a: Dict[str, Tuple[datetime, datetime]], b: Dict[str, Tuple[datetime, datetime]]
) -> Dict[str, Tuple[datetime, datetime]]:
    keys = set(a) | set(b)
    merged: Dict[str, Tuple[datetime, datetime]] = {}
    for k in keys:
        la, ha = a.get(k, (None, None))
        lb, hb = b.get(k, (None, None))
        lo = la if lb is None else lb if la is None else min(la, lb)
        hi = ha if hb is None else hb if ha is None else max(ha, hb)
        if lo is not None and hi is not None:
            merged[k] = (lo, hi)
    return merged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: <root>/artifacts/market_data/alpaca_bars.jsonl",
    )
    ap.add_argument("--pad-days", type=int, default=1, help="Extra calendar days before/after window")
    ap.add_argument(
        "--merge-blocked-state",
        action="store_true",
        help="Union fetch windows with state/blocked_trades.jsonl (block_ts .. block_ts+61m per row).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = args.out or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    import os

    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    sec = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_API_SECRET")
        or os.getenv("ALPACA_SECRET", "")
    )
    if not key or not sec:
        print("ERROR: Missing ALPACA_API_KEY/ALPACA_SECRET_KEY (or ALPACA_KEY/ALPACA_SECRET)", file=sys.stderr)
        return 2

    windows = _load_exit_windows(root)
    if args.merge_blocked_state:
        windows = _merge_windows(windows, _load_blocked_windows(root))
    if not windows:
        print("ERROR: No symbol time windows (exit rows and/or --merge-blocked-state)", file=sys.stderr)
        return 3

    pad = timedelta(days=max(0, int(args.pad_days)))
    written = 0
    with out_path.open("w", encoding="utf-8") as sink:
        for sym, (lo, hi) in sorted(windows.items()):
            start = (lo - pad).replace(hour=0, minute=0, second=0, microsecond=0)
            end = (hi + pad).replace(hour=23, minute=59, second=59, microsecond=999999)
            bars: List[Dict[str, Any]] = _fetch_bars_range(sym, start, end)
            if not bars:
                continue
            rec = {"data": {"bars": {sym: bars}}}
            sink.write(json.dumps(rec, default=str) + "\n")
            written += 1
            print(sym, "bars", len(bars), flush=True)

    print("Wrote", written, "symbol lines to", out_path, flush=True)
    return 0 if written else 4


if __name__ == "__main__":
    raise SystemExit(main())
