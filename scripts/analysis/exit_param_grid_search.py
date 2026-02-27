#!/usr/bin/env python3
"""
Exit parameter grid search: simulate many exit-rule variations on historical exits using bars.
Finds best combinations of trailing_stop_pct, profit_target_pct, stop_loss_pct, time_stop_minutes.
Output: grid_results.json (ranked by total simulated PnL), top configs for board review.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root
REPO = Path(__file__).resolve().parents[2]


def _parse_ts(v: Any) -> Optional[datetime]:
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


def _load_bars_from_dir(bars_dir: Optional[Path], symbol: str, date_str: str, entry_ts: datetime, end_ts: datetime) -> List[Dict]:
    """Read bars from explicit cache dir (e.g. from fetch_missing_bars)."""
    if not bars_dir or not bars_dir.exists():
        return []
    safe = (symbol or "").replace("/", "_").strip() or "unknown"
    for tf in ("1Min", "5Min", "15Min"):
        path = bars_dir / date_str / f"{safe}_{tf}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw = data.get("bars", data) if isinstance(data, dict) else data
            if not isinstance(raw, list):
                continue
            out = []
            for b in raw:
                t = b.get("t") or b.get("timestamp")
                dt = _parse_ts(t)
                if dt and entry_ts <= dt <= end_ts:
                    out.append(b)
            if out:
                return out
        except Exception:
            continue
    return []


def _load_bars_for_exit(
    symbol: str, entry_ts: datetime, exit_ts: datetime, max_minutes: int = 600, bars_dir: Optional[Path] = None
) -> List[Dict]:
    """Load bars from entry to exit (plus buffer). Uses bars_dir if provided, else bars_loader."""
    if not symbol or symbol == "?":
        return []
    end_ts = exit_ts + timedelta(minutes=30)
    date_str = entry_ts.strftime("%Y-%m-%d")
    if bars_dir is not None:
        bars = _load_bars_from_dir(bars_dir, symbol, date_str, entry_ts, end_ts)
        if bars:
            return bars
    try:
        from data.bars_loader import load_bars, load_bars_from_daily_parquet
    except ImportError:
        return []
    # Prefer intraday for exact simulation; parquet is daily so less precise for intraday exits
    # Prefer cache (e.g. from fetch_missing_bars); allow fetch when keys are set (e.g. on droplet with .env)
    bars = load_bars(
        symbol, date_str, timeframe="1Min",
        start_ts=entry_ts, end_ts=end_ts,
        use_cache=True, fetch_if_missing=True,
    )
    if not bars:
        for tf in ("5Min", "15Min"):
            bars = load_bars(
                symbol, date_str, timeframe=tf,
                start_ts=entry_ts, end_ts=end_ts,
                use_cache=True, fetch_if_missing=True,
            )
            if bars:
                break
    if not bars:
        end_date = (entry_ts + timedelta(days=2)).strftime("%Y-%m-%d")
        bars = load_bars_from_daily_parquet(symbol, date_str, end_date)
        if bars and (entry_ts or end_ts):
            out = []
            for b in bars:
                t = b.get("t") or b.get("timestamp")
                dt = _parse_ts(t)
                if dt:
                    if dt < entry_ts:
                        continue
                    if dt > end_ts:
                        break
                    out.append(b)
            return out
        return list(bars) if bars else []
    return list(bars)


def _bar_list(bars: List[Dict], entry_ts: datetime) -> List[Tuple[datetime, float, float, float, float]]:
    """Return (dt, o, h, l, c) for bars at or after entry_ts, sorted by time."""
    out = []
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt is None or dt < entry_ts:
            continue
        o = float(b.get("o") or b.get("open") or 0)
        h = float(b.get("h") or b.get("high") or 0)
        l = float(b.get("l") or b.get("low") or 0)
        c = float(b.get("c") or b.get("close") or 0)
        if o or h or l or c:
            out.append((dt, o, h, l, c))
    out.sort(key=lambda x: x[0])
    return out


def simulate_exit(
    bar_list: List[Tuple[datetime, float, float, float, float]],
    entry_ts: datetime,
    entry_price: float,
    side: str,
    trailing_stop_pct: float,
    profit_target_pct: float,
    stop_loss_pct: float,
    time_stop_minutes: int,
) -> Tuple[float, str]:
    """
    Simulate one exit. Returns (simulated_pnl_pct, exit_reason).
    Long: profit at entry*(1+profit_target_pct), stop at entry*(1-stop_loss_pct), trail from high water.
    """
    if not bar_list or entry_price <= 0:
        return 0.0, "no_bars"
    is_long = (side or "long").lower() not in ("short", "sell")
    time_stop_ts = entry_ts + timedelta(minutes=time_stop_minutes)
    high_water = entry_price
    low_water = entry_price
    for i, (dt, o, h, l, c) in enumerate(bar_list):
        if is_long:
            ret_c = (c - entry_price) / entry_price
            ret_h = (h - entry_price) / entry_price
            ret_l = (l - entry_price) / entry_price
            profit_price = entry_price * (1.0 + profit_target_pct)
            stop_price = entry_price * (1.0 - stop_loss_pct)
            if h >= profit_price:
                return profit_target_pct * 100.0, "profit_target"
            if l <= stop_price:
                return (stop_price - entry_price) / entry_price * 100.0, "stop_loss"
            high_water = max(high_water, h)
            trail_trigger = high_water * (1.0 - trailing_stop_pct)
            if l <= trail_trigger:
                exit_p = min(c, trail_trigger)
                return (exit_p - entry_price) / entry_price * 100.0, "trailing_stop"
        else:
            profit_price = entry_price * (1.0 - profit_target_pct)
            stop_price = entry_price * (1.0 + stop_loss_pct)
            if l <= profit_price:
                return profit_target_pct * 100.0, "profit_target"
            if h >= stop_price:
                return (entry_price - stop_price) / entry_price * 100.0, "stop_loss"
            low_water = min(low_water, l) if i else l
            trail_trigger = low_water * (1.0 + trailing_stop_pct)
            if h >= trail_trigger:
                exit_p = max(c, trail_trigger)
                return (entry_price - exit_p) / entry_price * 100.0, "trailing_stop"
        if dt >= time_stop_ts:
            if is_long:
                return (c - entry_price) / entry_price * 100.0, "time_stop"
            return (entry_price - c) / entry_price * 100.0, "time_stop"
    # session end
    dt, o, h, l, c = bar_list[-1]
    if is_long:
        return (c - entry_price) / entry_price * 100.0, "session_end"
    return (entry_price - c) / entry_price * 100.0, "session_end"


def build_param_grid(
    trailing_pct: Optional[List[float]] = None,
    profit_target_pct: Optional[List[float]] = None,
    stop_loss_pct: Optional[List[float]] = None,
    time_stop_min: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    trailing_pct = trailing_pct or [0.01, 0.015, 0.02, 0.025, 0.03]
    profit_target_pct = profit_target_pct or [0.015, 0.02, 0.025, 0.03]
    stop_loss_pct = stop_loss_pct or [0.02, 0.03]
    time_stop_min = time_stop_min or [120, 180, 240, 360]
    grid = []
    for t, p, s, m in itertools.product(trailing_pct, profit_target_pct, stop_loss_pct, time_stop_min):
        grid.append({
            "trailing_stop_pct": t,
            "profit_target_pct": p,
            "stop_loss_pct": s,
            "time_stop_minutes": m,
        })
    return grid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical", required=True, help="normalized_exit_truth.json")
    ap.add_argument("--out", required=True, help="grid_results.json")
    ap.add_argument("--bars_dir", default=None, help="Optional: read bars from this dir (e.g. repo/data/bars)")
    ap.add_argument("--max_exits", type=int, default=0, help="0 = all")
    ap.add_argument("--grid_size", type=int, default=0, help="0 = full grid; N = sample N random configs")
    args = ap.parse_args()
    in_path = Path(args.historical)
    out_path = Path(args.out)
    bars_dir = Path(args.bars_dir) if args.bars_dir else None
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        out_path.write_text(json.dumps({
            "error": "no_historical",
            "message": "Missing historical exit truth",
            "param_results": [],
            "top_configs": [],
        }, indent=2), encoding="utf-8")
        print("No historical file", file=sys.stderr)
        return 1

    data = json.loads(in_path.read_text(encoding="utf-8"))
    exits = data.get("exits", [])
    if args.max_exits and len(exits) > args.max_exits:
        exits = exits[: args.max_exits]
    param_grid = build_param_grid()
    if args.grid_size and len(param_grid) > args.grid_size:
        import random
        random.seed(42)
        param_grid = random.sample(param_grid, args.grid_size)

    def get_exit_meta(rec: Dict) -> Tuple[Optional[str], Optional[datetime], Optional[float], Optional[datetime], str]:
        sym = (rec.get("symbol") or rec.get("sym") or "").strip().upper() or None
        entry_ts = _parse_ts(rec.get("entry_timestamp") or rec.get("entry_ts"))
        entry_price = rec.get("entry_price") or rec.get("entry_price_avg")
        if entry_price is not None:
            try:
                entry_price = float(entry_price)
            except (TypeError, ValueError):
                entry_price = None
        exit_ts = _parse_ts(rec.get("exit_timestamp") or rec.get("ts") or rec.get("ts_iso") or rec.get("timestamp"))
        side = (rec.get("side") or "long").lower()
        return sym, entry_ts, entry_price, exit_ts, side

    has_meta = sum(1 for rec in exits if all(get_exit_meta(rec)[:4]))
    print(f"Exits with (symbol, entry_ts, entry_price, exit_ts): {has_meta}/{len(exits)}", file=sys.stderr)

    # Run grid: for each param set, sum simulated PnL over exits that have bars
    param_results = []
    for params in param_grid:
        total_pnl_pct = 0.0
        n_simulated = 0
        for rec in exits:
            sym, entry_ts, entry_price, exit_ts, side = get_exit_meta(rec)
            if not sym or not entry_ts or not entry_price or not exit_ts:
                continue
            bars = _load_bars_for_exit(sym, entry_ts, exit_ts, bars_dir=bars_dir)
            bar_list = _bar_list(bars, entry_ts)
            if not bar_list:
                continue
            pnl_pct, _ = simulate_exit(
                bar_list, entry_ts, entry_price, side,
                params["trailing_stop_pct"], params["profit_target_pct"],
                params["stop_loss_pct"], params["time_stop_minutes"],
            )
            total_pnl_pct += pnl_pct
            n_simulated += 1
        param_results.append({
            **params,
            "total_pnl_pct": round(total_pnl_pct, 4),
            "n_simulated": n_simulated,
        })
    param_results.sort(key=lambda x: x["total_pnl_pct"], reverse=True)
    top_configs = param_results[:20]

    n_total = len(exits)
    n_with_bars = max(r["n_simulated"] for r in param_results) if param_results else 0
    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_exits_total": n_total,
        "n_exits_with_bars": n_with_bars,
        "coverage_pct": round(100.0 * n_with_bars / n_total, 2) if n_total else 0,
        "n_param_sets": len(param_results),
        "param_results": param_results,
        "top_configs": top_configs,
    }
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Grid search: {len(param_results)} configs, {n_with_bars}/{n_total} exits simulated, top PnL%={top_configs[0]['total_pnl_pct'] if top_configs else 0} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
