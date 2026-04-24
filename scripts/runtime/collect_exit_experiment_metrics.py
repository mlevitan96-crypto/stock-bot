#!/usr/bin/env python3
"""
Collect metrics for the exit aggression experiment from promotion, monitor, and ledger.
Output: EXIT_AGGRESSION_RESULTS_<date>.json for CSA evaluation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect exit experiment metrics")
    ap.add_argument("--promotion", required=True)
    ap.add_argument("--monitor", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    paths = [Path(args.promotion), Path(args.monitor), Path(args.ledger)]
    for p in paths:
        if not p.exists():
            print(f"Missing: {p}", file=sys.stderr)
            return 2

    prom = json.loads(Path(args.promotion).read_text(encoding="utf-8"))
    mon = json.loads(Path(args.monitor).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))

    executed = ledger.get("executed", []) or []
    realized_pnl = sum(float(e.get("realized_pnl") or 0) for e in executed if isinstance(e, dict))
    metrics_from_monitor = mon.get("metrics", {}) or {}

    results = {
        "date": prom.get("date"),
        "promotion_type": prom.get("promotion_type"),
        "selected_parameter": prom.get("selected_parameter"),
        "realized_pnl": round(realized_pnl, 4),
        "would_have_pnl": metrics_from_monitor.get("would_have_pnl"),
        "exit_latency": metrics_from_monitor.get("exit_latency"),
        "tail_risk": None,
        "executed_count": len(executed),
        "blocked_count": len(ledger.get("blocked") or []),
        "metrics_source": "ledger_executed",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("Collected results:", out_path, "realized_pnl=", results["realized_pnl"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
