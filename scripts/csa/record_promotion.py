#!/usr/bin/env python3
"""
CSA: Record a promotion for audit and daily-quota satisfaction.
Writes CSA_PROMOTION_RECORD_<date>.json for assert_daily_promotion.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Record promotion for CSA audit")
    ap.add_argument("--promotion", required=True, help="EXIT_AGGRESSION_PROMOTION_<date>.json")
    ap.add_argument("--reason", required=True, help="Human-readable reason (e.g. daily promotion quota)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.promotion)
    if not path.exists():
        print(f"Promotion file missing: {path}", file=sys.stderr)
        return 2

    prom = json.loads(path.read_text(encoding="utf-8"))

    out = {
        "date": prom.get("date"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "promotion_type": prom.get("promotion_type", "EXIT_AGGRESSION"),
        "reason": args.reason,
        "selected_parameter": prom.get("selected_parameter"),
        "mode": prom.get("mode"),
        "max_loss_usd": prom.get("max_loss_usd"),
        "duration_hours": prom.get("duration_hours"),
        "active_from": prom.get("active_from"),
        "active_until": prom.get("active_until"),
        "quota_satisfied": True,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Recorded:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
