#!/usr/bin/env python3
"""
CSA: Emit authoritative contract for true replay — required fields and timestamp requirements.
Used by patch plan and backfill. No live impact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit true replay contract")
    ap.add_argument("--required", nargs="+", default=["signal_vectors", "normalized_scores", "decision_timestamps", "entry_exit_reasons"])
    ap.add_argument("--timestamp-requirements", nargs="+", default=["entry_ts", "exit_ts"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    out = {
        "version": "1.0",
        "required_artifacts": args.required,
        "timestamp_requirements": args.timestamp_requirements,
        "contract": "Ledger trade records must include these artifacts for TRUE_REPLAY_POSSIBLE. Paper emission may add logging only; shadow backfill may synthesize where missing.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("CSA contract: required", args.required)
    return 0


if __name__ == "__main__":
    sys.exit(main())
