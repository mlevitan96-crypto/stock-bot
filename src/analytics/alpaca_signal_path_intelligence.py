"""
Alpaca Signal Path Intelligence (SPI) — read-only executed-trade path analytics.

Governance contract: see MEMORY_BANK_ALPACA.md (Alpaca Signal Path Intelligence). SPI is
evidence-only; it does not authorize behavior change, signals, exits, or risk.
"""

from __future__ import annotations

import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Default profit thresholds as fractional moves (0.005 = +0.5%).
DEFAULT_PROFIT_THRESHOLDS_FRAC: Tuple[float, ...] = (0.005, 0.01, 0.02)


def _parse_ts_iso(val: Any) -> Optional[datetime]:
    if not val:
        return None
    try:
        s = str(val).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _is_long_side(side: str) -> bool:
    s = (side or "long").lower()
    return s not in ("short", "sell")


def dominant_attribution_signal(exit_row: dict) -> str:
    """
    Best-effort dominant signal bucket from exit attribution (read-only).
    Uses exit_contributions / v2_exit_components when present; else attribution_unknown.
    """
    ec = exit_row.get("exit_contributions")
    if isinstance(ec, dict) and ec:
        best = max(ec.items(), key=lambda kv: abs(float(kv[1]) if isinstance(kv[1], (int, float)) else 0.0))
        return str(best[0]) if best[0] else "attribution_unknown"
    v2 = exit_row.get("v2_exit_components")
    if isinstance(v2, dict) and v2:
        best = max(v2.items(), key=lambda kv: abs(float(kv[1]) if isinstance(kv[1], (int, float)) else 0.0))
        return str(best[0]) if best[0] else "attribution_unknown"
    sigs = exit_row.get("signals")
    if isinstance(sigs, list) and sigs:
        for item in sigs:
            if isinstance(item, dict) and item.get("signal_id"):
                return str(item.get("signal_id"))
            if isinstance(item, str) and item:
                return item
    return "attribution_unknown"


def _bars_window(
    symbol: str,
    entry_dt: datetime,
    exit_dt: datetime,
    *,
    fetch_if_missing: bool,
) -> Tuple[List[dict], str]:
    """Load 1Min bars covering [entry, exit]; returns (bars, source_note)."""
    if not symbol or symbol == "?":
        return [], "no_symbol"
    date_str = entry_dt.strftime("%Y-%m-%d")
    try:
        from data.bars_loader import load_bars
    except Exception:
        return [], "bars_loader_import_failed"

    pad_start = entry_dt
    pad_end = exit_dt
    if pad_end < pad_start:
        pad_end = pad_start
    bars = load_bars(
        symbol,
        date_str,
        timeframe="1Min",
        start_ts=pad_start,
        end_ts=pad_end,
        use_cache=True,
        fetch_if_missing=fetch_if_missing,
    )
    if bars:
        return bars, "bars_cache_or_fetch"
    return [], "no_bars_cache"


def _baseline_bars(
    symbol: str,
    entry_dt: datetime,
    duration_seconds: float,
    *,
    fetch_if_missing: bool,
) -> List[dict]:
    """Pre-entry window of ~same length as hold (same ET session day as entry)."""
    if duration_seconds <= 0:
        return []
    start_dt = datetime.fromtimestamp(
        entry_dt.timestamp() - duration_seconds, tz=timezone.utc
    )
    date_str = entry_dt.strftime("%Y-%m-%d")
    try:
        from data.bars_loader import load_bars
    except Exception:
        return []
    return load_bars(
        symbol,
        date_str,
        timeframe="1Min",
        start_ts=start_dt,
        end_ts=entry_dt,
        use_cache=True,
        fetch_if_missing=fetch_if_missing,
    )


def _bar_ts(b: dict) -> Optional[datetime]:
    return _parse_ts_iso(b.get("t") or b.get("timestamp"))


