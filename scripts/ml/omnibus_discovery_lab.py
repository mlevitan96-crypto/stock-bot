#!/usr/bin/env python3
"""
Omnibus Discovery Lab: strict cohort + UW (unified events) + 1m bars → exits, seasonality,
macro drag (SPY), and Random Forest feature importance. Writes ``artifacts/ml/OMNIBUS_REPORT.md``.

Usage:
  PYTHONPATH=. python3 scripts/ml/omnibus_discovery_lab.py --root /root/stock-bot
  PYTHONPATH=. python3 scripts/ml/omnibus_discovery_lab.py --root . --max-rows 100
"""
from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from telemetry.alpaca_strict_completeness_gate import (  # noqa: E402
    STRICT_EPOCH_START,
    evaluate_completeness,
)
from src.governance.canonical_trade_count import iter_harvester_era_exit_records_for_csv  # noqa: E402

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    _ET = None


def _load_dcm():
    path = REPO / "scripts" / "ml" / "deep_correlation_matrix.py"
    name = "deep_correlation_matrix_lab"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _iter_jsonl(p: Path) -> Iterator[dict]:
    if not p.is_file():
        return
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


def load_strict_cohort_exit_rows(root: Path, open_ts_epoch: float) -> List[dict]:
    """Prefer strict gate trade_ids ∩ exit_attribution; else harvester-era iterator."""
    gate = evaluate_completeness(
        root,
        open_ts_epoch=float(open_ts_epoch),
        audit=False,
        collect_strict_cohort_trade_ids=True,
    )
    want = {str(x) for x in (gate.get("strict_cohort_trade_ids") or []) if x}
    exit_path = root / "logs" / "exit_attribution.jsonl"
    rows: List[dict] = []
    if want:
        for rec in _iter_jsonl(exit_path):
            tid = str(rec.get("trade_id") or "")
            if tid in want:
                rows.append(rec)
        return rows
    for rec in iter_harvester_era_exit_records_for_csv(root, floor_epoch=float(open_ts_epoch)):
        rows.append(rec)
    return rows


def entry_bucket_et(entry_ts: datetime) -> str:
    if _ET is None:
        return "unknown_tz"
    loc = entry_ts.astimezone(_ET)
    dec = loc.hour * 60 + loc.minute
    open_rth = 9 * 60 + 30
    close_rth = 16 * 60
    if dec < open_rth:
        return "pre_0930_et"
    if dec >= close_rth:
        return "post_1600_et"
    if dec < 10 * 60:
        return "0930_1000_et"
    if dec < 11 * 60:
        return "1000_1100_et"
    if dec < 12 * 60:
        return "1100_1200_et"
    if dec < 13 * 60:
        return "1200_1300_et"
    if dec < 14 * 60:
        return "1300_1400_et"
    if dec < 15 * 60:
        return "1400_1500_et"
    return "1500_1600_et"


def spy_return_leading(
    bars_spy: List[Any],
    entry_ts: datetime,
    lead_minutes: int = 15,
) -> Optional[float]:
    """Fractional SPY close change from last bar <= entry-lead to last bar <= entry."""
    if not bars_spy:
        return None
    times = [b.t for b in bars_spy]
    t_from = entry_ts - timedelta(minutes=lead_minutes)
    i0 = bisect.bisect_right(times, t_from) - 1
    i1 = bisect.bisect_right(times, entry_ts) - 1
    if i0 < 0 or i1 < 0 or i0 >= len(bars_spy) or i1 >= len(bars_spy):
        return None
    c0 = float(bars_spy[i0].c)
    c1 = float(bars_spy[i1].c)
    if c0 <= 1e-9:
        return None
    return (c1 / c0) - 1.0


def spy_tailwind_label(ret: Optional[float]) -> str:
    if ret is None or not math.isfinite(ret):
        return "unknown"
    if ret > 0.0005:
        return "spy_tailwind"
    if ret < -0.0005:
        return "spy_headwind"
    return "spy_neutral"


