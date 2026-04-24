#!/usr/bin/env python3
"""
Audit: Assert promotable shortlist contract (method, provenance). Fail-closed if not met.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert promotable shortlist contract")
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--require-method", default="true_replay_rescore")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.shortlist)
    if not path.exists():
        print(f"Shortlist missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    method = data.get("method")
    shortlist = data.get("shortlist", [])
    passed = method == args.require_method and len(shortlist) > 0
    blockers = []
    if method != args.require_method:
        blockers.append(f"method is '{method}', required '{args.require_method}'")
    if len(shortlist) == 0:
        blockers.append("shortlist is empty")

    out = {
        "shortlist_path": str(path.resolve()),
        "required_method": args.require_method,
        "actual_method": method,
        "shortlist_count": len(shortlist),
        "passed": passed,
        "blockers": blockers,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    if not passed:
        print("Assert failed:", blockers, file=sys.stderr)
        return 1
    print("Promotable shortlist contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