def _iter_hold_bars(bars: List[dict], entry_dt: datetime, exit_dt: datetime) -> List[dict]:
    hold: List[dict] = []
    for b in bars:
        dt = _bar_ts(b)
        if dt and entry_dt <= dt <= exit_dt:
            hold.append(b)
    return sorted(hold, key=lambda x: _bar_ts(x) or entry_dt)


def time_to_fractional_move_minutes(
    hold_bars: List[dict],
    entry_price: float,
    entry_dt: datetime,
    exit_dt: datetime,
    target_frac: float,
    *,
    long_side: bool,
) -> Optional[float]:
    """Minutes from entry to first bar where favorable move >= target_frac; None if never."""
    if entry_price <= 0 or not hold_bars:
        return None
    for b in hold_bars:
        dt = _bar_ts(b)
        if not dt or dt < entry_dt:
            continue
        h = float(b.get("h") or b.get("high") or 0)
        l = float(b.get("l") or b.get("low") or 0)
        if long_side:
            move = (h - entry_price) / entry_price
        else:
            move = (entry_price - l) / entry_price
        if move >= target_frac:
            return max(0.0, (dt - entry_dt).total_seconds() / 60.0)
    return None


def path_mae_mfe_pct(
    hold_bars: List[dict],
    entry_price: float,
    entry_dt: datetime,
    exit_dt: datetime,
    *,
    long_side: bool,
) -> Tuple[Optional[float], Optional[float]]:
    """MAE/MFE over hold window as % of entry (unsigned adverse / favorable excursion)."""
    if entry_price <= 0 or not hold_bars:
        return None, None
    mae_px = 0.0
    mfe_px = 0.0
    any_bar = False
    for b in hold_bars:
        dt = _bar_ts(b)
        if not dt or dt < entry_dt or dt > exit_dt:
            continue
        any_bar = True
        h = float(b.get("h") or b.get("high") or 0)
        l = float(b.get("l") or b.get("low") or 0)
        if long_side:
            mfe_px = max(mfe_px, h - entry_price)
            mae_px = max(mae_px, entry_price - l)
        else:
            mfe_px = max(mfe_px, entry_price - l)
            mae_px = max(mae_px, h - entry_price)
    if not any_bar:
        return None, None
    return round(100.0 * mae_px / entry_price, 6), round(100.0 * mfe_px / entry_price, 6)


def mae_pct_until_first_threshold(
    hold_bars: List[dict],
    entry_price: float,
    entry_dt: datetime,
    exit_dt: datetime,
    target_frac: float,
    *,
    long_side: bool,
) -> Optional[float]:
    """Max adverse excursion from entry until first favorable hit of target_frac (or exit if never)."""
    if entry_price <= 0 or not hold_bars:
        return None
    mae_px = 0.0
    for b in hold_bars:
        dt = _bar_ts(b)
        if not dt or dt < entry_dt:
            continue
        if dt > exit_dt:
            break
        h = float(b.get("h") or b.get("high") or 0)
        l = float(b.get("l") or b.get("low") or 0)
        if long_side:
            mae_px = max(mae_px, entry_price - l)
            move = (h - entry_price) / entry_price
        else:
            mae_px = max(mae_px, h - entry_price)
            move = (entry_price - l) / entry_price
        if move >= target_frac:
            return round(100.0 * mae_px / entry_price, 6)
    return round(100.0 * mae_px / entry_price, 6)


def realized_vol_log_returns(bars: List[dict]) -> Optional[float]:
    """Population std of log(close_t/close_{t-1}) on consecutive closes; None if insufficient."""
    closes: List[float] = []
    for b in sorted(bars, key=lambda x: _bar_ts(x) or datetime.min.replace(tzinfo=timezone.utc)):
        c = float(b.get("c") or b.get("close") or 0)
        if c > 0:
            closes.append(c)
    if len(closes) < 3:
        return None
    lr: List[float] = []
    for i in range(1, len(closes)):
        lr.append(math.log(closes[i] / closes[i - 1]))
    if len(lr) < 2:
        return None
    mean = sum(lr) / len(lr)
    var = sum((x - mean) ** 2 for x in lr) / max(1, (len(lr) - 1))
    return math.sqrt(var) if var > 0 else 0.0


