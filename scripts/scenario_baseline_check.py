#!/usr/bin/env python3
"""Phase 1: Confirm last-387 baseline on droplet. Exit 0 only if telemetry_backed=387, replay_ready=true."""
from __future__ import annotations
import json
import sys
from pathlib import Path

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if not path.exists():
        print("FAIL: last387_comprehensive_review.json not found", file=sys.stderr)
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    lt = data.get("learning_telemetry") or {}
    tb = lt.get("telemetry_backed")
    ready = lt.get("ready_for_replay")
    if tb != 387:
        print(f"FAIL: telemetry_backed={tb} (expected 387)", file=sys.stderr)
        return 1
    if ready is not True:
        print(f"FAIL: ready_for_replay={ready} (expected true)", file=sys.stderr)
        return 1
    print("OK: baseline confirmed (telemetry_backed=387, replay_ready=true)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
