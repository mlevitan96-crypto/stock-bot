#!/usr/bin/env python3
"""
Start live monitoring for the exit aggression experiment. Records metrics to track.
Output: EXIT_AGGRESSION_MONITOR_<date>.json (metrics list and last_updated).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Start exit experiment monitor")
    ap.add_argument("--mode", default="paper")
    ap.add_argument("--promotion", required=True, help="EXIT_AGGRESSION_PROMOTION_<date>.json")
    ap.add_argument("--metrics", nargs="+", default=["realized_pnl", "would_have_pnl", "exit_latency", "ci_interactions"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.promotion)
    if not path.exists():
        print(f"Promotion missing: {path}", file=sys.stderr)
        return 2

    prom = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)

    out = {
        "mode": args.mode,
        "promotion_type": prom.get("promotion_type"),
        "selected_parameter": prom.get("selected_parameter"),
        "metrics": {m: None for m in args.metrics},
        "last_updated": now.isoformat(),
        "active_from": prom.get("active_from"),
        "active_until": prom.get("active_until"),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Monitor started:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
