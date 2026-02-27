#!/usr/bin/env python3
"""
Generate summary.md and metrics.json (and trades.csv if missing) from backtest run dir.
Accepts --dir (single run dir) or --dirs (glob, e.g. reports/backtests/<RUN_ID>/*) and --out (summary output dir).
Writes summary.md and metrics.json under --out; also writes baseline/metrics.json when baseline exists.
Usage: python scripts/generate_backtest_summary.py --dir reports/backtests/<RUN_ID>
       python scripts/generate_backtest_summary.py --dirs reports/backtests/<RUN_ID>/* --out reports/backtests/<RUN_ID>/summary
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="Backtest run dir (e.g. reports/backtests/alpaca_backtest_<ts>)")
    ap.add_argument("--dirs", default=None, help="Glob of dirs (e.g. reports/backtests/<RUN_ID>/*); run dir = parent of first with baseline/)")
    ap.add_argument("--out", default=None, help="Output dir for summary.md and metrics.json (e.g. reports/backtests/<RUN_ID>/summary)")
    args = ap.parse_args()
    if args.dirs:
        pattern = args.dirs
        if not Path(pattern).is_absolute():
            pattern = str(REPO / pattern)
        expanded = sorted(glob.glob(pattern))
        if not expanded:
            base = REPO / Path(args.dirs.replace("*", "").rstrip("/").strip("/"))
        else:
            base = Path(expanded[0]).parent
            if not base.is_absolute():
                base = REPO / base
    else:
        base = Path(args.dir)
        if not base.is_absolute():
            base = REPO / base
    out = Path(args.out) if args.out else base
    if not out.is_absolute():
        out = REPO / out
    out.mkdir(parents=True, exist_ok=True)

    baseline = base / "baseline"
    summary_json = baseline / "backtest_summary.json"
    trades_jsonl = baseline / "backtest_trades.jsonl"
    metrics_out = out / "metrics.json"
    trades_csv = out / "trades.csv"
    summary_md = out / "summary.md"

    # metrics.json from baseline/backtest_summary.json
    if summary_json.exists():
        try:
            d = json.loads(summary_json.read_text(encoding="utf-8"))
            metrics = {
                "net_pnl": d.get("total_pnl_usd"),
                "gate_p10": None,
                "gate_p50": None,
                "gate_p90": None,
                "trades_count": d.get("trades_count"),
                "win_rate_pct": d.get("win_rate_pct"),
                "winning_trades": d.get("winning_trades"),
                "losing_trades": d.get("losing_trades"),
                "window_start": d.get("window_start"),
                "window_end": d.get("window_end"),
            }
            metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        except Exception:
            metrics_out.write_text(json.dumps({"error": "failed to read baseline summary"}, indent=2), encoding="utf-8")
    else:
        metrics_out.write_text(json.dumps({"error": "no baseline backtest_summary.json"}, indent=2), encoding="utf-8")

    # Also write baseline/metrics.json for contract (key metrics)
    baseline_metrics = base / "baseline" / "metrics.json"
    if summary_json.exists() and metrics_out.exists():
        try:
            baseline_metrics.write_text(metrics_out.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass

    # trades.csv from baseline/backtest_trades.jsonl (write to out)
    if trades_jsonl.exists() and not trades_csv.exists():
        try:
            rows = []
            for line in trades_jsonl.read_text(encoding="utf-8", errors="replace").strip().splitlines():
                if not line.strip():
                    continue
                rows.append(json.loads(line))
            if rows:
                keys = list(rows[0].keys()) if rows else []
                with trades_csv.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                    w.writeheader()
                    for r in rows:
                        w.writerow({k: (str(v) if not isinstance(v, (int, float, type(None))) else v) for k, v in r.items()})
        except Exception:
            pass

    # summary.md
    lines = [
        "# Backtest Run Summary",
        "",
        f"**Run dir:** `{base.name}`",
        "",
    ]
    if summary_json.exists():
        try:
            d = json.loads(summary_json.read_text(encoding="utf-8"))
            lines.extend([
                "## Baseline",
                "",
                f"- Trades: {d.get('trades_count', 0)}",
                f"- PnL (USD): {d.get('total_pnl_usd')}",
                f"- Win rate (%): {d.get('win_rate_pct')}",
                f"- Window: {d.get('window_start')} to {d.get('window_end')}",
                "",
            ])
        except Exception:
            pass
    lines.append("---")
    lines.append("*Generated by scripts/generate_backtest_summary.py*")
    summary_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {summary_md}, {metrics_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
