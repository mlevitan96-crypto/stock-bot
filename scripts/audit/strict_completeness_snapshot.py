#!/usr/bin/env python3
"""Emit key strict-completeness fields as JSON (SRE / droplet triage)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from telemetry.alpaca_strict_completeness_gate import evaluate_completeness  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--audit", action="store_true")
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help="UTC epoch floor for exit/cohort filtering (default: ET market open today).",
    )
    args = ap.parse_args()
    r = evaluate_completeness(
        args.root.resolve(),
        open_ts_epoch=args.open_ts_epoch,
        audit=args.audit,
    )
    keys = (
        "LEARNING_STATUS",
        "learning_fail_closed_reason",
        "trades_seen",
        "trades_complete",
        "trades_incomplete",
        "reason_histogram",
        "incomplete_examples",
    )
    sys.stdout.write(json.dumps({k: r.get(k) for k in keys}, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
