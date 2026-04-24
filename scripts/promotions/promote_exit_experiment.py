#!/usr/bin/env python3
"""
Promote selected exit experiment to paper: apply with max-loss and duration caps.
Mode: paper only. Reversible. Entries and CI unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Promote exit experiment to paper")
    ap.add_argument("--selection", required=True, help="EXIT_AGGRESSION_SELECTION_<date>.json")
    ap.add_argument("--mode", default="paper", choices=["paper", "shadow"])
    ap.add_argument("--max-loss-usd", type=float, default=25.0)
    ap.add_argument("--duration-hours", type=float, default=48.0)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.selection)
    if not path.exists():
        print(f"Selection missing: {path}", file=sys.stderr)
        return 2

    sel = json.loads(path.read_text(encoding="utf-8"))
    selected = sel.get("selected", "")
    if not selected:
        print("No selected parameter in selection file", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=args.duration_hours)

    out = {
        "promotion_type": "EXIT_AGGRESSION",
        "selected_parameter": selected,
        "mode": args.mode,
        "max_loss_usd": args.max_loss_usd,
        "duration_hours": args.duration_hours,
        "active_from": now.isoformat(),
        "active_until": end.isoformat(),
        "constraints": ["entries_unchanged", "ci_unchanged", "paper_only", "reversible"],
        "date": sel.get("date"),
        "notes": ["First profit-seeking promotion; daily quota. Activate in paper immediately."],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Promotion written:", out_path, "parameter:", selected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
