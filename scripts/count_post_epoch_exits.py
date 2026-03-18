#!/usr/bin/env python3
"""Count exit_attribution lines with exit timestamp >= repair_iso_utc."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EPOCH = REPO / "state" / "alpaca_telemetry_repair_epoch.json"
EXIT = REPO / "logs" / "exit_attribution.jsonl"


def main() -> int:
    if not EPOCH.exists():
        print(0)
        return 0
    t0 = json.loads(EPOCH.read_text(encoding="utf-8")).get("repair_iso_utc", "")[:19]
    n = 0
    if not EXIT.exists():
        print(0)
        return 0
    with EXIT.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ts = str(r.get("timestamp") or "")[:19]
                if ts and ts >= t0:
                    n += 1
            except json.JSONDecodeError:
                pass
    print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
