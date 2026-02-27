#!/usr/bin/env python3
"""
Slice a truth JSON (trades + exits) to a time window [start_utc, end_utc].
Used for week-to-date or other windowed reviews. Preserves schema for downstream
label_large_moves, correlate_signals_*, and policy simulation.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _parse_utc(s: str) -> float | None:
    """Parse ISO UTC string (e.g. 2026-02-24T00:00:00Z) to seconds since epoch."""
    if not s or not s.strip():
        return None
    s = s.strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _ts_seconds(ts) -> float | None:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            t = float(ts)
            return t if t > 1e10 else t
        s = str(ts).strip()
        if not s:
            return None
        if s.replace(".", "").replace("-", "").isdigit():
            t = float(ts) if isinstance(ts, (int, float)) else float(s)
            return t / 1000.0 if t > 1e12 else t
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Slice truth by UTC time window")
    ap.add_argument("--truth", required=True, help="Path to truth JSON (trades + exits)")
    ap.add_argument("--start_utc", required=True, help="Start of window (ISO UTC, e.g. 2026-02-24T00:00:00Z)")
    ap.add_argument("--end_utc", default=None, help="End of window (default: now UTC)")
    ap.add_argument("--out", required=True, help="Output path for sliced truth JSON")
    args = ap.parse_args()

    start_s = _parse_utc(args.start_utc)
    if start_s is None:
        print(f"Invalid --start_utc: {args.start_utc}", file=sys.stderr)
        return 1

    end_s = _parse_utc(args.end_utc) if args.end_utc else datetime.now(timezone.utc).timestamp()
    if end_s is not None and end_s < start_s:
        print("end_utc < start_utc", file=sys.stderr)
        return 1

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    if not truth_path.exists():
        print(f"Truth not found: {truth_path}", file=sys.stderr)
        return 1

    data = json.loads(truth_path.read_text(encoding="utf-8"))
    trades = data.get("trades", [])
    exits = data.get("exits", [])

    def in_window(ts) -> bool:
        s = _ts_seconds(ts)
        if s is None:
            return False
        if end_s is not None and s > end_s:
            return False
        return s >= start_s

    trades_slice = [t for t in trades if in_window(t.get("timestamp") or t.get("ts"))]
    exits_slice = [e for e in exits if in_window(e.get("timestamp") or e.get("ts"))]

    out_obj = {
        "window_start_utc": args.start_utc,
        "window_end_utc": args.end_utc or "now",
        "trade_count": len(trades_slice),
        "exit_count": len(exits_slice),
        "trades": trades_slice,
        "exits": exits_slice,
    }
    # Preserve optional top-level keys (e.g. window_start, bar_dates_available) with slice-aware values
    for k in ("window_start", "window_end", "days", "bar_dates_available", "bar_dates_sample"):
        if k in data and k not in out_obj:
            out_obj[k] = data[k]

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}: {len(trades_slice)} trades, {len(exits_slice)} exits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
