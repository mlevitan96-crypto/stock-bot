#!/usr/bin/env python3
"""
Identify historical exits that are missing bar coverage (no cached bars for symbol/date).
Output: missing_bars.json for fetch_missing_bars_from_alpaca.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

def _parse_ts(v) -> Optional[datetime]:
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


def _has_bars(bars_dir: Path, symbol: str, date_str: str, timeframe: str = "1Min") -> bool:
    """True if bars_dir has cached bars for symbol/date (any of 1Min, 5Min, 15Min)."""
    safe = (symbol or "").replace("/", "_").strip() or "unknown"
    for tf in (timeframe, "1Min", "5Min", "15Min"):
        path = bars_dir / date_str / f"{safe}_{tf}.json"
        if path.exists() and path.stat().st_size > 0:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                bars = data.get("bars", data) if isinstance(data, dict) else data
                if isinstance(bars, list) and len(bars) > 0:
                    return True
            except Exception:
                pass
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True)
    ap.add_argument("--bars_dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    in_path = Path(args.normalized)
    bars_dir = Path(args.bars_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        out_path.write_text(json.dumps({"missing": [], "n_total": 0, "n_with_bars": 0, "n_missing": 0}, indent=2), encoding="utf-8")
        print("No normalized file", file=__import__("sys").stderr)
        return 1

    data = json.loads(in_path.read_text(encoding="utf-8"))
    exits = data.get("exits", [])
    missing = []
    seen = set()

    for rec in exits:
        sym = (rec.get("symbol") or rec.get("sym") or "").strip().upper() or None
        entry_ts = _parse_ts(rec.get("entry_timestamp") or rec.get("entry_ts"))
        entry_price = rec.get("entry_price") or rec.get("entry_price_avg")
        if entry_price is not None:
            try:
                float(entry_price)
            except (TypeError, ValueError):
                entry_price = None
        exit_ts = _parse_ts(rec.get("exit_timestamp") or rec.get("ts") or rec.get("ts_iso") or rec.get("timestamp"))
        if not sym or not entry_ts or not entry_price or not exit_ts:
            continue
        date_str = entry_ts.strftime("%Y-%m-%d")
        key = (sym, date_str)
        if key in seen:
            continue
        seen.add(key)
        if _has_bars(bars_dir, sym, date_str):
            continue
        missing.append({
            "symbol": sym,
            "date": date_str,
            "entry_ts": entry_ts.isoformat(),
            "exit_ts": exit_ts.isoformat(),
        })

    n_total = len(exits)
    n_with_meta = len(seen)  # unique (symbol, date) we considered
    n_missing = len(missing)
    n_with_bars = n_with_meta - n_missing
    out = {
        "missing": missing,
        "n_total": n_total,
        "n_unique_symbol_dates": n_with_meta,
        "n_with_bars": n_with_bars,
        "n_missing": n_missing,
    }
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Missing bars: {n_missing} symbol-dates (of {n_with_meta} unique) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
