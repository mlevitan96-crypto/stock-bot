#!/usr/bin/env python3
"""
Assert continuous promotion: current exit experiment verdict and next promotion verdict both exist and are valid.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert continuous promotion chain")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--current", required=True, help="CSA_EXIT_EXPERIMENT_VERDICT_<date>.json")
    ap.add_argument("--next", required=True, help="CSA_NEXT_PROMOTION_VERDICT_<date>.json")
    args = ap.parse_args()

    current_path = Path(args.current)
    next_path = Path(args.next)
    if not current_path.exists():
        print(f"Current verdict missing: {current_path}", file=sys.stderr)
        return 1
    if not next_path.exists():
        print(f"Next verdict missing: {next_path}", file=sys.stderr)
        return 1

    current = json.loads(current_path.read_text(encoding="utf-8"))
    next_data = json.loads(next_path.read_text(encoding="utf-8"))

    if current.get("verdict") not in ("EXTEND", "AMPLIFY", "REVERT"):
        print("Current verdict invalid:", current.get("verdict"), file=sys.stderr)
        return 1
    if next_data.get("verdict") != "GO":
        print("Next promotion verdict not GO:", next_data.get("verdict"), file=sys.stderr)
        return 1

    print("Continuous promotion asserted: current", current.get("verdict"), "-> next", next_data.get("verdict"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