def simulate_fixed_rr_usd(
    dcm: Any,
    sym: str,
    side: str,
    entry_ts: datetime,
    exit_ts: datetime,
    entry_px: float,
    exit_px: float,
    qty: float,
    bars_sym: List[Any],
    sl_pct: float = 0.5,
    tp_pct: float = 1.0,
) -> Optional[float]:
    """
    1m path from entry to actual exit time. Same-bar TP+SL → SL first (matches training mandate).
    If neither hits, PnL at actual exit_px.
    """
    long = dcm.is_long_side(side)
    sess = dcm.session_open_utc(entry_ts)
    win = dcm.slice_ohlcv(bars_sym, sess, exit_ts + timedelta(minutes=1))
    path = [b for b in win if b.t >= entry_ts and b.t <= exit_ts]
    if not path:
        return None

    def pnl_at(px: float) -> float:
        if long:
            return (px - entry_px) * qty
        return (entry_px - px) * qty

    p = float(entry_px)
    sl_mag = abs(sl_pct)

    for b in path:
        h, low, c = float(b.h), float(b.l), float(b.c)
        if long:
            low_pct = (low - p) / p * 100.0
            high_pct = (h - p) / p * 100.0
            hit_sl = low_pct <= -sl_mag
            hit_tp = high_pct >= tp_pct
            if hit_sl and hit_tp:
                return pnl_at(p * (1.0 - sl_mag / 100.0))
            if hit_sl:
                return pnl_at(p * (1.0 - sl_mag / 100.0))
            if hit_tp:
                return pnl_at(p * (1.0 + tp_pct / 100.0))
        else:
            adv = (h - p) / p * 100.0
            fav = (p - low) / p * 100.0
            hit_sl = adv >= sl_mag
            hit_tp = fav >= tp_pct
            if hit_sl and hit_tp:
                return pnl_at(p * (1.0 + sl_mag / 100.0))
            if hit_sl:
                return pnl_at(p * (1.0 + sl_mag / 100.0))
            if hit_tp:
                return pnl_at(p * (1.0 - tp_pct / 100.0))
    return pnl_at(float(exit_px))


def _md_table(df: Any, floatfmt: str = ".4f") -> str:
    try:
        return df.to_markdown(floatfmt=floatfmt) + "\n"
    except Exception:
        return "```\n" + df.to_string() + "\n```\n"


