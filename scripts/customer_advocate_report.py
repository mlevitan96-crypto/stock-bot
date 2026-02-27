#!/usr/bin/env python3
"""Customer advocate: one report per run - what would help the customer make money?"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    run_dir = REPO / args.run_dir if not Path(args.run_dir).is_absolute() else Path(args.run_dir)
    out_path = (REPO / args.out if args.out else run_dir / "customer_advocate.md") if args.out else run_dir / "customer_advocate.md"
    if args.out and not Path(args.out).is_absolute():
        out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = {}
    if (run_dir / "baseline" / "metrics.json").exists():
        metrics = json.loads((run_dir / "baseline" / "metrics.json").read_text(encoding="utf-8"))
    score_rec = ""
    if (run_dir / "score_analysis" / "score_bands.json").exists():
        sa = json.loads((run_dir / "score_analysis" / "score_bands.json").read_text(encoding="utf-8"))
        score_rec = sa.get("recommendation") or ""

    net_pnl = metrics.get("net_pnl")
    win_rate = metrics.get("win_rate_pct")
    n = metrics.get("trades_count", 0)
    verdict = "Run not yet profitable." if (net_pnl is not None and net_pnl < 0) else "Run shows positive PnL."
    if n < 30:
        verdict = "Low trade count; get more trades then re-assess."
    levers = [score_rec] if score_rec else []
    if net_pnl is not None and net_pnl < 0 and win_rate is not None and win_rate < 50:
        levers.append("Improve entry (min_exec_score, weights) or exit timing.")
    md = ["# Customer advocate", "", "## Verdict", verdict, "", "## Metrics", f"Net PnL: {net_pnl}, Win rate: {win_rate}, Trades: {n}", "", "## Levers"] + ["- " + x for x in levers] + [""]
    out_path.write_text("\n".join(md), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
