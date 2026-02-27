#!/usr/bin/env python3
"""
Fill missing Alpaca bars only. Uses existing bars in data/bars; fetches from Alpaca
only (symbol, date) that are missing. Does NOT re-fetch 30 days from scratch.

Input: either --normalized (path to normalized_exit_truth.json from a previous run)
       or --days N to build exit list from logs/exit_attribution.jsonl (last N days).
Output: data/bars/YYYY-MM-DD/SYMBOL_1Min.json only for previously missing symbol-dates.

Run on droplet so ALPACA_KEY/SECRET and logs/exit_attribution.jsonl are present.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _parse_ts(s) -> datetime | None:
    if s is None:
        return None
    try:
        s = str(s).strip()
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        if s.isdigit():
            return datetime.fromtimestamp(int(s) if len(s) < 11 else int(s) / 1000, tz=timezone.utc)
        return None
    except Exception:
        return None


def _build_normalized_from_exit_attribution(days: int, out_path: Path) -> bool:
    """Build normalized_exit_truth-shaped JSON from logs/exit_attribution.jsonl (last N days)."""
    exit_path = REPO / "logs" / "exit_attribution.jsonl"
    if not exit_path.exists():
        print(f"No {exit_path}; cannot build normalized list.", file=sys.stderr)
        return False

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    exits = []
    seen = set()

    for line in exit_path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ts_val = rec.get("ts") or rec.get("ts_iso") or rec.get("exit_timestamp") or rec.get("timestamp")
        dt = _parse_ts(ts_val)
        if not dt or dt < start:
            continue
        sym = (rec.get("symbol") or "").strip().upper()
        entry_ts = rec.get("entry_timestamp") or rec.get("entry_ts")
        entry_price = rec.get("entry_price") or rec.get("entry_price_avg")
        if not sym or not entry_ts:
            continue
        key = (sym, entry_ts[:10] if isinstance(entry_ts, str) else str(entry_ts)[:10])
        if key in seen:
            continue
        seen.add(key)
        exits.append({
            "symbol": sym,
            "entry_timestamp": entry_ts,
            "entry_ts": entry_ts,
            "exit_timestamp": ts_val,
            "ts": ts_val,
            "entry_price": entry_price,
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"window_start": start.strftime("%Y-%m-%d"), "window_end": end.strftime("%Y-%m-%d"), "count": len(exits), "exits": exits}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Built {len(exits)} exits (last {days} days) -> {out_path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill missing Alpaca bars only; uses existing data/bars.")
    ap.add_argument("--bars_dir", default=None, help="Bars cache dir (default: REPO/data/bars)")
    ap.add_argument("--days", type=int, default=30, help="Days of exit_attribution to consider when building normalized list (default 30)")
    ap.add_argument("--normalized", default=None, help="Path to normalized_exit_truth.json; if set, skip building from exit_attribution")
    ap.add_argument("--out_dir", default=None, help="Where to write missing_bars.json (default: reports/exit_review/fill_bars_<tag>)")
    ap.add_argument("--max_days_per_symbol", type=int, default=20, help="Max symbol-dates to fetch per symbol (default 20)")
    args = ap.parse_args()

    bars_dir = Path(args.bars_dir) if args.bars_dir else REPO / "data" / "bars"
    bars_dir.mkdir(parents=True, exist_ok=True)

    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir) if args.out_dir else REPO / "reports" / "exit_review" / f"fill_bars_{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = Path(args.normalized) if args.normalized else out_dir / "normalized_exit_truth.json"
    if not args.normalized:
        if not _build_normalized_from_exit_attribution(args.days, normalized_path):
            return 1
    elif not normalized_path.exists():
        print(f"Missing --normalized file: {normalized_path}", file=sys.stderr)
        return 1

    missing_path = out_dir / "missing_bars.json"

    # 1) Identify missing (symbol, date)
    r1 = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "analysis" / "find_exits_missing_bars.py"),
            "--normalized", str(normalized_path),
            "--bars_dir", str(bars_dir),
            "--out", str(missing_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r1.returncode != 0:
        print(r1.stderr or r1.stdout or "find_exits_missing_bars failed", file=sys.stderr)
    print(r1.stdout or "")
    if not missing_path.exists():
        print("No missing_bars.json produced; nothing to fill.", file=sys.stderr)
        return 0

    data = json.loads(missing_path.read_text(encoding="utf-8"))
    n_missing = len(data.get("missing", []))
    if n_missing == 0:
        print("No missing symbol-dates; existing bars are sufficient.")
        return 0

    # 2) Fetch only missing from Alpaca
    if not (os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")) or not (os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")):
        print("ALPACA_API_KEY/SECRET not set; cannot fetch. List of missing symbol-dates written to", missing_path, file=sys.stderr)
        return 1

    r2 = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "analysis" / "fetch_missing_bars_from_alpaca.py"),
            "--missing", str(missing_path),
            "--bars_dir", str(bars_dir),
            "--timeframe", "1Min",
            "--max_days_per_symbol", str(args.max_days_per_symbol),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(r2.stdout or "")
    if r2.stderr:
        print(r2.stderr, file=sys.stderr)
    if r2.returncode != 0:
        print("fetch_missing_bars_from_alpaca failed; some gaps may remain.", file=sys.stderr)
        return 1

    print("Fill complete. Existing bars unchanged; only missing symbol-dates were fetched from Alpaca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
