#!/usr/bin/env python3
"""Phase 0 / CSA: strict completeness + chain matrices (post-deploy window)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telemetry.alpaca_strict_completeness_gate import evaluate_completeness  # noqa: E402


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Strict completeness audit with chain matrices")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        required=True,
        help="UTC epoch floor for exit_attribution rows (e.g. service ActiveEnterTimestamp)",
    )
    args = ap.parse_args()
    r = evaluate_completeness(args.root.resolve(), open_ts_epoch=args.open_ts_epoch, audit=True)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
