#!/usr/bin/env python3
"""
Run Molt workflow: orchestrator → sentinel → board → promotion discipline → memory evolution.
NO-APPLY. Produces artifacts only.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from moltbot import (
    run_learning_orchestrator,
    run_engineering_sentinel,
    run_learning_board,
    run_promotion_discipline,
    run_memory_evolution_proposal,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Molt workflow: date={date}")
    # Ensure unified daily intelligence pack exists
    try:
        from scripts.run_molt_intelligence_expansion import ensure_daily_pack
        ensure_daily_pack(base, date)
        print("  daily intelligence pack ensured")
    except Exception as e:
        print(f"  daily pack (optional): {e}")
    run_learning_orchestrator(date, base_dir=base)
    print("  learning_orchestrator done")
    run_engineering_sentinel(date, base_dir=base)
    print("  engineering_sentinel done")
    run_learning_board(date, base_dir=base)
    print("  learning_board done")
    run_promotion_discipline(date, base_dir=base)
    print("  promotion_discipline done")
    run_memory_evolution_proposal(date, base_dir=base)
    print("  memory_evolution done")
    print(f"Molt workflow complete. Reports in {base}/reports/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
