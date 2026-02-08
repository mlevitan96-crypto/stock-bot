#!/usr/bin/env python3
"""
Multi-Day Analysis Module — Board Upgrade V3.

Computes rolling 3-day, 5-day, 7-day windows for:
- Regime persistence and regime transition probability
- Volatility trend
- Sector rotation trend
- Attribution vs exit attribution trend
- Churn trend
- Hold-time trend
- Exit-reason distribution trend
- Blocked trade trend (displacement, max positions, capacity)
- Displacement sensitivity trend
- Capacity utilization trend
- Expectancy trend
- MAE/MFE trend

Outputs: board/eod/out/YYYY-MM-DD/multi_day_analysis.json and multi_day_analysis.md
Run after daily EOD pipeline. Path-agnostic.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _day_utc(ts: str) -> str:
    return str(ts)[:10] if ts else ""


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
            if isinstance(rec, dict):
                out.append(rec)
        except Exception:
            continue
    return out


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else (default or {})
    except Exception:
        return default if default is not None else {}


def _load_stockbot_day(base: Path, day: str) -> dict | None:
    """Load stockbot pack for a single day if it exists."""
    pack = base / "reports" / "stockbot" / day
    if not pack.exists():
        return None
    eod = _load_json(pack / "STOCK_EOD_SUMMARY.json", {})
    regime = _load_json(pack / "STOCK_REGIME_AND_UNIVERSE.json", {})
    prof = _load_json(pack / "STOCK_PROFITABILITY_DIAGNOSTICS.json", {})
    return {
        "date": day,
        "eod": eod,
        "regime": regime,
        "profitability": prof,
    }


def _load_attribution_window(base: Path, days: list[str]) -> list[dict]:
    """Load attribution records for a window of days."""
    raw = _iter_jsonl(base / "logs" / "attribution.jsonl")
    return [r for r in raw if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) in days]


def _load_exit_attribution_window(base: Path, days: list[str]) -> list[dict]:
    """Load exit attribution records for a window of days."""
    raw = _iter_jsonl(base / "logs" / "exit_attribution.jsonl")
    return [r for r in raw if _day_utc(str(r.get("ts") or r.get("timestamp") or r.get("exit_ts") or "")) in days]


def _load_blocked_window(base: Path, days: list[str]) -> list[dict]:
    """Load blocked trades for a window of days."""
    raw = _iter_jsonl(base / "state" / "blocked_trades.jsonl")
    return [r for r in raw if _day_utc(str(r.get("ts") or r.get("timestamp") or "")) in days]


def _compute_window(
    base: Path,
    window_days: list[str],
    window_size: int,
) -> dict:
    """Compute all metrics for a single rolling window."""
    stockbot_days = [_load_stockbot_day(base, d) for d in window_days]
    attr = _load_attribution_window(base, window_days)
    exit_attr = _load_exit_attribution_window(base, window_days)
    blocked = _load_blocked_window(base, window_days)

    # Regime persistence and transition
    regimes = []
    for s in stockbot_days:
        if s and s.get("regime"):
            r = s["regime"].get("regime") or s["regime"].get("regime_label") or "UNKNOWN"
            regimes.append(r)
    regime_counts = Counter(regimes)
    dominant_regime = regime_counts.most_common(1)[0][0] if regime_counts else "UNKNOWN"
    regime_stability = regime_counts.get(dominant_regime, 0) / len(regimes) if regimes else 0
    # Transition probability: days where regime differs from previous
    transitions = sum(1 for i in range(1, len(regimes)) if regimes[i] != regimes[i - 1])
    transition_prob = transitions / (len(regimes) - 1) if len(regimes) > 1 else 0

    # Volatility trend (from stockbot when available)
    vol_buckets = [s["regime"].get("volatility_bucket") for s in stockbot_days if s and s.get("regime")]
    vol_trend = "stable"
    if len(vol_buckets) >= 2 and vol_buckets[0] and vol_buckets[-1]:
        if vol_buckets[-1] != vol_buckets[0]:
            vol_trend = "rising" if vol_buckets[-1] and vol_buckets[0] and str(vol_buckets[-1]) > str(vol_buckets[0]) else "falling"

    # Sector rotation
    all_sectors: list[str] = []
    for s in stockbot_days:
        if s and s.get("regime"):
            sec = s["regime"].get("sectors") or []
            all_sectors.extend(sec if isinstance(sec, list) else [])
    sector_rotation = dict(Counter(all_sectors).most_common(5)) if all_sectors else {}

    # Attribution vs exit attribution
    attr_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or 0) for r in attr)
    exit_pnl = sum(float(r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl") or 0) for r in exit_attr)
    attr_vs_exit_delta = attr_pnl - exit_pnl
    attr_vs_exit_trend = "aligned" if abs(attr_vs_exit_delta) < 50 else ("attribution_higher" if attr_vs_exit_delta > 0 else "exit_higher")

    # Churn: trades per day
    trades_per_day = defaultdict(int)
    for r in attr:
        d = _day_utc(str(r.get("ts") or r.get("timestamp") or ""))
        if d in window_days:
            trades_per_day[d] += 1
    churn_trend = "stable"
    churn_vals = [trades_per_day[d] for d in window_days if d in trades_per_day]
    if len(churn_vals) >= 2:
        churn_trend = "rising" if churn_vals[-1] > churn_vals[0] else ("falling" if churn_vals[-1] < churn_vals[0] else "stable")

    # Hold-time trend
    hold_times: list[float] = []
    for r in exit_attr:
        ht = r.get("hold_time_seconds") or r.get("hold_seconds") or r.get("hold_time_hours")
        if ht is not None:
            hold_times.append(float(ht) if not isinstance(ht, (int, float)) or isinstance(ht, bool) else float(ht))
    entry_ts = None
    exit_ts = None
    for r in exit_attr:
        et = r.get("entry_ts") or r.get("entry_timestamp")
        xt = r.get("exit_ts") or r.get("ts") or r.get("timestamp")
        if et and xt:
            try:
                e = datetime.fromisoformat(str(et).replace("Z", "+00:00"))
                x = datetime.fromisoformat(str(xt).replace("Z", "+00:00"))
                hold_times.append((x - e).total_seconds())
            except (ValueError, TypeError):
                pass
    avg_hold = sum(hold_times) / len(hold_times) if hold_times else None
    hold_trend = "unknown"
    if len(hold_times) >= 4:
        mid = len(hold_times) // 2
        first_half_avg = sum(hold_times[:mid]) / mid
        second_half_avg = sum(hold_times[mid:]) / (len(hold_times) - mid)
        hold_trend = "rising" if second_half_avg > first_half_avg else ("falling" if second_half_avg < first_half_avg else "stable")

    # Exit-reason distribution
    exit_reasons: Counter[str] = Counter()
    for r in attr + exit_attr:
        reason = r.get("close_reason") or r.get("exit_reason") or r.get("reason") or "unknown"
        exit_reasons[reason] += 1
    exit_reason_dist = dict(exit_reasons.most_common(10))

    # Blocked trades: displacement, max positions, capacity
    blocked_displacement = sum(1 for r in blocked if "displacement" in str(r.get("reason") or r.get("blocked_reason") or "").lower())
    blocked_max_pos = sum(1 for r in blocked if "max_pos" in str(r.get("reason") or "").lower() or "capacity" in str(r.get("reason") or "").lower())
    blocked_capacity = sum(1 for r in blocked if "capacity" in str(r.get("reason") or "").lower())
    displacement_trend = "unknown"
    capacity_trend = "unknown"
    if len(window_days) >= 2:
        first_half = [d for d in window_days[: len(window_days) // 2]]
        second_half = [d for d in window_days[len(window_days) // 2 :]]
        b1 = _load_blocked_window(base, first_half)
        b2 = _load_blocked_window(base, second_half)
        d1 = sum(1 for r in b1 if "displacement" in str(r.get("reason") or "").lower())
        d2 = sum(1 for r in b2 if "displacement" in str(r.get("reason") or "").lower())
        displacement_trend = "rising" if d2 > d1 else ("falling" if d2 < d1 else "stable")
        c1 = sum(1 for r in b1 if "capacity" in str(r.get("reason") or "").lower() or "max_pos" in str(r.get("reason") or "").lower())
        c2 = sum(1 for r in b2 if "capacity" in str(r.get("reason") or "").lower() or "max_pos" in str(r.get("reason") or "").lower())
        capacity_trend = "rising" if c2 > c1 else ("falling" if c2 < c1 else "stable")

    # Expectancy trend
    exp_vals = []
    for s in stockbot_days:
        if s and s.get("profitability"):
            eq = s["profitability"].get("expectancy_per_strategy", {}).get("equity")
            if eq is not None:
                exp_vals.append(float(eq))
    expectancy_trend = "unknown"
    if len(exp_vals) >= 2:
        expectancy_trend = "rising" if exp_vals[-1] > exp_vals[0] else ("falling" if exp_vals[-1] < exp_vals[0] else "stable")
    total_trades = len(attr) or 1
    rolling_expectancy = (attr_pnl / total_trades) if total_trades else 0

    # MAE/MFE trend (from profitability when available)
    mae_mfe_trend = "unknown"
    for s in stockbot_days:
        if s and s.get("profitability") and s["profitability"].get("mae_mfe_distributions"):
            mae_mfe_trend = "available"
            break

    return {
        "window_size": window_size,
        "window_days": window_days,
        "regime": {
            "dominant_regime": dominant_regime,
            "regime_stability_score": round(regime_stability, 4),
            "regime_transition_probability": round(transition_prob, 4),
            "regime_distribution": dict(regime_counts),
        },
        "volatility_trend": vol_trend,
        "sector_rotation_trend": sector_rotation,
        "attribution_vs_exit": {
            "attribution_pnl": round(attr_pnl, 2),
            "exit_attribution_pnl": round(exit_pnl, 2),
            "delta": round(attr_vs_exit_delta, 2),
            "trend": attr_vs_exit_trend,
        },
        "churn_trend": churn_trend,
        "hold_time_trend": hold_trend,
        "avg_hold_time_seconds": round(avg_hold, 2) if avg_hold is not None else None,
        "exit_reason_distribution": exit_reason_dist,
        "blocked_trades": {
            "displacement_count": blocked_displacement,
            "max_positions_count": blocked_max_pos,
            "capacity_count": blocked_capacity,
            "displacement_trend": displacement_trend,
            "capacity_trend": capacity_trend,
        },
        "displacement_sensitivity_trend": displacement_trend,
        "capacity_utilization_trend": capacity_trend,
        "expectancy_trend": expectancy_trend,
        "rolling_expectancy_usd": round(rolling_expectancy, 2),
        "mae_mfe_trend": mae_mfe_trend,
        "total_trades": len(attr),
        "total_exits": len(exit_attr),
        "total_blocked": len(blocked),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-Day Analysis (Board V3)")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script parent)")
    args = ap.parse_args()
    target_date = args.date.strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = Path(args.base_dir) if args.base_dir else ROOT

    try:
        t = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date: {target_date}", file=sys.stderr)
        return 1

    windows = {}
    for w in [3, 5, 7]:
        start = t - timedelta(days=w - 1)
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(w)]
        windows[f"{w}_day"] = _compute_window(base, days, w)

    out_dir = base / "board" / "eod" / "out" / target_date
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "date": target_date,
        "multi_day_analysis": windows,
    }

    json_path = out_dir / "multi_day_analysis.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    md_lines = [
        f"# Multi-Day Analysis — {target_date}",
        "",
        "## Summary",
        "",
        f"Rolling windows: 3-day, 5-day, 7-day (ending {target_date}).",
        "",
    ]
    for wkey, wdata in windows.items():
        md_lines.append(f"## {wkey.replace('_', '-').title()} Window")
        md_lines.append("")
        md_lines.append(f"- **Dominant regime:** {wdata['regime']['dominant_regime']}")
        md_lines.append(f"- **Regime stability:** {wdata['regime']['regime_stability_score']:.2%}")
        md_lines.append(f"- **Regime transition probability:** {wdata['regime']['regime_transition_probability']:.2%}")
        md_lines.append(f"- **Volatility trend:** {wdata['volatility_trend']}")
        md_lines.append(f"- **Attribution vs exit:** {wdata['attribution_vs_exit']['trend']} (delta ${wdata['attribution_vs_exit']['delta']:.2f})")
        md_lines.append(f"- **Churn trend:** {wdata['churn_trend']}")
        md_lines.append(f"- **Hold-time trend:** {wdata['hold_time_trend']}")
        md_lines.append(f"- **Displacement trend:** {wdata['blocked_trades']['displacement_trend']}")
        md_lines.append(f"- **Expectancy trend:** {wdata['expectancy_trend']} (rolling ${wdata['rolling_expectancy_usd']:.2f})")
        md_lines.append("")
    md_path = out_dir / "multi_day_analysis.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Multi-day analysis written to {out_dir}")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
