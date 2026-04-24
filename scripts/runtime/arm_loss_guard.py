#!/usr/bin/env python3
"""
Arm loss and time guardrails for the exit experiment. On breach or expiry: revert.
Output: EXIT_AGGRESSION_GUARD_<date>.json for monitor and revert logic.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Arm loss guard for exit experiment")
    ap.add_argument("--mode", default="paper")
    ap.add_argument("--max-loss-usd", type=float, default=25.0)
    ap.add_argument("--duration-hours", type=float, default=48.0)
    ap.add_argument("--on-breach", default="revert", choices=["revert", "alert", "pause"])
    ap.add_argument("--on-expiry", default="revert", choices=["revert", "alert", "pause"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=args.duration_hours)

    out = {
        "mode": args.mode,
        "max_loss_usd": args.max_loss_usd,
        "duration_hours": args.duration_hours,
        "armed_at": now.isoformat(),
        "expires_at": expiry.isoformat(),
        "on_breach": args.on_breach,
        "on_expiry": args.on_expiry,
        "breach_triggered": False,
        "expiry_triggered": False,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Guard armed:", out_path, "max_loss=", args.max_loss_usd, "expiry=", expiry.isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main())