def run_rf_top10(df: Any, target: str, min_rows: int = 40) -> Tuple[Any, str]:
    import numpy as np
    import pandas as pd

    try:
        from sklearn.ensemble import RandomForestRegressor
    except ImportError:
        return None, "sklearn not installed (`pip install scikit-learn`).\n"

    if target not in df.columns or len(df) < min_rows:
        return None, f"RF skipped (rows={len(df)}, need target `{target}`).\n"

    y = df[target].astype(float)
    Xdf = df.select_dtypes(include=[np.number]).copy()
    # Strict anti-leakage: never put the label (or sibling PnL scale) in X.
    for c in (target, "realized_pnl_usd", "realized_pnl_bps"):
        if c in Xdf.columns:
            Xdf = Xdf.drop(columns=[c])
    for c in (
        "sim_baseline_usd",
        "sim_vwap_stop_usd",
        "sim_atr2x_usd",
        "sim_fixed_rr_usd",
        "hold_hours",
    ):
        if c in Xdf.columns:
            Xdf = Xdf.drop(columns=[c])
    Xdf = Xdf.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if Xdf.shape[1] < 3:
        return None, "RF skipped (too few numeric feature columns).\n"

    m = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    m.fit(Xdf, y.fillna(0.0))
    imp = pd.Series(m.feature_importances_, index=Xdf.columns).sort_values(ascending=False).head(10)
    return imp, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--bars", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--open-ts-epoch", type=float, default=float(STRICT_EPOCH_START))
    ap.add_argument("--max-rows", type=int, default=0, help="Cap cohort rows (0=all)")
    args = ap.parse_args()
    root = args.root.resolve()
    bars_path = args.bars or (root / "artifacts" / "market_data" / "alpaca_bars.jsonl")
    out_md = args.out or (root / "artifacts" / "ml" / "OMNIBUS_REPORT.md")

    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("ERROR: pandas and numpy required.", file=sys.stderr)
        return 1

    dcm = _load_dcm()
    print("Loading 1m OHLCV bars...", flush=True)
    bars = dcm.load_bars_ohlcv_jsonl(bars_path)
    print("Building entry indexes from unified events...", flush=True)
    entry_by_tid, entry_by_ct, entry_by_tk = dcm.build_entry_indexes(root)

    cohort = load_strict_cohort_exit_rows(root, float(args.open_ts_epoch))
    if args.max_rows and args.max_rows > 0:
        cohort = cohort[: int(args.max_rows)]

    rows_out: List[Dict[str, Any]] = []
    for rec in cohort:
        row = dcm.cohort_row(rec, entry_by_tid, entry_by_ct, entry_by_tk, bars)
        if row is None:
            continue
        et = dcm.parse_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
        if et is None and rec.get("trade_id"):
            m = getattr(dcm, "_TID_ENTRY_TS", None)
            if m:
                mm = m.match(str(rec.get("trade_id") or "").strip())
                if mm:
                    et = dcm.parse_ts(mm.group(1))
        sym = str(rec.get("symbol") or "").upper()
        side = rec.get("side") or rec.get("position_side") or "long"
        exit_ts = dcm.parse_ts(rec.get("exit_ts") or rec.get("timestamp"))
        snap = rec.get("snapshot") if isinstance(rec.get("snapshot"), dict) else {}
        ep = dcm._safe_float(rec.get("entry_price")) or dcm._safe_float(snap.get("entry_price"))
        xp = dcm._safe_float(rec.get("exit_price")) or dcm._safe_float(snap.get("exit_price"))
        qty = dcm._safe_float(rec.get("qty")) or dcm._safe_float(snap.get("qty"))
        if et is None:
            row["entry_bucket_et"] = "unknown_entry_ts"
            row["spy_leading_15m_ret"] = None
            row["spy_macro_bucket"] = "unknown"
            row["sim_fixed_rr_usd"] = None
            rows_out.append(row)
            continue
        row["entry_bucket_et"] = entry_bucket_et(et)
        spy = bars.get("SPY") or []
        r15 = spy_return_leading(spy, et, 15)
        row["spy_leading_15m_ret"] = r15
        row["spy_macro_bucket"] = spy_tailwind_label(r15)
        if ep is not None and xp is not None and qty is not None and exit_ts is not None:
            row["sim_fixed_rr_usd"] = simulate_fixed_rr_usd(
                dcm, sym, side, et, exit_ts, float(ep), float(xp), float(qty), bars.get(sym) or []
            )
        else:
            row["sim_fixed_rr_usd"] = None
        rows_out.append(row)

    if len(rows_out) < 1:
        print("ERROR: zero cohort rows after bar+unified join (check exit_attribution, bars, epoch).", file=sys.stderr)
        return 1

    df = pd.DataFrame(rows_out)
    # --- Exit matrix ---
    exit_cols = ["realized_pnl_usd", "sim_vwap_stop_usd", "sim_atr2x_usd", "sim_fixed_rr_usd"]
    em = []
    for c, label in zip(exit_cols, ["Actual (realized)", "VWAP cross", "2x ATR trail", "Fixed 1:2 (0.5% SL / 1% TP)"]):
        s = df[c].dropna() if c in df.columns else pd.Series(dtype=float)
        em.append(
            {
                "strategy": label,
                "n": int(s.shape[0]),
                "total_pnl_usd": round(float(s.sum()), 2),
                "mean_pnl_usd": round(float(s.mean()), 4) if len(s) else None,
                "median_pnl_usd": round(float(s.median()), 4) if len(s) else None,
            }
        )
    exit_matrix = pd.DataFrame(em)

    # --- Seasonality ---
    if "entry_bucket_et" in df.columns:
        sea = (
            df.groupby("entry_bucket_et", dropna=False)["realized_pnl_usd"]
            .agg(n="count", total_usd="sum", mean_usd="mean")
            .reset_index()
            .sort_values("mean_usd")
        )
    else:
        sea = pd.DataFrame()

    # --- Macro ---
    if "spy_macro_bucket" in df.columns:
        macro = (
            df.groupby("spy_macro_bucket", dropna=False)["realized_pnl_usd"]
            .agg(n="count", total_usd="sum", mean_usd="mean")
            .reset_index()
        )
    else:
        macro = pd.DataFrame()

    # --- RF ---
    rf_note = ""
    top10 = None
    rf_target = ""
    if "realized_pnl_bps" in df.columns:
        rf_target = "realized_pnl_bps"
        top10, rf_note = run_rf_top10(df, rf_target)
    if top10 is None and "realized_pnl_usd" in df.columns:
        rf_target = "realized_pnl_usd"
        top10, rf_note = run_rf_top10(df, rf_target)

    out_md.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Omnibus Discovery Lab",
        "",
        f"- **Root:** `{root}`",
        f"- **Cohort rows:** {len(df)} (strict gate when available, else harvester-era floor)",
        f"- **Bars file:** `{bars_path}` (symbols loaded: {len(bars)})",
        f"- **Epoch floor:** `{args.open_ts_epoch}`",
        "",
        "## 1. Dynamic exits & R:R matrix (USD)",
        "",
        "Simulated exits use session 1m bars from RTH open through actual exit time (see `deep_correlation_matrix.simulate_dynamic_exits` for VWAP/ATR). "
        "Fixed R:R uses first-touch on 1m highs/lows with same-bar TP+SL → SL first.",
        "",
        _md_table(exit_matrix, floatfmt=".2f"),
        "",
        "## 2. Time-of-day seasonality (actual realized PnL by entry bucket, ET)",
        "",
        _md_table(sea, floatfmt=".4f") if not sea.empty else "_No bucket data._\n",
        "",
        "## 3. Macro drag — SPY 15m return into entry vs PnL",
        "",
        "SPY return: last 1m close at or before `entry - 15m` vs last close at or before `entry`. "
        "Labels: tailwind > +5 bps, headwind < −5 bps, else neutral.",
        "",
        _md_table(macro, floatfmt=".4f") if not macro.empty else "_No macro bucket data._\n",
        "",
        "## 4. Non-linear feature importance (RandomForest, top 10)",
        "",
        (
            f"Regressor target: `{rf_target}`. Excluded from **X**: target, sibling PnL column, all `sim_*`, "
            f"`hold_hours` (post-trade / anti-leakage)."
            if rf_target
            else "_No RF target column._"
        ),
        "",
        rf_note if rf_note else "",
    ]
    if top10 is not None:
        tdf = top10.reset_index()
        tdf.columns = ["feature", "importance"]
        lines.append(_md_table(tdf, floatfmt=".5f"))
    else:
        lines.append("_Feature importance not available._\n")

    lines.extend(
        [
            "",
            "## 5. Quick interpretation (automated heuristics)",
            "",
        ]
    )
    # Heuristic bullets
    bullets: List[str] = []
    if not exit_matrix.empty:
        best = exit_matrix.loc[exit_matrix["total_pnl_usd"].idxmax()]
        worst = exit_matrix.loc[exit_matrix["total_pnl_usd"].idxmin()]
        bullets.append(
            f"- **Best total-PnL exit style:** {best['strategy']} (total {best['total_pnl_usd']} USD across n={best['n']})."
        )
        bullets.append(
            f"- **Weakest total-PnL exit style:** {worst['strategy']} (total {worst['total_pnl_usd']} USD)."
        )
    if not sea.empty and "entry_bucket_et" in sea.columns:
        worst_bucket = sea.sort_values("mean_usd").iloc[0]
        best_bucket = sea.sort_values("mean_usd").iloc[-1]
        bullets.append(
            f"- **Mean PnL by entry hour:** worst `{worst_bucket['entry_bucket_et']}` "
            f"(mean {worst_bucket['mean_usd']:.4f} USD/trade); best `{best_bucket['entry_bucket_et']}` "
            f"(mean {best_bucket['mean_usd']:.4f})."
        )
    if not macro.empty and "spy_macro_bucket" in macro.columns:
        tw = macro[macro["spy_macro_bucket"] == "spy_tailwind"]
        hw = macro[macro["spy_macro_bucket"] == "spy_headwind"]
        if not tw.empty and not hw.empty:
            bullets.append(
                f"- **SPY tailwind vs headwind mean PnL:** "
                f"{float(tw['mean_usd'].iloc[0]):.4f} vs {float(hw['mean_usd'].iloc[0]):.4f} USD/trade."
            )
    if top10 is not None and len(top10):
        bullets.append(f"- **Top RF feature:** `{top10.index[0]}` (importance {float(top10.iloc[0]):.5f}).")
    if not bullets:
        bullets.append("- _No automated bullets (insufficient data)._")
    lines.extend(bullets)

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
