#!/usr/bin/env python3
"""
Phase 5 — Signal & Exit Effectiveness Analysis.

Generates:
1. Signal effectiveness report (per signal_id: trade_count, win_rate, avg_pnl, avg_MFE, avg_MAE, avg_profit_giveback)
2. Exit effectiveness report (per exit_reason_code: frequency, avg_pnl, avg_giveback, % saved_loss / left_money)
3. Entry vs exit blame report (for losers: % weak entry vs % exit timing, examples)
4. Counterfactual exit analysis (hold longer vs exit earlier)

Usage:
  python scripts/analysis/run_effectiveness_reports.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--base-dir PATH] [--out-dir PATH]
  python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/30d_xxx [--out-dir PATH]

Output: --out-dir (default reports/effectiveness_<date>) with JSON + CSV + MD.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import (
    load_joined_closed_trades,
    load_from_backtest_dir,
    load_jsonl,
)


def _safe_float(x: any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _safe_int(x: any, default: int = 0) -> int:
    try:
        return int(x) if x is not None else default
    except Exception:
        return default


# --- 1) Signal effectiveness ---
def build_signal_effectiveness(joined: list[dict]) -> dict:
    """Per signal_id (from entry attribution_components): trade_count, win_rate, avg_pnl, avg_MFE, avg_MAE, avg_profit_giveback."""
    by_signal: dict[str, list[dict]] = defaultdict(list)
    for row in joined:
        ac = row.get("entry_attribution_components") or []
        if not isinstance(ac, list):
            continue
        pnl = _safe_float(row.get("pnl"))
        pnl_pct = _safe_float(row.get("pnl_pct"))
        qm = row.get("exit_quality_metrics") or {}
        mfe = qm.get("mfe")
        mae = qm.get("mae")
        giveback = qm.get("profit_giveback")
        regime = (row.get("entry_regime") or row.get("exit_regime") or "UNKNOWN")[:32]
        ts = row.get("timestamp") or row.get("ts") or ""
        hour = str(ts)[11:13] if len(str(ts)) >= 13 else ""
        for c in ac:
            sid = c.get("signal_id") or c.get("name")
            if not sid:
                continue
            contrib = _safe_float(c.get("contribution_to_score"))
            by_signal[sid].append({
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "mfe": mfe,
                "mae": mae,
                "profit_giveback": giveback,
                "contribution": contrib,
                "regime": regime,
                "hour": hour,
                "symbol": row.get("symbol"),
            })
    report = {}
    for sid, trades in by_signal.items():
        n = len(trades)
        if n == 0:
            continue
        wins = sum(1 for t in trades if t["pnl"] > 0)
        pnls = [t["pnl"] for t in trades if t["pnl"] is not None]
        mfes = [t["mfe"] for t in trades if t["mfe"] is not None]
        maes = [t["mae"] for t in trades if t["mae"] is not None]
        givebacks = [t["profit_giveback"] for t in trades if t["profit_giveback"] is not None]
        by_regime: dict[str, list] = defaultdict(list)
        by_hour: dict[str, list] = defaultdict(list)
        for t in trades:
            if t.get("regime"):
                by_regime[t["regime"]].append(t["pnl"])
            if t.get("hour") != "":
                by_hour[t["hour"]].append(t["pnl"])
        report[sid] = {
            "signal_id": sid,
            "trade_count": n,
            "win_rate": round(wins / n, 4) if n else 0,
            "avg_pnl": round(sum(pnls) / n, 4) if pnls else None,
            "avg_pnl_pct": round(sum(t["pnl_pct"] for t in trades) / n, 4) if trades else None,
            "avg_MFE": round(sum(mfes) / len(mfes), 6) if mfes else None,
            "avg_MAE": round(sum(maes) / len(maes), 6) if maes else None,
            "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
            "breakdown_by_regime": {k: {"count": len(v), "avg_pnl": round(sum(v) / len(v), 4)} for k, v in by_regime.items() if v},
            "breakdown_by_hour": {k: {"count": len(v), "avg_pnl": round(sum(v) / len(v), 4)} for k, v in by_hour.items() if v},
        }
    return report


# --- 2) Exit effectiveness ---
def build_exit_effectiveness(joined: list[dict]) -> dict:
    """Per exit_reason_code and exit component: frequency, avg_realized_pnl, avg_profit_giveback, % saved_loss, % left_money."""
    by_reason: dict[str, list[dict]] = defaultdict(list)
    for row in joined:
        reason = (row.get("exit_reason_code") or row.get("exit_reason") or "other").strip() or "other"
        qm = row.get("exit_quality_metrics") or {}
        eff = qm.get("exit_efficiency") or {}
        by_reason[reason].append({
            "pnl": _safe_float(row.get("pnl")),
            "pnl_pct": _safe_float(row.get("pnl_pct")),
            "profit_giveback": qm.get("profit_giveback"),
            "post_exit_excursion": qm.get("post_exit_excursion"),
            "saved_loss": eff.get("saved_loss"),
            "left_money": eff.get("left_money"),
        })
    total = len(joined)
    report = {}
    for reason, trades in by_reason.items():
        n = len(trades)
        pnls = [t["pnl"] for t in trades]
        givebacks = [t["profit_giveback"] for t in trades if t["profit_giveback"] is not None]
        saved = sum(1 for t in trades if t.get("saved_loss"))
        left = sum(1 for t in trades if t.get("left_money"))
        post_exit = [t["post_exit_excursion"] for t in trades if t.get("post_exit_excursion") is not None]
        report[reason] = {
            "exit_reason_code": reason,
            "frequency": n,
            "frequency_pct": round(100.0 * n / total, 2) if total else 0,
            "avg_realized_pnl": round(sum(pnls) / n, 4) if pnls else None,
            "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
            "avg_post_exit_excursion": round(sum(post_exit) / len(post_exit), 6) if post_exit else None,
            "pct_saved_loss": round(100.0 * saved / n, 2) if n else 0,
            "pct_left_money": round(100.0 * left / n, 2) if n else 0,
        }
    return report


# --- 3) Entry vs exit blame (losers only) ---
def build_entry_vs_exit_blame(joined: list[dict]) -> dict:
    """For losing trades: % attributable to weak entry vs exit timing; examples. Includes unclassified_pct."""
    losers = [r for r in joined if _safe_float(r.get("pnl")) < 0]
    if not losers:
        return {
            "total_losing_trades": 0,
            "weak_entry_pct": 0,
            "exit_timing_pct": 0,
            "unclassified_pct": 0,
            "unclassified_count": 0,
            "examples": [],
        }
    entry_score_threshold = 3.0  # below = weak entry
    giveback_threshold = 0.3    # high giveback = exit timing cost
    weak_entry_idxs: set[int] = set()
    exit_timing_idxs: set[int] = set()
    for i, r in enumerate(losers):
        score = _safe_float(r.get("entry_score"), 0.0)
        qm = r.get("exit_quality_metrics") or {}
        giveback = qm.get("profit_giveback")
        mfe = qm.get("mfe")
        if score > 0 and score < entry_score_threshold:
            weak_entry_idxs.add(i)
        if giveback is not None and giveback >= giveback_threshold:
            exit_timing_idxs.add(i)
        if mfe is not None and mfe > 0 and _safe_float(r.get("pnl")) < 0:
            exit_timing_idxs.add(i)  # had upside but exited at loss
    n = len(losers)
    weak_pct = round(100.0 * len(weak_entry_idxs) / n, 2)
    timing_pct = round(100.0 * len(exit_timing_idxs) / n, 2)
    classified_idxs = weak_entry_idxs | exit_timing_idxs
    unclassified_count = n - len(classified_idxs)
    unclassified_pct = round(100.0 * unclassified_count / n, 2)
    exit_timing = [losers[i] for i in exit_timing_idxs]
    weak_entry = [losers[i] for i in weak_entry_idxs]
    examples_good_entry_bad_exit = [
        {"symbol": r.get("symbol"), "entry_score": r.get("entry_score"), "pnl": r.get("pnl"), "profit_giveback": (r.get("exit_quality_metrics") or {}).get("profit_giveback"), "exit_reason_code": r.get("exit_reason_code")}
        for r in exit_timing[:5]
    ]
    examples_bad_entry = [
        {"symbol": r.get("symbol"), "entry_score": r.get("entry_score"), "pnl": r.get("pnl"), "exit_reason_code": r.get("exit_reason_code")}
        for r in weak_entry[:5]
    ]
    return {
        "total_losing_trades": n,
        "weak_entry_count": len(weak_entry_idxs),
        "weak_entry_pct": weak_pct,
        "exit_timing_count": len(exit_timing_idxs),
        "exit_timing_pct": timing_pct,
        "unclassified_count": unclassified_count,
        "unclassified_pct": unclassified_pct,
        "examples_good_entry_bad_exit": examples_good_entry_bad_exit,
        "examples_bad_entry": examples_bad_entry,
    }


# --- 4) Counterfactual exit ---
def build_counterfactual_exit(joined: list[dict]) -> dict:
    """Trades where holding longer would have helped (high giveback); where earlier exit would have saved loss (high MAE, loss)."""
    hold_longer = []   # high profit_giveback, realized positive but left money
    exit_earlier = []  # loss + had MAE (adverse excursion)
    for r in joined:
        pnl = _safe_float(r.get("pnl"))
        qm = r.get("exit_quality_metrics") or {}
        giveback = qm.get("profit_giveback")
        mae = qm.get("mae")
        left_money = (qm.get("exit_efficiency") or {}).get("left_money")
        if giveback is not None and giveback >= 0.25 and (left_money or pnl > 0):
            hold_longer.append({
                "symbol": r.get("symbol"),
                "entry_timestamp": r.get("entry_timestamp"),
                "pnl": pnl,
                "profit_giveback": giveback,
                "mfe": qm.get("mfe"),
                "exit_reason_code": r.get("exit_reason_code"),
            })
        if pnl < 0 and mae is not None and mae > 0:
            exit_earlier.append({
                "symbol": r.get("symbol"),
                "entry_timestamp": r.get("entry_timestamp"),
                "pnl": pnl,
                "mae": mae,
                "exit_reason_code": r.get("exit_reason_code"),
            })
    return {
        "hold_longer_would_help_count": len(hold_longer),
        "hold_longer_examples": hold_longer[:10],
        "exit_earlier_would_save_count": len(exit_earlier),
        "exit_earlier_examples": exit_earlier[:10],
    }


def write_md_summary(out_dir: Path, signal_report: dict, exit_report: dict, blame_report: dict, counterfactual: dict, joined_count: int) -> None:
    md = out_dir / "EFFECTIVENESS_SUMMARY.md"
    lines = [
        "# Signal & Exit Effectiveness Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Closed trades (joined): {joined_count}",
        "",
        "## 1. Signal effectiveness (top 15 by trade count)",
        "",
        "| signal_id | trade_count | win_rate | avg_pnl | avg_MFE | avg_MAE | avg_giveback |",
        "|-----------|-------------|----------|---------|---------|---------|--------------|",
    ]
    sorted_signals = sorted(signal_report.items(), key=lambda x: -x[1].get("trade_count", 0))[:15]
    for sid, v in sorted_signals:
        tc = v.get("trade_count", 0)
        wr = v.get("win_rate")
        ap = v.get("avg_pnl")
        mfe = v.get("avg_MFE")
        mae = v.get("avg_MAE")
        gb = v.get("avg_profit_giveback")
        lines.append(f"| {sid} | {tc} | {wr} | {ap} | {mfe} | {mae} | {gb} |")
    lines.extend([
        "",
        "## 2. Exit effectiveness by exit_reason_code",
        "",
        "| exit_reason_code | frequency | avg_realized_pnl | avg_giveback | % saved_loss | % left_money |",
        "|------------------|-----------|------------------|--------------|--------------|---------------|",
    ])
    for reason, v in sorted(exit_report.items(), key=lambda x: -x[1].get("frequency", 0)):
        lines.append(f"| {reason} | {v.get('frequency')} | {v.get('avg_realized_pnl')} | {v.get('avg_profit_giveback')} | {v.get('pct_saved_loss')} | {v.get('pct_left_money')} |")
    # Overall aggregates (for gate comparison)
    wins = joined_count - blame_report.get("total_losing_trades", 0)
    overall_win_rate = round(wins / joined_count, 4) if joined_count else None
    givebacks = []
    for _reason, row in (exit_report.items() if isinstance(exit_report, dict) else []):
        if isinstance(row, dict) and row.get("avg_profit_giveback") is not None:
            freq = row.get("frequency", 0) or 0
            for _ in range(freq):
                givebacks.append(row["avg_profit_giveback"])
    overall_avg_giveback = round(sum(givebacks) / len(givebacks), 4) if givebacks else None
    lines_aggregates = [
        "",
        "## 0. Overall aggregates",
        "",
        f"- Overall win_rate: {overall_win_rate}",
        f"- Overall avg_profit_giveback (from exit reasons): {overall_avg_giveback}",
        "",
    ]
    lines.extend(lines_aggregates)
    lines.extend([
        "",
        "## 3. Entry vs exit blame (losing trades)",
        "",
        f"- Total losing trades: {blame_report.get('total_losing_trades', 0)}",
        f"- % weak entry (entry_score < 3): {blame_report.get('weak_entry_pct', 0)}",
        f"- % exit timing (high giveback / had MFE): {blame_report.get('exit_timing_pct', 0)}",
        f"- % unclassified (neither): {blame_report.get('unclassified_pct', 0)}",
        "",
        "## 4. Counterfactual exit",
        "",
        f"- Hold longer would have helped: {counterfactual.get('hold_longer_would_help_count', 0)} trades",
        f"- Exit earlier would have saved loss: {counterfactual.get('exit_earlier_would_save_count', 0)} trades",
        "",
    ])
    md.write_text("\n".join(lines), encoding="utf-8")


def _exit_timestamp(r: dict) -> str:
    """Sort key for joined records: exit timestamp (iso or numeric string)."""
    ts = r.get("timestamp") or r.get("ts") or r.get("exit_timestamp") or r.get("entry_timestamp") or ""
    if isinstance(ts, (int, float)):
        return str(ts)
    return str(ts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 5: Signal & exit effectiveness reports")
    ap.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo or log base")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: reports/effectiveness_<date>)")
    ap.add_argument("--backtest-dir", type=Path, default=None, help="Use backtest outputs instead of logs")
    ap.add_argument("--last-n", type=int, default=None, help="Use only the last N closed trades (by exit timestamp). For rolling effectiveness; ignored when --backtest-dir is set.")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = base / "reports" / f"effectiveness_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.backtest_dir:
        joined = load_from_backtest_dir(args.backtest_dir.resolve())
    else:
        attr_path = base / "logs" / "attribution.jsonl"
        exit_path = base / "logs" / "exit_attribution.jsonl"
        joined = load_joined_closed_trades(
            attr_path,
            exit_path,
            start_date=args.start,
            end_date=args.end,
        )
        if joined and args.last_n is not None and args.last_n > 0:
            joined = sorted(joined, key=_exit_timestamp)[-args.last_n:]
            print(f"Using last {len(joined)} closed trades (--last-n={args.last_n})", file=sys.stderr)

    if not joined:
        print("No joined closed trades found. Ensure logs/attribution.jsonl and logs/exit_attribution.jsonl exist and have matching entries.", file=sys.stderr)
        # Write empty reports so structure is clear
        for name, data in [
            ("signal_effectiveness", {}),
            ("exit_effectiveness", {}),
            ("entry_vs_exit_blame", {"total_losing_trades": 0}),
            ("counterfactual_exit", {}),
        ]:
            (out_dir / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        (out_dir / "EFFECTIVENESS_SUMMARY.md").write_text("# No data\n\nNo joined closed trades in range.\n", encoding="utf-8")
        return 0

    signal_report = build_signal_effectiveness(joined)
    exit_report = build_exit_effectiveness(joined)
    blame_report = build_entry_vs_exit_blame(joined)
    counterfactual = build_counterfactual_exit(joined)

    (out_dir / "signal_effectiveness.json").write_text(json.dumps(signal_report, indent=2), encoding="utf-8")
    (out_dir / "exit_effectiveness.json").write_text(json.dumps(exit_report, indent=2), encoding="utf-8")
    (out_dir / "entry_vs_exit_blame.json").write_text(json.dumps(blame_report, indent=2), encoding="utf-8")
    (out_dir / "counterfactual_exit.json").write_text(json.dumps(counterfactual, indent=2), encoding="utf-8")
    # Gate comparison: one-place aggregates + expectancy (for governance stopping condition)
    n_joined = len(joined)
    n_losers = blame_report.get("total_losing_trades", 0)
    agg_win_rate = round((n_joined - n_losers) / n_joined, 4) if n_joined else None
    gb_list = []
    for _r, v in (exit_report.items() if isinstance(exit_report, dict) else []):
        if isinstance(v, dict) and v.get("avg_profit_giveback") is not None:
            gb_list.extend([v["avg_profit_giveback"]] * (v.get("frequency", 0) or 0))
    agg_giveback = round(sum(gb_list) / len(gb_list), 4) if gb_list else None
    # Fallback: compute from joined rows' exit_quality_metrics.profit_giveback when no exit reason had giveback
    if agg_giveback is None:
        direct_gb = [
            (r.get("exit_quality_metrics") or {}).get("profit_giveback")
            for r in joined
            if (r.get("exit_quality_metrics") or {}).get("profit_giveback") is not None
        ]
        agg_giveback = round(sum(direct_gb) / len(direct_gb), 4) if direct_gb else None
    total_pnl = sum(_safe_float(r.get("pnl")) for r in joined)
    expectancy_per_trade = round(total_pnl / n_joined, 6) if n_joined else None
    (out_dir / "effectiveness_aggregates.json").write_text(
        json.dumps({
            "joined_count": n_joined,
            "total_losing_trades": n_losers,
            "win_rate": agg_win_rate,
            "avg_profit_giveback": agg_giveback,
            "total_pnl": round(total_pnl, 2),
            "expectancy_per_trade": expectancy_per_trade,
        }, indent=2),
        encoding="utf-8",
    )

    # CSV: signal effectiveness
    with (out_dir / "signal_effectiveness.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["signal_id", "trade_count", "win_rate", "avg_pnl", "avg_MFE", "avg_MAE", "avg_profit_giveback"])
        for sid, v in sorted(signal_report.items(), key=lambda x: -x[1].get("trade_count", 0)):
            w.writerow([sid, v.get("trade_count"), v.get("win_rate"), v.get("avg_pnl"), v.get("avg_MFE"), v.get("avg_MAE"), v.get("avg_profit_giveback")])

    # CSV: exit effectiveness
    with (out_dir / "exit_effectiveness.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["exit_reason_code", "frequency", "frequency_pct", "avg_realized_pnl", "avg_profit_giveback", "pct_saved_loss", "pct_left_money"])
        for reason, v in sorted(exit_report.items(), key=lambda x: -x[1].get("frequency", 0)):
            w.writerow([reason, v.get("frequency"), v.get("frequency_pct"), v.get("avg_realized_pnl"), v.get("avg_profit_giveback"), v.get("pct_saved_loss"), v.get("pct_left_money")])

    write_md_summary(out_dir, signal_report, exit_report, blame_report, counterfactual, len(joined))
    print(f"Wrote reports to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
