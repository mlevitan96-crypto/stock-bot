#!/usr/bin/env python3
"""
MFE/MAE hold-period analysis + TP/SL grid search on strict Alpaca cohort.

- Cohort: same trade_ids as ``evaluate_completeness(..., collect_strict_cohort_trade_ids=True)``
  (default ``open_ts_epoch=STRICT_EPOCH_START``).
- Bars: Alpaca 1Min via ``alpaca_trade_api.REST`` (keys from env), batched by symbol with one
  range fetch per symbol. Optional cache under ``data/bars_mfe_cache/``.
- Counterfactual: first-touch TP/SL on 1m OHLC; same-bar TP+SL → SL first (conservative).

Writes Markdown report (default ``results_tp_sl.md`` at repo root; override with ``--out``).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv

    _env = _ROOT / ".env"
    if _env.is_file():
        load_dotenv(_env, override=False)
except Exception:
    pass

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)
from src.telemetry.alpaca_trade_key import normalize_side  # noqa: E402


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_exit_attribution(path: Path) -> List[dict]:
    if not path.is_file():
        return []
    rows: List[dict] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _exit_epoch(rec: dict) -> Optional[float]:
    for k in ("exit_ts", "timestamp", "ts", "exit_timestamp"):
        dt = _parse_ts(rec.get(k))
        if dt:
            return dt.timestamp()
    return None


def _load_strict_cohort_rows(root: Path, open_ts_epoch: float) -> Tuple[List[str], Dict[str, dict]]:
    r = evaluate_completeness(
        root,
        open_ts_epoch=open_ts_epoch,
        audit=False,
        collect_strict_cohort_trade_ids=True,
    )
    ids: List[str] = list(r.get("strict_cohort_trade_ids") or [])
    want = set(ids)
    by_tid: Dict[str, dict] = {}
    exit_path = root / "logs" / "exit_attribution.jsonl"
    for rec in _iter_exit_attribution(exit_path):
        tid = str(rec.get("trade_id") or "")
        if tid in want:
            by_tid[tid] = rec
    return ids, by_tid


def _trade_fields(rec: dict) -> Optional[Tuple[str, datetime, datetime, float, float, str]]:
    """symbol, t_entry, t_exit, entry_px, exit_px, side_norm LONG|SHORT."""
    sym = str(rec.get("symbol") or "").upper().strip()
    if not sym or sym == "?":
        return None
    raw_side = rec.get("position_side") or rec.get("side") or "long"
    side = normalize_side(raw_side)
    ent = _parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    ex = _parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
    if ent is None or ex is None or ex <= ent:
        return None
    try:
        ep = float(rec.get("entry_price") or 0.0)
        xp = float(rec.get("exit_price") or 0.0)
    except (TypeError, ValueError):
        return None
    if ep <= 0 or xp <= 0:
        return None
    return sym, ent, ex, ep, xp, side


def _bars_from_df(resp: Any) -> List[Dict[str, Any]]:
    df = getattr(resp, "df", None)
    if df is None or len(df) == 0:
        return []
    out: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        t = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
        if hasattr(idx, "tz_localize") and idx.tzinfo is None:
            t = idx.tz_localize("UTC").isoformat().replace("+00:00", "Z")
        out.append(
            {
                "t": t,
                "o": float(row.get("open", row.get("o", 0))),
                "h": float(row.get("high", row.get("h", 0))),
                "l": float(row.get("low", row.get("l", 0))),
                "c": float(row.get("close", row.get("c", 0))),
            }
        )
    return out


def _filter_window(bars: List[Dict[str, Any]], t0: datetime, t1: datetime) -> List[Dict[str, Any]]:
    out = []
    for b in bars:
        dt = _parse_ts(b.get("t"))
        if dt is None:
            continue
        if dt < t0 - timedelta(minutes=1):
            continue
        if dt > t1 + timedelta(minutes=1):
            continue
        out.append(b)
    out.sort(key=lambda x: (_parse_ts(x["t"]) or datetime.min.replace(tzinfo=timezone.utc)))
    return out


def _mfe_mae_from_bars(
    bars: List[Dict[str, Any]], side: str, entry_px: float
) -> Tuple[float, float]:
    """Return (MFE%, MAE%) in signed percent space (MAE <= 0 for long, MAE <= 0 typical for short)."""
    if not bars or entry_px <= 0:
        return 0.0, 0.0
    p = entry_px
    if side == "LONG":
        highs = [(b["h"] - p) / p * 100.0 for b in bars]
        lows = [(b["l"] - p) / p * 100.0 for b in bars]
        return float(max(highs)), float(min(lows))
    highs = [(p - b["h"]) / p * 100.0 for b in bars]
    lows = [(p - b["l"]) / p * 100.0 for b in bars]
    return float(max(lows)), float(min(highs))


def _simulate_tp_sl(
    bars: List[Dict[str, Any]],
    side: str,
    entry_px: float,
    exit_px: float,
    tp_pct: float,
    sl_pct: float,
) -> float:
    """
    First-touch path PnL% vs entry. sl_pct is negative (e.g. -1.0).
    Same bar: SL before TP (conservative).
    If neither hits, actual hold return from entry to exit_px.
    """
    p = entry_px
    sl_mag = abs(sl_pct)
    if side == "LONG":

        def bar_outcome(b: Dict[str, Any]) -> Optional[Tuple[str, float]]:
            low_pct = (b["l"] - p) / p * 100.0
            high_pct = (b["h"] - p) / p * 100.0
            hit_sl = low_pct <= sl_pct
            hit_tp = high_pct >= tp_pct
            if hit_sl and hit_tp:
                return "SL", sl_pct
            if hit_sl:
                return "SL", sl_pct
            if hit_tp:
                return "TP", tp_pct
            return None

    else:

        def bar_outcome(b: Dict[str, Any]) -> Optional[Tuple[str, float]]:
            adv = (b["h"] - p) / p * 100.0
            fav = (p - b["l"]) / p * 100.0
            hit_sl = adv >= sl_mag
            hit_tp = fav >= tp_pct
            if hit_sl and hit_tp:
                return "SL", -sl_mag
            if hit_sl:
                return "SL", -sl_mag
            if hit_tp:
                return "TP", tp_pct
            return None

    for b in bars:
        o = bar_outcome(b)
        if o:
            return float(o[1])
    if side == "LONG":
        return (exit_px - p) / p * 100.0
    return (p - exit_px) / p * 100.0


def _alpaca_rest():
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        return None
    try:
        from alpaca_trade_api import REST

        return REST(key, secret, base_url=base)
    except Exception:
        return None


async def _fetch_symbol_bars(
    sym: str,
    t_min: datetime,
    t_max: datetime,
    api: Any,
    cache_dir: Path,
    sem: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    ck = cache_dir / f"{sym}_{t_min.date()}_{t_max.date()}_1m.json"
    if ck.is_file():
        try:
            raw = json.loads(ck.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return raw
        except Exception:
            pass
    start_s = _iso_z(t_min - timedelta(minutes=2))
    end_s = _iso_z(t_max + timedelta(minutes=2))
    async with sem:

        def _call():
            return api.get_bars(sym, "1Min", start=start_s, end=end_s, limit=10000)

        try:
            resp = await asyncio.to_thread(_call)
        except Exception as e:
            print(f"[warn] get_bars {sym}: {e}", file=sys.stderr)
            return []
    bars = _bars_from_df(resp)
    try:
        ck.write_text(json.dumps(bars), encoding="utf-8")
    except Exception:
        pass
    return bars


async def _load_all_bars(
    grouped: Dict[str, List[Tuple[datetime, datetime]]],
    cache_dir: Path,
    concurrency: int,
) -> Dict[str, List[Dict[str, Any]]]:
    api = _alpaca_rest()
    if api is None:
        print("No Alpaca API keys; cannot fetch bars.", file=sys.stderr)
        return {}
    sem = asyncio.Semaphore(max(1, concurrency))
    out: Dict[str, List[Dict[str, Any]]] = {}
    tasks = []
    syms = []
    for sym, spans in grouped.items():
        t0 = min(s[0] for s in spans)
        t1 = max(s[1] for s in spans)
        syms.append(sym)
        tasks.append(_fetch_symbol_bars(sym, t0, t1, api, cache_dir, sem))
    results = await asyncio.gather(*tasks)
    for sym, bars in zip(syms, results):
        out[sym] = bars
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=_ROOT)
    ap.add_argument("--open-ts-epoch", type=float, default=float(STRICT_EPOCH_START))
    ap.add_argument("--out", type=Path, default=_ROOT / "results_tp_sl.md")
    ap.add_argument("--cache-dir", type=Path, default=_ROOT / "data" / "bars_mfe_cache")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--max-trades", type=int, default=0, help="0 = all strict cohort")
    args = ap.parse_args()
    root = args.root.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    ids, by_tid = _load_strict_cohort_rows(root, float(args.open_ts_epoch))
    if args.max_trades > 0:
        ids = ids[: int(args.max_trades)]

    trades: List[dict] = []
    grouped: Dict[str, List[Tuple[datetime, datetime]]] = defaultdict(list)
    skipped = 0
    for tid in ids:
        rec = by_tid.get(tid)
        if not rec:
            skipped += 1
            continue
        tf = _trade_fields(rec)
        if not tf:
            skipped += 1
            continue
        sym, ent, ex, ep, xp, side = tf
        trades.append(
            {
                "trade_id": tid,
                "symbol": sym,
                "t_entry": ent,
                "t_exit": ex,
                "entry_px": ep,
                "exit_px": xp,
                "side": side,
                "actual_pnl_pct": (xp - ep) / ep * 100.0 if side == "LONG" else (ep - xp) / ep * 100.0,
            }
        )
        grouped[sym].append((ent, ex))

    n = len(trades)
    bars_by_sym = asyncio.run(_load_all_bars(grouped, args.cache_dir.resolve(), int(args.concurrency)))

    per_trade: List[dict] = []
    for t in trades:
        sym = t["symbol"]
        raw = bars_by_sym.get(sym) or []
        bars = _filter_window(raw, t["t_entry"], t["t_exit"])
        mfe, mae = _mfe_mae_from_bars(bars, t["side"], t["entry_px"])
        per_trade.append({**t, "bars_n": len(bars), "mfe_pct": mfe, "mae_pct": mae, "bars": bars})

    tp_grid = np.arange(0.25, 5.0 + 1e-9, 0.25)
    sl_grid = -np.arange(0.25, 5.0 + 1e-9, 0.25)
    grid_rows: List[Tuple[float, float, float, float, float, int, int]] = []
    for tp in tp_grid:
        for sl in sl_grid:
            rets: List[float] = []
            wins = 0
            pos_sum = 0.0
            neg_sum = 0.0
            for pt in per_trade:
                bars = pt.get("bars") or []
                r = _simulate_tp_sl(
                    bars,
                    pt["side"],
                    pt["entry_px"],
                    pt["exit_px"],
                    float(tp),
                    float(sl),
                )
                rets.append(r)
                if r > 0:
                    wins += 1
                    pos_sum += r
                elif r < 0:
                    neg_sum += r
            wr = wins / n if n else 0.0
            total = float(sum(rets))
            pf = (pos_sum / abs(neg_sum)) if neg_sum < 0 else float("inf") if pos_sum > 0 else 0.0
            grid_rows.append((float(tp), float(sl), wr, total, float(pf), wins, n - wins))

    grid_rows.sort(key=lambda x: (-(x[4] if np.isfinite(x[4]) else -1), -x[3]))
    top15 = grid_rows[:15]

    mfe_all = np.array([pt["mfe_pct"] for pt in per_trade if pt["bars_n"] > 0], dtype=float)
    mae_all = np.array([pt["mae_pct"] for pt in per_trade if pt["bars_n"] > 0], dtype=float)
    winners = [pt for pt in per_trade if pt["actual_pnl_pct"] > 0 and pt["bars_n"] > 0]
    mae_win = np.array([pt["mae_pct"] for pt in winners], dtype=float)

    def pctile(arr: np.ndarray, q: float) -> float:
        if arr.size == 0:
            return float("nan")
        return float(np.percentile(arr, q))

    mae_5_w = pctile(mae_win, 5) if mae_win.size else float("nan")
    mfe_95_all = pctile(mfe_all, 95) if mfe_all.size else float("nan")

    lines: List[str] = []
    lines.append("# TP/SL grid search — strict cohort MFE/MAE\n")
    lines.append(f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"- **Root:** `{root}`\n")
    lines.append(f"- **open_ts_epoch:** `{args.open_ts_epoch}` (STRICT_EPOCH_START default)\n")
    lines.append(f"- **Strict cohort trade_ids:** {len(ids)} | **Joined exit rows:** {n} | **Skipped:** {skipped}\n")
    lines.append(f"- **Trades with ≥1 1m bar in window:** {sum(1 for p in per_trade if p['bars_n'] > 0)} / {n}\n")
    lines.append("\n## 1) Top 15 TP/SL by profit factor (then total PnL %)\n")
    lines.append("| Rank | TP % | SL % | Win rate | Total PnL % | Profit factor | Wins | Losses |\n")
    lines.append("|-----:|-----:|-----:|---------:|--------------:|--------------:|-----:|-------:|\n")
    for i, (tp, sl, wr, tot, pf, wv, lv) in enumerate(top15, 1):
        pfs = f"{pf:.3f}" if np.isfinite(pf) else "inf"
        lines.append(f"| {i} | {tp:.2f} | {sl:.2f} | {wr*100:.2f}% | {tot:.2f}% | {pfs} | {wv} | {lv} |\n")

    lines.append("\n## 2) MAE “statistical dead zone” (winners, 1m bars)\n")
    lines.append(
        f"- Among **{len(winners)}** trades with **actual PnL % > 0** and non-empty bars: "
        f"**5th percentile of MAE%** = **{mae_5_w:.3f}%**.\n"
    )
    lines.append(
        f"- Interpretation: **~95%** of winners had **MAE ≥ {mae_5_w:.3f}%** (with MAE usually ≤ 0 on longs: they did not draw down past this level more than ~5% of winners did). "
        "Mixed long/short cohort: compare MFE/MAE in context of `side` for deep dives.\n"
    )

    lines.append("\n## 3) MFE “exhaustion” (all trades with bars)\n")
    lines.append(
        f"- **95th percentile of MFE%** across trades with bars: **{mfe_95_all:.3f}%** "
        f"(~**5%** of trades exceeded this favorable excursion).\n"
    )

    lines.append("\n## 4) Raw cohort summary (actual exit)\n")
    act = np.array([p["actual_pnl_pct"] for p in per_trade], dtype=float)
    if act.size:
        lines.append(
            f"- Mean actual PnL %: **{float(np.mean(act)):.3f}%** | Median: **{float(np.median(act)):.3f}%** | "
            f"Win rate (actual): **{100.0 * float(np.mean(act > 0)):.2f}%**\n"
        )
    lines.append("\n## 5) Method notes\n")
    lines.append("- **Bars:** Alpaca `1Min` between entry/exit (±2m pad), one merged fetch per symbol.\n")
    lines.append("- **Same-minute TP+SL:** SL assumed first (conservative).\n")
    lines.append("- **No fills:** If Alpaca returns no bars, counterfactual falls back to **actual** exit return only.\n")

    args.out.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {args.out} ({n} trades, {len(grid_rows)} grid cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