def classify_path_archetype(
    mae_pct: Optional[float],
    mfe_pct: Optional[float],
    pnl_pct: Optional[float],
    time_to_first_threshold_min: Optional[float],
    hold_minutes: float,
) -> str:
    """
    Descriptive buckets only — not predictive labels.
    """
    mae = mae_pct if mae_pct is not None else 0.0
    mfe = mfe_pct if mfe_pct is not None else 0.0
    pnl = pnl_pct if pnl_pct is not None else 0.0
    hm = max(hold_minutes, 1e-6)
    early = time_to_first_threshold_min is not None and time_to_first_threshold_min < hm * 0.25

    if mfe < 0.15 and mae < 0.15:
        return "grind_flat"
    if mae > 0.6 and mfe > mae * 1.15 and pnl > 0:
        return "dip_then_recover"
    if early and mfe >= 0.8 and mae > mfe * 0.45:
        return "spike_then_chop"
    if mae > 0.5 and mfe < 0.35:
        return "immediate_rejection"
    if mfe > 0.4 and mae < mfe * 0.35 and pnl > 0:
        return "trend_hold"
    return "other_mixed"


def _percentile_sorted(sorted_vals: List[float], p: float) -> Optional[float]:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = min(len(sorted_vals) - 1, max(0, int(round(p * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def summarize_numeric(values: List[float]) -> Dict[str, Any]:
    s = sorted(x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x)))
    if not s:
        return {"n": 0}
    return {
        "n": len(s),
        "min": s[0],
        "p25": _percentile_sorted(s, 0.25),
        "p50": _percentile_sorted(s, 0.5),
        "p75": _percentile_sorted(s, 0.75),
        "max": s[-1],
    }


def compute_trade_spi_row(
    exit_row: dict,
    repo_root: Path,
    *,
    profit_thresholds_frac: Sequence[float] = DEFAULT_PROFIT_THRESHOLDS_FRAC,
    fetch_if_missing: bool = False,
) -> Dict[str, Any]:
    tid = str(exit_row.get("trade_id") or "")
    sym = str(exit_row.get("symbol") or "").upper()
    side = str(exit_row.get("side") or exit_row.get("direction") or "long")
    long_side = _is_long_side(side)
    entry_dt = _parse_ts_iso(exit_row.get("entry_timestamp"))
    exit_dt = _parse_ts_iso(exit_row.get("timestamp"))
    entry_price = float(exit_row.get("entry_price") or 0)
    exit_price = float(exit_row.get("exit_price") or 0)
    pnl_pct = exit_row.get("pnl_pct")
    try:
        pnl_pct_f = float(pnl_pct) if pnl_pct is not None else None
    except (TypeError, ValueError):
        pnl_pct_f = None

    snap = exit_row.get("snapshot") if isinstance(exit_row.get("snapshot"), dict) else {}
    snap_mae = snap.get("mae_pct_so_far") or snap.get("mae_pct")
    snap_mfe = snap.get("mfe_pct_so_far") or snap.get("mfe_pct")

    signal_key = dominant_attribution_signal(exit_row)
    labels = {0.005: "to_plus_0_5pct_min", 0.01: "to_plus_1pct_min", 0.02: "to_plus_2pct_min"}
    empty_tmap: Dict[str, Optional[float]] = {}
    for th in profit_thresholds_frac:
        key = labels.get(th, f"to_plus_{int(th * 10000)}bp_min")
        empty_tmap[key] = None

    base: Dict[str, Any] = {
        "trade_id": tid,
        "symbol": sym,
        "signal_attribution_bucket": signal_key,
        "path_source": "attribution_only",
        "hold_minutes": None,
        "time_to_exit_minutes": None,
        "time_to_profit_frac_minutes": dict(empty_tmap),
        "mae_pct_hold": None,
        "mfe_pct_hold": None,
        "mae_pct_before_first_1pct": None,
        "vol_path": None,
        "vol_baseline": None,
        "vol_ratio_path_vs_baseline": None,
        "path_archetype": "unknown",
        "snapshot_mae_pct": float(snap_mae) if snap_mae is not None else None,
        "snapshot_mfe_pct": float(snap_mfe) if snap_mfe is not None else None,
        "pnl_pct_realized": pnl_pct_f,
    }

    if not entry_dt or not exit_dt or entry_price <= 0:
        base["path_source"] = "insufficient_timestamps_or_price"
        return base

    hold_sec = (exit_dt - entry_dt).total_seconds()
    hold_min = max(0.0, hold_sec / 60.0)
    base["hold_minutes"] = round(hold_min, 4)
    base["time_to_exit_minutes"] = round(hold_min, 4)

    bars, _note = _bars_window(sym, entry_dt, exit_dt, fetch_if_missing=fetch_if_missing)
    hold_bars = _iter_hold_bars(bars, entry_dt, exit_dt)

    if not hold_bars:
        # Fall back to snapshot-only path metrics when bars missing
        base["path_source"] = "attribution_snapshot_no_bars"
        if snap_mae is not None or snap_mfe is not None:
            try:
                mae_s = float(snap_mae) if snap_mae is not None else None
            except (TypeError, ValueError):
                mae_s = None
            try:
                mfe_s = float(snap_mfe) if snap_mfe is not None else None
            except (TypeError, ValueError):
                mfe_s = None
            base["path_archetype"] = classify_path_archetype(
                mae_s, mfe_s, pnl_pct_f, None, hold_min
            )
        else:
            base["path_archetype"] = "no_intraday_path_data"
        return base

    base["path_source"] = "ohlc_bars_hold_window"

    tmap: Dict[str, Optional[float]] = dict(empty_tmap)
    for th in profit_thresholds_frac:
        key = labels.get(th, f"to_plus_{int(th * 10000)}bp_min")
        tmap[key] = time_to_fractional_move_minutes(
            hold_bars, entry_price, entry_dt, exit_dt, th, long_side=long_side
        )
    base["time_to_profit_frac_minutes"] = tmap

    mae_h, mfe_h = path_mae_mfe_pct(hold_bars, entry_price, entry_dt, exit_dt, long_side=long_side)
    base["mae_pct_hold"] = mae_h
    base["mfe_pct_hold"] = mfe_h
    base["mae_pct_before_first_1pct"] = mae_pct_until_first_threshold(
        hold_bars, entry_price, entry_dt, exit_dt, 0.01, long_side=long_side
    )

    t_first = tmap.get("to_plus_1pct_min")
    base["path_archetype"] = classify_path_archetype(
        mae_h, mfe_h, pnl_pct_f, t_first, hold_min
    )

    v_path = realized_vol_log_returns(hold_bars)
    base["vol_path"] = v_path
    bl = _baseline_bars(sym, entry_dt, hold_sec, fetch_if_missing=fetch_if_missing)
    v_bl = realized_vol_log_returns(bl)
    base["vol_baseline"] = v_bl
    if v_path is not None and v_bl is not None and v_bl > 1e-12:
        base["vol_ratio_path_vs_baseline"] = round(v_path / v_bl, 6)
    return base


def aggregate_spi(trade_rows: List[dict]) -> Dict[str, Any]:
    by_sig: Dict[str, List[dict]] = defaultdict(list)
    for r in trade_rows:
        by_sig[str(r.get("signal_attribution_bucket") or "unknown")].append(r)

    per_signal: Dict[str, Any] = {}
    all_mae: List[float] = []
    all_hold: List[float] = []
    for sig, rows in sorted(by_sig.items(), key=lambda x: (-len(x[1]), x[0])):
        holds = [float(r["hold_minutes"]) for r in rows if r.get("hold_minutes") is not None]
        maes = [float(r["mae_pct_hold"]) for r in rows if r.get("mae_pct_hold") is not None]
        ratios = [
            float(r["vol_ratio_path_vs_baseline"])
            for r in rows
            if r.get("vol_ratio_path_vs_baseline") is not None
        ]
        t05 = [
            float(r["time_to_profit_frac_minutes"]["to_plus_0_5pct_min"])
            for r in rows
            if isinstance(r.get("time_to_profit_frac_minutes"), dict)
            and r["time_to_profit_frac_minutes"].get("to_plus_0_5pct_min") is not None
        ]
        arch = Counter(str(r.get("path_archetype") or "") for r in rows)
        per_signal[sig] = {
            "trade_count": len(rows),
            "hold_minutes": summarize_numeric(holds),
            "mae_pct_hold": summarize_numeric(maes),
            "vol_ratio_path_vs_baseline": summarize_numeric(ratios),
            "time_to_plus_0_5pct_min": summarize_numeric(t05),
            "path_archetype_counts": dict(arch),
        }
        all_mae.extend(maes)
        all_hold.extend(holds)

    # Descriptive "anomalies" — not alerts, not gating
    anomalies: List[dict] = []
    for r in trade_rows:
        mae = r.get("mae_pct_hold")
        if mae is not None and float(mae) >= 2.5:
            anomalies.append(
                {
                    "kind": "high_intrahold_mae_pct",
                    "trade_id": r.get("trade_id"),
                    "symbol": r.get("symbol"),
                    "signal_attribution_bucket": r.get("signal_attribution_bucket"),
                    "mae_pct_hold": mae,
                    "path_archetype": r.get("path_archetype"),
                }
            )
    anomalies.sort(key=lambda x: float(x.get("mae_pct_hold") or 0), reverse=True)

    return {
        "per_signal": per_signal,
        "aggregate": {
            "trade_count": len(trade_rows),
            "mae_pct_hold": summarize_numeric(all_mae),
            "hold_minutes": summarize_numeric(all_hold),
        },
        "top_anomalies_descriptive": anomalies[:12],
        "disclaimer": (
            "Distributions and descriptive buckets only; not forecasts, targets, or recommendations. "
            "SPI does not authorize behavior change (MEMORY_BANK_ALPACA.md)."
        ),
    }


def build_spi_bundle(
    *,
    root: Path,
    repo_root: Path,
    complete_trade_ids: Sequence[str],
    exit_by_id: Dict[str, dict],
    ts: str,
    profit_thresholds_frac: Sequence[float] = DEFAULT_PROFIT_THRESHOLDS_FRAC,
) -> Dict[str, Any]:
    """
    Build full SPI JSON for a strict-complete cohort (same trade ids as PnL reconciliation).
    Never raises — returns error field on failure.
    """
    fetch = os.environ.get("ALPACA_SPI_FETCH_BARS", "").strip().lower() in ("1", "true", "yes")
    try:
        rows: List[dict] = []
        for tid in complete_trade_ids:
            ex = exit_by_id.get(str(tid))
            if not ex:
                continue
            rows.append(
                compute_trade_spi_row(
                    ex,
                    repo_root,
                    profit_thresholds_frac=profit_thresholds_frac,
                    fetch_if_missing=fetch,
                )
            )
        agg = aggregate_spi(rows)
        return {
            "spi_version": "1.0.0",
            "ts": ts,
            "cohort_trade_count": len(complete_trade_ids),
            "spi_trade_rows": len(rows),
            "profit_thresholds_fractional": list(profit_thresholds_frac),
            "fetch_bars_if_missing": fetch,
            "repo_root": str(repo_root),
            "trading_bot_root": str(root),
            "trade_rows": rows,
            "summary": agg,
        }
    except Exception as e:
        return {
            "spi_version": "1.0.0",
            "ts": ts,
            "error": str(e),
            "summary": {"disclaimer": "SPI build failed; non-blocking."},
        }
