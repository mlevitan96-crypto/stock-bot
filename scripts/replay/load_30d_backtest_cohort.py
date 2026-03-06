#!/usr/bin/env python3
"""
Load the canonical 30-day backtest cohort from droplet/local logs.

Uses:
- logs/exit_attribution.jsonl (primary: one row per closed trade)
- logs/attribution.jsonl (optional join for entry context)
- reports/board/30d_comprehensive_review.json (window dates only)

Returns a frozen list of trades with: trade_id, symbol, entry_ts, exit_ts,
entry_price, exit_price, realized_pnl, regime_at_entry, side (long/short),
direction_intel_embed (if present).

Usage:
  python scripts/replay/load_30d_backtest_cohort.py [--base-dir .] [--end-date YYYY-MM-DD] [--days 30]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _day_utc(ts: Any) -> str:
    if ts is None:
        return ""
    s = str(ts)[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _normalize_side(r: Dict[str, Any]) -> str:
    d = r.get("direction") or r.get("position_side") or r.get("side") or ""
    d = str(d).strip().lower()
    if d in ("bullish", "long", "buy"):
        return "long"
    if d in ("bearish", "short", "sell"):
        return "short"
    return "long"  # default for legacy records


def load_30d_backtest_cohort(
    base_dir: Path,
    end_date: str,
    days: int = 30,
) -> Tuple[Tuple[Dict[str, Any], ...], List[str]]:
    """
    Load 30d cohort from exit_attribution (+ optional attribution join).
    Returns (frozen list of trade dicts, list of window days).
    """
    try:
        from scripts.analysis.attribution_loader import load_joined_closed_trades
    except Exception:
        load_joined_closed_trades = None

    try:
        t = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return (), []

    start = t - timedelta(days=days - 1)
    window_days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    attr_path = base_dir / "logs" / "attribution.jsonl"
    exit_path = base_dir / "logs" / "exit_attribution.jsonl"

    if not exit_path.exists():
        return (), window_days

    if load_joined_closed_trades and attr_path.exists():
        joined = load_joined_closed_trades(
            attr_path,
            exit_path,
            start_date=window_days[0],
            end_date=window_days[-1],
        )
    else:
        import json
        joined = []
        for line in exit_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if not isinstance(rec, dict):
                    continue
                ts = rec.get("timestamp") or rec.get("ts") or rec.get("entry_timestamp")
                if ts and _day_utc(ts) not in window_days and _day_utc(rec.get("entry_timestamp")) not in window_days:
                    continue
                joined.append(rec)
            except Exception:
                continue

    trades: List[Dict[str, Any]] = []
    for r in joined:
        entry_ts = str(r.get("entry_timestamp") or r.get("entry_ts") or "")
        exit_ts = str(r.get("timestamp") or r.get("ts") or "")
        symbol = (r.get("symbol") or "").upper()
        if not symbol or not entry_ts:
            continue
        try:
            entry_price = float(r.get("entry_price") or 0)
            exit_price = float(r.get("exit_price") or 0)
            pnl = float(r.get("pnl") or r.get("realized_pnl_usd") or r.get("pnl_usd") or 0)
        except (TypeError, ValueError):
            entry_price = exit_price = pnl = 0.0

        trade_id = str(r.get("trade_id") or r.get("decision_id") or f"open_{symbol}_{entry_ts}")
        regime_at_entry = str(r.get("entry_regime") or r.get("entry_regime_label") or "").strip() or "unknown"
        side = _normalize_side(r)
        direction_intel_embed = r.get("direction_intel_embed") if isinstance(r.get("direction_intel_embed"), dict) else None

        trades.append({
            "trade_id": trade_id,
            "symbol": symbol,
            "entry_ts": entry_ts,
            "exit_ts": exit_ts,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "realized_pnl": pnl,
            "regime_at_entry": regime_at_entry,
            "side": side,
            "direction_intel_embed": direction_intel_embed,
            "qty": float(r.get("qty") or 1),
        })
    return (tuple(trades), window_days)


def main() -> int:
    ap = argparse.ArgumentParser(description="Load 30-day backtest cohort (frozen list of trades)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script grandparent)")
    ap.add_argument("--end-date", default="", help="End date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--days", type=int, default=30, help="Window days")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    end_date = (args.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip()
    days = max(1, args.days)

    cohort, window_days = load_30d_backtest_cohort(base, end_date, days)
    if not window_days:
        print("Invalid end-date or no window", file=sys.stderr)
        return 1

    print(f"Window: {window_days[0]} to {window_days[-1]} ({days} days)")
    print(f"Loaded {len(cohort)} trades")
    if cohort:
        sample = cohort[0]
        print(f"Sample keys: {list(sample.keys())}")
        print(f"Sample trade_id: {sample.get('trade_id')}, regime_at_entry: {sample.get('regime_at_entry')}, side: {sample.get('side')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
