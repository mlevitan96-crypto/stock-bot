#!/usr/bin/env python3
"""Write state/alpaca_telemetry_repair_epoch.json at deploy — forward proof counts exits after this instant."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "state" / "alpaca_telemetry_repair_epoch.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    commit = ""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO), text=True, timeout=10
        ).strip()
    except Exception:
        pass
    rec = {
        "repair_iso_utc": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit,
        "note": "Forward proof: exits with exit timestamp >= repair_iso_utc must have entry in alpaca_entry_attribution.jsonl",
    }
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
