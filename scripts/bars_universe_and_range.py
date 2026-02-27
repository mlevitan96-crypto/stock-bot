#!/usr/bin/env python3
"""
Phase 1: Define universe (symbols from score_snapshot + blocked_trades) and date range.
Start = min(snapshot_ts) - 400 trading days, End = max(snapshot_ts).
Write reports/bars/universe_and_range.md.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SNAPSHOT_PATH = REPO / "logs" / "score_snapshot.jsonl"
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
REPORT_DIR = REPO / "reports" / "bars"
REPORT_PATH = REPORT_DIR / "universe_and_range.md"

TRADING_DAYS_BACK = 400


def _parse_ts(v) -> datetime | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def trading_days_back(dt: datetime, n: int) -> datetime:
    """Approximate n trading days before dt (weekdays only)."""
    d = dt
    count = 0
    while count < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            count += 1
    return d


def main() -> int:
    symbols = set()
    timestamps: list[datetime] = []

    if SNAPSHOT_PATH.exists():
        for line in SNAPSHOT_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            s = (r.get("symbol") or r.get("ticker") or "").strip()
            if s and s != "?":
                symbols.add(s)
            ts = _parse_ts(r.get("timestamp") or r.get("ts") or r.get("snapshot_ts"))
            if ts:
                timestamps.append(ts)

    if BLOCKED_PATH.exists():
        for line in BLOCKED_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            s = (r.get("symbol") or "").strip()
            if s and s != "?":
                symbols.add(s)
            ts = _parse_ts(r.get("timestamp") or r.get("ts"))
            if ts:
                timestamps.append(ts)

    if not timestamps:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            "# Universe and range\n\n**Error:** No timestamps found in score_snapshot or blocked_trades.\n",
            encoding="utf-8",
        )
        print("No timestamps in snapshot/blocked_trades")
        return 1

    end_dt = max(timestamps)
    start_dt = trading_days_back(end_dt, TRADING_DAYS_BACK)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    symbol_list = sorted(symbols) if symbols else []

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Universe and date range",
        "",
        "| Item | Value |",
        "|------|-------|",
        f"| Symbols count | {len(symbol_list)} |",
        f"| Start (min - {TRADING_DAYS_BACK} trading days) | {start_str} |",
        f"| End (max snapshot_ts) | {end_str} |",
        "",
        "## Symbols",
        "",
        " ".join(symbol_list[:50]) + (" ..." if len(symbol_list) > 50 else ""),
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Universe: {len(symbol_list)} symbols, range {start_str} to {end_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
