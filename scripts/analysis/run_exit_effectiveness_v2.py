#!/usr/bin/env python3
"""
Exit effectiveness report v2 — by exit_reason_code, regime, symbol bucket.

Outputs: reports/exit_review/exit_effectiveness_v2.json, exit_effectiveness_v2.md
Includes: avg/median pnl, tail loss, giveback distribution, saved_loss rate, left_money rate,
          time-in-trade distribution, pressure-at-exit (if in data).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import load_joined_closed_trades, load_from_backtest_dir


def _safe_float(x: any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _exit_timestamp(r: dict) -> str:
    ts = r.get("timestamp") or r.get("ts") or r.get("exit_timestamp") or r.get("entry_timestamp") or ""
    return str(ts) if isinstance(ts, (int, float)) else str(ts)


def build_exit_effectiveness_v2(joined: list[dict]) -> dict:
    by_reason: dict[str, list[dict]] = defaultdict(list)
    by_regime: dict[str, list[dict]] = defaultdict(list)
    for row in joined:
        reason = (row.get("exit_reason_code") or row.get("exit_reason") or "other").strip() or "other"
        regime = (row.get("entry_regime") or row.get("exit_regime") or "UNKNOWN")[:32]
        qm = row.get("exit_quality_metrics") or {}
        eff = qm.get("exit_efficiency") or {}
        rec = {
            "pnl": _safe_float(row.get("pnl")),
            "pnl_pct": _safe_float(row.get("pnl_pct")),
            "profit_giveback": qm.get("profit_giveback"),
            "saved_loss": eff.get("saved_loss"),
            "left_money": eff.get("left_money"),
            "mfe": qm.get("mfe"),
            "mae": qm.get("mae"),
            "time_in_trade_minutes": row.get("time_in_trade_minutes"),
            "pressure_at_exit": row.get("exit_pressure"),  # if logged
            "regime": regime,
            "symbol": row.get("symbol"),
        }
        by_reason[reason].append(rec)
        by_regime[regime].append(rec)

    total = len(joined)
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "joined_count": total,
        "by_exit_reason_code": {},
        "by_regime": {},
        "overall": {},
    }

    for reason, trades in by_reason.items():
        n = len(trades)
        pnls = [t["pnl"] for t in trades]
        pnls_sorted = sorted(pnls) if pnls else []
        median_pnl = pnls_sorted[n // 2] if pnls_sorted else None
        tail_95 = pnls_sorted[int(n * 0.05)] if n and len(pnls_sorted) > int(n * 0.05) else None
        givebacks = [t["profit_giveback"] for t in trades if t.get("profit_giveback") is not None]
        times = [t["time_in_trade_minutes"] for t in trades if t.get("time_in_trade_minutes") is not None]
        pressures = [t["pressure_at_exit"] for t in trades if t.get("pressure_at_exit") is not None]
        report["by_exit_reason_code"][reason] = {
            "frequency": n,
            "frequency_pct": round(100.0 * n / total, 2) if total else 0,
            "avg_pnl": round(sum(pnls) / n, 4) if pnls else None,
            "median_pnl": round(median_pnl, 4) if median_pnl is not None else None,
            "tail_loss_5pct": round(tail_95, 4) if tail_95 is not None else None,
            "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
            "saved_loss_rate": round(100.0 * sum(1 for t in trades if t.get("saved_loss")) / n, 2) if n else 0,
            "left_money_rate": round(100.0 * sum(1 for t in trades if t.get("left_money")) / n, 2) if n else 0,
            "avg_time_in_trade_min": round(sum(times) / len(times), 1) if times else None,
            "avg_pressure_at_exit": round(sum(pressures) / len(pressures), 4) if pressures else None,
        }

    for regime, trades in by_regime.items():
        n = len(trades)
        pnls = [t["pnl"] for t in trades]
        givebacks = [t["profit_giveback"] for t in trades if t.get("profit_giveback") is not None]
        report["by_regime"][regime] = {
            "count": n,
            "avg_pnl": round(sum(pnls) / n, 4) if pnls else None,
            "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
        }

    all_pnls = [r.get("pnl") for r in joined if r.get("pnl") is not None]
    all_gb = []
    for row in joined:
        gb = (row.get("exit_quality_metrics") or {}).get("profit_giveback")
        if gb is not None:
            all_gb.append(gb)
    report["overall"] = {
        "avg_pnl": round(sum(all_pnls) / len(all_pnls), 4) if all_pnls else None,
        "avg_profit_giveback": round(sum(all_gb) / len(all_gb), 4) if all_gb else None,
        "win_count": sum(1 for p in all_pnls if p > 0),
        "loss_count": sum(1 for p in all_pnls if p < 0),
    }
    return report


def write_md(out_path: Path, data: dict) -> None:
    lines = [
        "# Exit Effectiveness v2",
        "",
        f"Generated: {data.get('generated_utc', '')}",
        f"Joined trades: {data.get('joined_count', 0)}",
        "",
        "## By exit_reason_code",
        "",
        "| exit_reason_code | frequency | avg_pnl | median_pnl | tail_5% | avg_giveback | saved_loss% | left_money% |",
        "|------------------|-----------|---------|------------|---------|--------------|-------------|-------------|",
    ]
    for reason, v in sorted((data.get("by_exit_reason_code") or {}).items(), key=lambda x: -x[1].get("frequency", 0)):
        lines.append(
            f"| {reason} | {v.get('frequency')} | {v.get('avg_pnl')} | {v.get('median_pnl')} | {v.get('tail_loss_5pct')} | {v.get('avg_profit_giveback')} | {v.get('saved_loss_rate')} | {v.get('left_money_rate')} |"
        )
    lines.extend([
        "",
        "## By regime",
        "",
        "| regime | count | avg_pnl | avg_giveback |",
        "|--------|-------|---------|--------------|",
    ])
    for regime, v in sorted((data.get("by_regime") or {}).items(), key=lambda x: -x[1].get("count", 0)):
        lines.append(f"| {regime} | {v.get('count')} | {v.get('avg_pnl')} | {v.get('avg_profit_giveback')} |")
    lines.extend(["", "## Overall", "", f"- avg_pnl: {data.get('overall', {}).get('avg_pnl')}", f"- avg_profit_giveback: {data.get('overall', {}).get('avg_profit_giveback')}", f"- wins: {data.get('overall', {}).get('win_count')}", f"- losses: {data.get('overall', {}).get('loss_count')}", ""])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Exit effectiveness report v2")
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--end", type=str, default=None)
    ap.add_argument("--base-dir", type=Path, default=REPO)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--backtest-dir", type=Path, default=None)
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out_dir = args.out_dir or base / "reports" / "exit_review"
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.backtest_dir:
        joined = load_from_backtest_dir(args.backtest_dir.resolve())
    else:
        joined = load_joined_closed_trades(
            base / "logs" / "attribution.jsonl",
            base / "logs" / "exit_attribution.jsonl",
            start_date=args.start,
            end_date=args.end,
        )
    if not joined:
        empty = {"generated_utc": datetime.now(timezone.utc).isoformat(), "joined_count": 0, "by_exit_reason_code": {}, "by_regime": {}, "overall": {}}
        (out_dir / "exit_effectiveness_v2.json").write_text(json.dumps(empty, indent=2), encoding="utf-8")
        (out_dir / "exit_effectiveness_v2.md").write_text("# Exit Effectiveness v2\n\nNo data.\n", encoding="utf-8")
        print("No joined trades; wrote empty reports.", file=sys.stderr)
        return 0

    report = build_exit_effectiveness_v2(joined)
    (out_dir / "exit_effectiveness_v2.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_md(out_dir / "exit_effectiveness_v2.md", report)
    print(f"Wrote {out_dir / 'exit_effectiveness_v2.json'} and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
