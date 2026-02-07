"""Fetch historical bars from Alpaca Market Data API for traded symbols."""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import requests


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def getenv(k, default=None):
    return os.getenv(k, default)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols-file", required=True, help="newline-separated symbols")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--timeframe", default="1Min")  # 1Min/5Min/15Min/1Hour/1Day, etc.
    ap.add_argument("--out", default="artifacts/market_data/alpaca_bars.jsonl")
    args = ap.parse_args()

    key = getenv("ALPACA_API_KEY_ID") or getenv("ALPACA_KEY")
    sec = getenv("ALPACA_API_SECRET_KEY") or getenv("ALPACA_SECRET")
    if not key or not sec:
        die("Missing ALPACA_API_KEY_ID/ALPACA_API_SECRET_KEY or ALPACA_KEY/ALPACA_SECRET in environment.")

    base = getenv("ALPACA_DATA_BASE", "https://data.alpaca.markets").rstrip("/")
    url = f"{base}/v2/stocks/bars"

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    symbols = [s.strip().upper() for s in open(args.symbols_file).read().splitlines() if s.strip()]
    if not symbols:
        die("No symbols found in symbols-file.")

    headers = {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": sec,
    }

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as out:
        for chunk in chunks(symbols, 200):
            params = {
                "symbols": ",".join(chunk),
                "timeframe": args.timeframe,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "adjustment": "raw",
                "limit": 10000,
            }
            r = requests.get(url, headers=headers, params=params, timeout=60)
            if r.status_code != 200:
                die(f"Alpaca bars request failed: {r.status_code} {r.text[:500]}")
            data = r.json() or {}
            out.write(json.dumps({"params": params, "data": data}) + "\n")
            out.flush()
            time.sleep(0.25)  # politeness
    print("Wrote", args.out)


if __name__ == "__main__":
    main()
