#!/usr/bin/env python3
"""One-off: max timestamp_utc in SPI CSV + optional UW cache age. Run on droplet."""
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    root = Path(os.environ.get("STOCKBOT_ROOT", "/root/stock-bot"))
    spi = root / "reports" / "Gemini" / "signal_intelligence_spi.csv"
    uw = root / "data" / "uw_flow_cache.json"
    if not spi.is_file():
        print("spi_missing", spi)
        return 1
    best = None
    sym = None
    with spi.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            t = (row.get("timestamp_utc") or "").strip()
            if not t:
                continue
            try:
                d = datetime.fromisoformat(t.replace("Z", "+00:00"))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=timezone.utc)
                else:
                    d = d.astimezone(timezone.utc)
                ts = d.timestamp()
            except Exception:
                continue
            if best is None or ts > best:
                best, sym = ts, row.get("symbol")
    now = time.time()
    print(
        "newest_symbol",
        sym,
        "newest_ts_utc",
        datetime.fromtimestamp(best, tz=timezone.utc).isoformat() if best else None,
        "age_sec",
        round(now - best, 1) if best else None,
    )
    if uw.is_file():
        m = uw.stat().st_mtime
        print("uw_flow_cache_age_sec", round(now - m, 1), "path", uw)
    else:
        print("uw_flow_cache_missing", uw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
