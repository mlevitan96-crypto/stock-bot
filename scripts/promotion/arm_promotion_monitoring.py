#!/usr/bin/env python3
"""
Arm monitoring and rollback rules for a paper promotion.
Writes PROMOTION_MONITORING_${CONFIG_ID}_${DATE}.json (watch metrics + rollback triggers).
No automatic actions; human or downstream automation consumes this.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Arm promotion monitoring and rollback spec.")
    parser.add_argument("--config-id", required=True, help="Promoted config_id.")
    parser.add_argument("--mode", default="paper", help="Mode (paper).")
    parser.add_argument(
        "--watch-metrics",
        nargs="+",
        default=["pnl", "drawdown", "trade_rate", "signal_contribution", "cluster_exposure"],
        help="Metrics to watch.",
    )
    parser.add_argument(
        "--rollback-on",
        nargs="+",
        default=["drawdown_breach", "pnl_regression"],
        help="Conditions that trigger rollback consideration.",
    )
    parser.add_argument("--output", required=True, help="Output PROMOTION_MONITORING_${CONFIG_ID}_${DATE}.json path.")
    args = parser.parse_args()

    monitoring = {
        "config_id": args.config_id,
        "mode": args.mode,
        "armed_at": datetime.now(timezone.utc).isoformat(),
        "watch_metrics": args.watch_metrics,
        "rollback_on": args.rollback_on,
        "scope": "paper_only",
        "instruction": "Human or automation: evaluate watch_metrics; on rollback_on trigger, consider reverting GOVERNED_TUNING_CONFIG and restart.",
    }

    root = Path(os.getcwd())
    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(monitoring, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
