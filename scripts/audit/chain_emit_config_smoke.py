#!/usr/bin/env python3
"""Print effective strict-chain telemetry flags from environment (mirrors main.Config defaults)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _eb(name: str, default: str = "true") -> bool:
    return os.environ.get(name, default).lower() == "true"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    log_dir = os.environ.get("LOG_DIR", "logs")
    out = {
        "PHASE2_TELEMETRY_ENABLED": _eb("PHASE2_TELEMETRY_ENABLED", "true"),
        "STRICT_RUNLOG_TELEMETRY_ENABLED": _eb("STRICT_RUNLOG_TELEMETRY_ENABLED", "true"),
        "strict_runlog_effective": _eb("PHASE2_TELEMETRY_ENABLED", "true")
        or _eb("STRICT_RUNLOG_TELEMETRY_ENABLED", "true"),
        "run_jsonl_abspath": str((root / log_dir / "run.jsonl").resolve()),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
