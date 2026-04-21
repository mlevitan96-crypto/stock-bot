#!/usr/bin/env python3
"""
Tier-1 quant lab: strict-epoch exit cohort vs UW entry features, entry-time technicals,
macro (SPY/QQQ), correlation / RF importance, and VWAP vs ATR exit simulations.

Usage:
  PYTHONPATH=. python3 scripts/ml/deep_correlation_matrix.py --root /root/stock-bot
  PYTHONPATH=. python3 scripts/ml/deep_correlation_matrix.py --root . --max-rows 200
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402
from src.governance.canonical_trade_count import iter_harvester_era_exit_records_for_csv  # noqa: E402
from src.telemetry.alpaca_trade_key import build_trade_key  # noqa: E402

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _ET = None

_TID_ENTRY_TS = re.compile(r"^open_[A-Z0-9]+_(.+)$")


def parse_ts(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return datetime.fromtimestamp(float(x), tz=timezone.utc)
    s = str(x)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if not math.isfinite(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def is_long_side(side: Any) -> bool:
    s = str(side or "long").lower()
    return s not in ("short", "sell", "s")


@dataclass
class OHLCV:
    t: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


def load_bars_ohlcv_jsonl(path: Path) -> Dict[str, List[OHLCV]]:
    out: Dict[str, List[OHLCV]] = defaultdict(list)
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = payload.get("data") or {}
            b = data.get("bars") or {}
            for sym, arr in b.items():
                if not isinstance(arr, list):
                    continue
                su = str(sym).upper()
                for bar in arr:
                    t = parse_ts(bar.get("t"))
                    c = _safe_float(bar.get("c"))
                    if t is None or c is None:
                        continue
                    o = _safe_float(bar.get("o")) or c
                    h = _safe_float(bar.get("h")) or _safe_float(bar.get("high")) or c
                    l = _safe_float(bar.get("l")) or _safe_float(bar.get("low")) or c
                    v = _safe_float(bar.get("v")) or _safe_float(bar.get("volume")) or 0.0
                    out[su].append(OHLCV(t=t, o=o, h=h, l=l, c=c, v=max(0.0, v)))
    for su in list(out.keys()):
        out[su].sort(key=lambda x: x.t)
    return dict(out)


def session_open_utc(entry_ts: datetime) -> datetime:
    if _ET is None:
        return entry_ts.replace(hour=14, minute=30, second=0, microsecond=0)
    loc = entry_ts.astimezone(_ET).date()
    open_local = datetime(loc.year, loc.month, loc.day, 9, 30, 0, tzinfo=_ET)
    return open_local.astimezone(timezone.utc)


def slice_ohlcv(series: List[OHLCV], t0: datetime, t1: datetime) -> List[OHLCV]:
    if not series:
        return []
    times = [b.t for b in series]
    i0 = bisect.bisect_left(times, t0)
    i1 = bisect.bisect_right(times, t1)
    return series[i0:i1]


def rsi_wilder(closes: List[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gains += d
        else:
            losses -= d
    avg_g = gains / period
    avg_l = losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = max(d, 0.0)
        l = max(-d, 0.0)
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
    if avg_l < 1e-12:
        return 100.0 if avg_g > 0 else 50.0
    rs = avg_g / avg_l
    return 100.0 - (100.0 / (1.0 + rs))


def resample_close_5m(bars: List[OHLCV], t_end: datetime, lookback_min: int = 180) -> List[float]:
    """Last closes in each 5m bucket ending at t_end (exclusive of future)."""
    t_start = t_end - timedelta(minutes=lookback_min)
    win = [b for b in bars if t_start <= b.t <= t_end]
    if not win:
        return []
    bucket_ms = 5 * 60
    by_bucket: Dict[int, float] = {}
    for b in win:
        sec = int(b.t.timestamp())
        bk = sec - (sec % bucket_ms)
        by_bucket[bk] = b.c
    if not by_bucket:
        return []
    keys = sorted(by_bucket.keys())
    return [by_bucket[k] for k in keys]


def true_range(h: float, l: float, pc: float) -> float:
    return max(h - l, abs(h - pc), abs(l - pc))


def atr_series(bars: List[OHLCV], period: int = 14) -> List[float]:
    """Wilder ATR aligned to ``bars`` indices (nan until first full period)."""
    if len(bars) < 2:
        return []
    trs: List[float] = []
    for i, b in enumerate(bars):
        pc = bars[i - 1].c if i > 0 else b.o
        trs.append(true_range(b.h, b.l, pc))
    atr: List[float] = [float("nan")] * len(trs)
    if len(trs) < period:
        return atr
    atr[period - 1] = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        prev = atr[i - 1]
        if math.isnan(prev):
            break
        atr[i] = (prev * (period - 1) + trs[i]) / period
    return atr


def cumulative_vwap_slice(bars: List[OHLCV]) -> List[Tuple[datetime, float]]:
    """Per-bar session VWAP (typical price * v)."""
    cum_pv = 0.0
    cum_v = 0.0
    out: List[Tuple[datetime, float]] = []
    for b in bars:
        tp = (b.h + b.l + b.c) / 3.0 if (b.h and b.l) else b.c
        vv = b.v if b.v > 0 else 1.0
        cum_pv += tp * vv
        cum_v += vv
        out.append((b.t, cum_pv / max(cum_v, 1e-9)))
    return out


def bollinger_position(closes: List[float], period: int = 20, k: float = 2.0) -> Optional[float]:
    if len(closes) < period:
        return None
    w = closes[-period:]
    mu = sum(w) / period
    var = sum((x - mu) ** 2 for x in w) / period
    sd = math.sqrt(max(var, 0.0))
    if sd < 1e-9:
        return 0.5
    upper = mu + k * sd
    lower = mu - k * sd
    c = closes[-1]
    if upper <= lower:
        return 0.5
    return max(0.0, min(1.0, (c - lower) / (upper - lower)))


def flatten_numeric(prefix: str, obj: Any, out: Dict[str, float], depth: int = 0) -> None:
    if depth > 4:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = f"{prefix}{k}" if not prefix else f"{prefix}_{k}"
            flatten_numeric(nk, v, out, depth + 1)
        return
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj[:20]):
            flatten_numeric(f"{prefix}_{i}", v, out, depth + 1)
        return
    if isinstance(obj, bool):
        out[prefix] = 1.0 if obj else 0.0
        return
    if isinstance(obj, (int, float)):
        if math.isfinite(float(obj)):
            out[prefix] = float(obj)
        return
    if isinstance(obj, str):
        v = _safe_float(obj)
        if v is not None:
            out[prefix] = v


def iter_unified_jsonl(root: Path) -> Iterator[dict]:
    paths = [
        root / "logs" / "alpaca_unified_events.jsonl",
        root / "logs" / "strict_backfill_alpaca_unified_events.jsonl",
    ]
    for p in paths:
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(o, dict):
                    yield o


def build_entry_indexes(root: Path) -> Tuple[Dict[str, dict], Dict[str, dict], Dict[str, dict]]:
    """trade_id / canonical_trade_id / trade_key -> latest entry attribution row."""
    by_tid: Dict[str, dict] = {}
    by_ct: Dict[str, dict] = {}
    by_tk: Dict[str, dict] = {}
    for rec in iter_unified_jsonl(root):
        et = str(rec.get("event_type") or "")
        if et != "alpaca_entry_attribution":
            continue
        tid = rec.get("trade_id")
        if tid:
            by_tid[str(tid)] = rec
        ct = rec.get("canonical_trade_id")
        if ct:
            by_ct[str(ct)] = rec
        tk = rec.get("trade_key")
        if tk:
            by_tk[str(tk)] = rec
    return by_tid, by_ct, by_tk


def macro_5m_trend(bars: List[OHLCV], entry_ts: datetime, lookback_5m_bars: int = 6) -> Optional[float]:
    """Fractional change over last N 5m closes before entry."""
    closes = resample_close_5m(bars, entry_ts, lookback_min=120)
    if len(closes) < 2:
        return None
    a = closes[-(lookback_5m_bars + 1) :] if len(closes) > lookback_5m_bars else closes
    if len(a) < 2:
        return None
    return (a[-1] - a[0]) / max(abs(a[0]), 1e-6)


def entry_technicals(
    sym: str,
    entry_ts: datetime,
    bars_by_sym: Dict[str, List[OHLCV]],
) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {
        "rsi_5m_10": None,
        "vwap_dist_at_entry": None,
        "bb_pos_1m_20": None,
        "spy_5m_trend": None,
        "qqq_5m_trend": None,
    }
    bars = bars_by_sym.get(sym.upper()) or []
    if not bars:
        return out
    sess_open = session_open_utc(entry_ts)
    win = slice_ohlcv(bars, sess_open, entry_ts + timedelta(minutes=1))
    if len(win) < 5:
        return out
    closes_1m = [b.c for b in win]
    out["bb_pos_1m_20"] = bollinger_position(closes_1m, period=20, k=2.0)
    c5 = resample_close_5m(bars, entry_ts, lookback_min=120)
    if len(c5) >= 12:
        out["rsi_5m_10"] = rsi_wilder(c5, period=10)
    vw = cumulative_vwap_slice(win)
    if vw:
        last_t, last_v = vw[-1]
        last_c = win[-1].c
        if last_v and abs(last_v) > 1e-9:
            out["vwap_dist_at_entry"] = (last_c - last_v) / abs(last_v)
    for idx_sym, key in (("SPY", "spy_5m_trend"), ("QQQ", "qqq_5m_trend")):
        ib = bars_by_sym.get(idx_sym) or []
        if ib:
            out[key] = macro_5m_trend(ib, entry_ts)
    return out


def simulate_dynamic_exits(
    sym: str,
    side: str,
    entry_ts: datetime,
    exit_ts: datetime,
    entry_px: float,
    exit_px: float,
    qty: float,
    bars_all: List[OHLCV],
) -> Dict[str, Optional[float]]:
    """Return simulated PnL USD for VWAP breach exit and 2x ATR trail vs hold to actual exit bar."""
    long = is_long_side(side)

    def pnl_at(exit_price: float) -> float:
        if long:
            return (exit_price - entry_px) * qty
        return (entry_px - exit_price) * qty

    sess = session_open_utc(entry_ts)
    win = slice_ohlcv(bars_all, sess, exit_ts + timedelta(minutes=2))
    baseline_fill = pnl_at(exit_px)
    if len(win) < 3:
        return {"pnl_baseline_usd": baseline_fill, "pnl_vwap_stop_usd": None, "pnl_atr2x_usd": None}
    atr = atr_series(win, period=14)
    vw_series = cumulative_vwap_slice(win)

    baseline = baseline_fill

    # VWAP stop: first bar after entry where close crosses VWAP adversely
    vwap_exit_px: Optional[float] = None
    for i, b in enumerate(win):
        if b.t < entry_ts:
            continue
        _, vwap = vw_series[i] if i < len(vw_series) else (b.t, entry_px)
        if long and b.c < vwap:
            vwap_exit_px = b.c
            break
        if (not long) and b.c > vwap:
            vwap_exit_px = b.c
            break
    if vwap_exit_px is None:
        vwap_exit_px = exit_px

    # ATR trailing: 2x ATR from peak (long) or trough (short) since entry
    atr_exit_px: Optional[float] = None
    peak = entry_px if long else entry_px
    trough = entry_px
    for i, b in enumerate(win):
        if b.t < entry_ts:
            continue
        a = atr[i] if i < len(atr) else float("nan")
        if long:
            peak = max(peak, b.h)
            if not math.isnan(a):
                stop = peak - 2.0 * a
                if b.l <= stop:
                    atr_exit_px = max(stop, b.l)
                    break
        else:
            trough = min(trough, b.l)
            if not math.isnan(a):
                stop = trough + 2.0 * a
                if b.h >= stop:
                    atr_exit_px = min(stop, b.h)
                    break
    if atr_exit_px is None:
        atr_exit_px = exit_px

    return {
        "pnl_baseline_usd": baseline,
        "pnl_vwap_stop_usd": pnl_at(vwap_exit_px),
        "pnl_atr2x_usd": pnl_at(atr_exit_px),
    }


def cohort_row(
    rec: dict,
    entry_by_tid: Dict[str, dict],
    entry_by_ct: Dict[str, dict],
    entry_by_tk: Dict[str, dict],
    bars: Dict[str, List[OHLCV]],
) -> Optional[Dict[str, Any]]:
    sym = str(rec.get("symbol") or "").upper()
    side = rec.get("side") or rec.get("position_side") or "long"
    tid = str(rec.get("trade_id") or "")
    entry_ts = parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    if entry_ts is None and tid:
        m = _TID_ENTRY_TS.match(tid.strip())
        if m:
            entry_ts = parse_ts(m.group(1))
    exit_ts = parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
    snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
    entry_px = (
        _safe_float(rec.get("entry_price"))
        or _safe_float(snap.get("entry_price"))
        or _safe_float(snap.get("avg_entry_price"))
    )
    exit_px = _safe_float(rec.get("exit_price")) or _safe_float(snap.get("exit_price"))
    qty = (
        _safe_float(rec.get("qty"))
        or _safe_float(snap.get("qty"))
        or _safe_float(rec.get("filled_qty"))
        or _safe_float(snap.get("filled_qty"))
    )
    pnl_usd = _safe_float(rec.get("pnl")) or _safe_float(snap.get("pnl")) or _safe_float(rec.get("pnl_usd"))
    if not sym or entry_ts is None or exit_ts is None or entry_px is None or exit_px is None or qty is None:
        return None
    if pnl_usd is None:
        if is_long_side(side):
            pnl_usd = (exit_px - entry_px) * qty
        else:
            pnl_usd = (entry_px - exit_px) * qty
    notional = abs(float(qty) * float(entry_px))
    pnl_bps = (float(pnl_usd) / notional * 10000.0) if notional > 1e-9 else None

    row: Dict[str, Any] = {
        "trade_id": tid,
        "symbol": sym,
        "side": str(side),
        "realized_pnl_bps": pnl_bps,
        "realized_pnl_usd": float(pnl_usd),
        "hold_hours": max(1e-6, (exit_ts - entry_ts).total_seconds() / 3600.0),
    }

    ent = entry_by_tid.get(tid)
    if ent is None:
        tk_exit = str(rec.get("trade_key") or "").strip()
        if tk_exit and tk_exit in entry_by_tk:
            ent = entry_by_tk[tk_exit]
    if ent is None:
        ct = str(rec.get("canonical_trade_id") or "").strip()
        if ct and ct in entry_by_ct:
            ent = entry_by_ct[ct]
    if ent is None:
        try:
            tk = build_trade_key(sym, side, rec.get("entry_ts") or rec.get("entry_timestamp"))
            ent = entry_by_ct.get(tk) or entry_by_tk.get(tk)
        except Exception:
            ent = None
    uw: Dict[str, float] = {}
    if ent:
        flatten_numeric("uw", ent, uw)
    row.update(uw)

    tech = entry_technicals(sym, entry_ts, bars)
    for k, v in tech.items():
        row[k] = v

    sim = simulate_dynamic_exits(sym, side, entry_ts, exit_ts, float(entry_px), float(exit_px), float(qty), bars.get(sym) or [])
    row["sim_baseline_usd"] = sim.get("pnl_baseline_usd")
    row["sim_vwap_stop_usd"] = sim.get("pnl_vwap_stop_usd")
    row["sim_atr2x_usd"] = sim.get("pnl_atr2x_usd")
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--bars", type=Path, default=None)
    ap.add_argument("--max-rows", type=int, default=0, help="Cap rows for dev (0=all)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")

    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        print("ERROR: numpy and pandas required. pip install pandas", file=sys.stderr)
        return 1

    print("Loading bars OHLCV...", flush=True)
    bars = load_bars_ohlcv_jsonl(bars_path)
    print("Loading unified entry index...", flush=True)
    entry_by_tid, entry_by_ct, entry_by_tk = build_entry_indexes(root)

    rows: List[Dict[str, Any]] = []
    for rec in iter_harvester_era_exit_records_for_csv(root, floor_epoch=float(STRICT_EPOCH_START)):
        r = cohort_row(rec, entry_by_tid, entry_by_ct, entry_by_tk, bars)
        if r:
            rows.append(r)
        if args.max_rows and len(rows) >= int(args.max_rows):
            break

    if len(rows) < 10:
        print("ERROR: too few cohort rows:", len(rows), file=sys.stderr)
        return 1

    df = pd.DataFrame(rows)
    target = "realized_pnl_bps"
    df = df.dropna(subset=[target])
    exclude = {
        "trade_id",
        "symbol",
        "side",
        "realized_pnl_usd",
        "sim_baseline_usd",
        "sim_vwap_stop_usd",
        "sim_atr2x_usd",
    }
    num_cols = [
        c
        for c in df.columns
        if c != target and c not in exclude and pd.api.types.is_numeric_dtype(df[c])
    ]
    Xdf = df[num_cols + [target]].copy()
    Xdf = Xdf.replace([np.inf, -np.inf], np.nan)
    min_non_na = max(10, int(0.05 * len(Xdf)))
    for c in list(num_cols):
        if Xdf[c].notna().sum() < min_non_na:
            Xdf.drop(columns=[c], inplace=True, errors="ignore")
    num_cols = [c for c in Xdf.columns if c != target]

    pearson: Dict[str, float] = {}
    spearman: Dict[str, float] = {}
    y = Xdf[target].astype(float)
    for c in num_cols:
        pair = Xdf[[c, target]].dropna()
        if len(pair) < 15:
            continue
        pr = float(pair[c].corr(pair[target]))
        if not math.isnan(pr):
            pearson[c] = pr
        try:
            from scipy.stats import spearmanr

            sr, _ = spearmanr(pair[c].values, pair[target].values)
            if not math.isnan(sr):
                spearman[c] = float(sr)
        except Exception:
            pass

    def _finite(v: Any) -> bool:
        try:
            x = float(v)
            return x == x and math.isfinite(x)
        except (TypeError, ValueError):
            return False

    finite_pearson = {k: float(v) for k, v in pearson.items() if _finite(v)}
    finite_spearman = {k: float(v) for k, v in spearman.items() if _finite(v)}
    p_sorted = sorted(finite_pearson.items(), key=lambda kv: abs(kv[1]), reverse=True)
    s_sorted = sorted(finite_spearman.items(), key=lambda kv: abs(kv[1]), reverse=True)

    rf_top: List[Dict[str, Any]] = []
    try:
        from sklearn.ensemble import RandomForestRegressor

        X = Xdf[num_cols].fillna(Xdf[num_cols].median())
        y2 = Xdf[target].values
        if len(num_cols) >= 2 and len(y2) >= 30:
            rf = RandomForestRegressor(
                n_estimators=80,
                max_depth=8,
                random_state=42,
                n_jobs=-1,
            )
            rf.fit(X.values, y2)
            imp = rf.feature_importances_
            order = np.argsort(-imp)[: min(15, len(num_cols))]
            for i in order[:5]:
                rf_top.append({"feature": num_cols[int(i)], "importance": float(imp[int(i)])})
    except Exception as e:
        rf_top = [{"error": str(e)}]

    vwap_sum = df["sim_vwap_stop_usd"].sum(skipna=True)
    atr_sum = df["sim_atr2x_usd"].sum(skipna=True)
    base_sum = df["sim_baseline_usd"].sum(skipna=True)
    n_sim = int(df["sim_baseline_usd"].notna().sum())
    n_vw = int(df["sim_vwap_stop_usd"].notna().sum())
    n_at = int(df["sim_atr2x_usd"].notna().sum())

    top_pos = sorted([kv for kv in finite_pearson.items() if kv[1] > 0], key=lambda kv: -kv[1])[:3]
    top_neg = sorted([kv for kv in finite_pearson.items() if kv[1] < 0], key=lambda kv: kv[1])[:3]

    sim_reliable = n_sim > 0 and n_vw > max(20, int(0.5 * n_sim)) and n_at > max(20, int(0.5 * n_sim))
    if sim_reliable and base_sum is not None and not (isinstance(base_sum, float) and math.isnan(base_sum)):
        vw_beat = vwap_sum > base_sum
        at_beat = atr_sum > base_sum
        exit_verdict = (
            f"VWAP stop aggregate {'beats' if vw_beat else 'lags'} baseline; "
            f"ATR 2x trail aggregate {'beats' if at_beat else 'lags'} baseline "
            f"({n_vw}/{n_sim} trades with VWAP sim, {n_at}/{n_sim} with ATR sim)."
        )
    else:
        exit_verdict = (
            f"VWAP/ATR path simulation largely unavailable (VWAP non-null {n_vw}/{n_sim}, ATR {n_at}/{n_sim}); "
            "expand artifacts/market_data/alpaca_bars.jsonl session coverage or use --fetch-bars-live elsewhere. "
            "Do not infer structural exit edge from NaN-heavy sims."
        )

    payload = {
        "root": str(root),
        "STRICT_EPOCH_START": STRICT_EPOCH_START,
        "cohort_rows": len(rows),
        "bars_symbols": len(bars),
        "bars_path": str(bars_path),
        "target": target,
        "top_pearson_abs": [{"feature": k, "pearson": v} for k, v in p_sorted[:25]],
        "top_spearman_abs": [{"feature": k, "spearman": v} for k, v in s_sorted[:25]],
        "random_forest_top5": rf_top,
        "exit_simulation": {
            "trades_with_bar_path": n_sim,
            "trades_with_vwap_sim": n_vw,
            "trades_with_atr_sim": n_at,
            "sum_pnl_usd_baseline_bar_replay": round(float(base_sum), 4) if n_sim else None,
            "sum_pnl_usd_vwap_stop": round(float(vwap_sum), 4) if n_vw else None,
            "sum_pnl_usd_atr2x_trail": round(float(atr_sum), 4) if n_at else None,
            "vwap_vs_baseline_usd_delta": round(float(vwap_sum - base_sum), 4) if n_vw and n_sim else None,
            "atr_vs_baseline_usd_delta": round(float(atr_sum - base_sum), 4) if n_at and n_sim else None,
        },
        "synthesis": {
            "top_3_alpha_drivers_pearson": [{"feature": k, "pearson": v} for k, v in top_pos],
            "top_3_toxic_traits_pearson": [{"feature": k, "pearson": v} for k, v in top_neg],
            "exit_verdict": exit_verdict,
        },
    }

    out_path = args.out or (root / "artifacts" / "ml" / "DEEP_CORRELATION_MATRIX.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    def _json_default(obj: Any) -> Any:
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        raise TypeError(str(type(obj)))

    out_path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    print("Wrote", out_path, flush=True)
    print(json.dumps(payload["synthesis"], indent=2), flush=True)
    print(json.dumps(payload["exit_simulation"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
