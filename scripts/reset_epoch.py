#!/usr/bin/env python3
"""
Anchor a new post-epoch era for ML / Telegram milestones.

Writes ``state/epoch_state.json`` with ``epoch_start_ts`` (UTC epoch seconds),
resets ``post_epoch_terminal_exit_count`` and ``fired_milestones``.

Usage:
  python scripts/reset_epoch.py              # print current state, exit 0
  python scripts/reset_epoch.py --write      # anchor new epoch (now)
  python scripts/reset_epoch.py --write --epoch-label "monday-v1"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Reset post-epoch anchor (epoch_state.json).")
    ap.add_argument(
        "--write",
        action="store_true",
        help="Persist new epoch_start_ts=now and reset milestone counters.",
    )
    ap.add_argument("--epoch-label", default="", help="Optional human label stored in state file.")
    ap.add_argument("--epoch-start-ts", type=float, default=None, help="Optional fixed epoch (UTC epoch seconds).")
    args = ap.parse_args()

    from src.telemetry.epoch_manager import anchor_new_epoch, load_epoch_state

    cur = load_epoch_state()
    print(json.dumps(cur, indent=2, sort_keys=True))
    if not args.write:
        print("\n(No --write: dry run. Re-run with --write to anchor a new era.)", flush=True)
        return 0
    nxt = anchor_new_epoch(epoch_label=str(args.epoch_label or ""), epoch_start_ts=args.epoch_start_ts)
    print("\nWrote new epoch anchor:", flush=True)
    print(json.dumps(nxt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
