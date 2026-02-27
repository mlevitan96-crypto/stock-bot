#!/usr/bin/env python3
"""
Resumable Kraken 30d OHLC downloader with checkpoint + cache.
Uses Kraken public REST API (no auth). Rate limit: ~1 req/sec.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    requests = None

# Kraken pair symbols (API uses XBT not BTC)
SYMBOL_TO_KRAKEN: Dict[str, str] = {
    "BTC/USD": "XBTUSD",
    "ETH/USD": "ETHUSD",
    "XBT/USD": "XBTUSD",
}

OHLC_BASE = "https://api.kraken.com/0/public/OHLC"
# API returns max 720 candles per request (12h for 1m)
MAX_CANDLES_PER_REQUEST = 720


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_universe(u: str) -> List[str]:
    u = (u or "").strip()
    if u.upper() == "AUTO" or u == "":
        return ["BTC/USD", "ETH/USD"]
    return [x.strip() for x in u.split(",") if x.strip()]


def iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(p: Path, default: Any) -> Any:
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def floor_to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def expected_minutes(start: datetime, end: datetime) -> int:
    delta = end - start
    return int(delta.total_seconds() // 60)


def fetch_kraken_ohlc(
    symbol: str,
    start_ts: datetime,
    end_ts: datetime,
    granularity_sec: int,
) -> List[Dict[str, Any]]:
    """
    Fetch OHLC from Kraken public API. Returns list of bars with ts (ISO), o, h, l, c, v.
    """
    if requests is None:
        return []

    pair = SYMBOL_TO_KRAKEN.get(symbol, symbol.replace("/", "").replace("BTC", "XBT"))
    # Kraken interval: 1, 5, 15, 30, 60, 240, 1440 (minutes)
    interval_min = max(1, granularity_sec // 60)
    since_ts = int(start_ts.timestamp())

    params = {"pair": pair, "interval": interval_min, "since": since_ts}
    try:
        r = requests.get(OHLC_BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    if data.get("error") and data["error"]:
        return []

    result = data.get("result") or {}
    # Result has "LAST" (next since) and one key with array of OHLC (e.g. XXBTZUSD or XBTUSD)
    ohlc_list: List[List[Any]] = []
    for k, v in result.items():
        if k == "last":
            continue
        if isinstance(v, list):
            ohlc_list = v
            break

    bars: List[Dict[str, Any]] = []
    # Kraken format: [time (unix), open, high, low, close, vwap, volume, count]
    for row in ohlc_list:
        if not row or len(row) < 6:
            continue
        ts_unix = int(row[0])
        dt = datetime.fromtimestamp(ts_unix, tz=timezone.utc)
        if dt >= end_ts:
            break
        if dt < start_ts:
            continue
        bars.append({
            "ts": iso(floor_to_minute(dt)),
            "o": str(row[1]),
            "h": str(row[2]),
            "l": str(row[3]),
            "c": str(row[4]),
            "v": str(row[6]) if len(row) > 6 else "0",
        })
    return bars


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--universe", type=str, default="AUTO")
    ap.add_argument("--granularity_sec", type=int, default=60)
    ap.add_argument("--raw_dir", type=str, required=True)
    ap.add_argument("--cache_dir", type=str, required=True)
    ap.add_argument("--checkpoint_dir", type=str, required=True)
    ap.add_argument("--out_dir", type=str, required=True)
    ap.add_argument("--max_loops", type=int, default=999999)
    ap.add_argument("--sleep_sec", type=int, default=2)
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    cache_dir = Path(args.cache_dir)
    ckpt_dir = Path(args.checkpoint_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    end = floor_to_minute(utc_now())
    start = end - timedelta(days=args.days)

    universe = parse_universe(args.universe)

    campaign_manifest: Dict[str, Any] = {
        "window": {"start": iso(start), "end": iso(end), "days": args.days, "granularity_sec": args.granularity_sec},
        "universe": universe,
        "status": "RUNNING",
        "symbols": {},
    }

    for loop_i in range(args.max_loops):
        all_complete = True

        for sym in universe:
            sym_key = sym.replace("/", "_").replace(" ", "")
            sym_raw = raw_dir / sym_key
            sym_cache = cache_dir / sym_key
            sym_ckpt = ckpt_dir / f"{sym_key}.json"
            sym_raw.mkdir(parents=True, exist_ok=True)
            sym_cache.mkdir(parents=True, exist_ok=True)

            ckpt = load_json(sym_ckpt, {})
            last_ts = ckpt.get("last_ts")
            if last_ts:
                cur_start = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                cur_start = start

            if cur_start >= end:
                campaign_manifest["symbols"][sym] = {"complete": True, "last_ts": iso(cur_start)}
                continue

            all_complete = False
            chunk_end = min(cur_start + timedelta(hours=6), end)

            bars = fetch_kraken_ohlc(sym, cur_start, chunk_end, args.granularity_sec)

            chunk_name = f"{iso(cur_start)}__{iso(chunk_end)}.json".replace(":", "").replace("-", "")
            (sym_cache / chunk_name).write_text(
                json.dumps({"symbol": sym, "start": iso(cur_start), "end": iso(chunk_end), "bars": bars}, indent=2),
                encoding="utf-8",
            )

            if bars:
                out_path = sym_raw / "bars_1m.jsonl"
                with out_path.open("a", encoding="utf-8") as f:
                    for b in bars:
                        f.write(json.dumps(b) + "\n")
                # Advance checkpoint to last bar + 1 interval to avoid duplicates
                last_bar_ts = bars[-1].get("ts")
                if last_bar_ts:
                    try:
                        last_dt = datetime.fromisoformat(last_bar_ts.replace("Z", "+00:00"))
                        cur_start = last_dt + timedelta(seconds=args.granularity_sec)
                    except Exception:
                        cur_start = chunk_end
                else:
                    cur_start = chunk_end
            else:
                cur_start = chunk_end

            ckpt["last_ts"] = iso(cur_start)
            save_json(sym_ckpt, ckpt)

            campaign_manifest["symbols"][sym] = {
                "complete": False,
                "last_ts": ckpt["last_ts"],
                "last_chunk": chunk_name,
                "bars_in_chunk": len(bars),
            }

            time.sleep(args.sleep_sec)

        save_json(out_dir / "KRAKEN_30D_DOWNLOAD_STATUS.json", campaign_manifest)

        coverage: Dict[str, Any] = {"window": campaign_manifest["window"], "symbols": {}, "complete": True}
        for sym in universe:
            sym_key = sym.replace("/", "_").replace(" ", "")
            raw_path = raw_dir / sym_key / "bars_1m.jsonl"
            expected = expected_minutes(start, end)
            seen: set[str] = set()
            if raw_path.exists():
                for line in raw_path.read_text(encoding="utf-8").splitlines():
                    try:
                        obj = json.loads(line)
                        ts = obj.get("ts")
                        if ts:
                            seen.add(ts)
                    except Exception:
                        pass
            got = len(seen)
            pct = (got / expected * 100.0) if expected > 0 else 0.0
            sym_ok = pct >= 99.0
            coverage["symbols"][sym] = {"expected_minutes": expected, "got_minutes": got, "pct": round(pct, 3), "ok": sym_ok}
            if not sym_ok:
                coverage["complete"] = False

        save_json(out_dir / "KRAKEN_30D_COVERAGE.json", coverage)

        if coverage["complete"]:
            campaign_manifest["status"] = "COMPLETE"
            save_json(out_dir / "KRAKEN_30D_DOWNLOAD_STATUS.json", campaign_manifest)
            print("KRAKEN 30D COVERAGE COMPLETE")
            return 0

        print(f"Coverage incomplete (loop {loop_i + 1}); continuing...")
        time.sleep(2)

    print("Max loops reached; coverage still incomplete.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
