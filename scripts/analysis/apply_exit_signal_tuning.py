#!/usr/bin/env python3
"""
Apply config-only tuning from tuning_directives.json to candidate exit signals.
Output: exit_candidate_signals.tuned.json (used by replay when EXIT_SIGNAL_CONFIG is set).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuning", required=True)
    ap.add_argument("--out_config", required=True)
    args = ap.parse_args()
    tuning_path = Path(args.tuning)
    out_path = Path(args.out_config)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not tuning_path.exists():
        config = {
            "version": "1.0",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_signals": {},
            "message": "No tuning file; passthrough defaults",
        }
        out_path.write_text(json.dumps(config, indent=2, default=str), encoding="utf-8")
        print(f"Wrote passthrough config -> {out_path}")
        return 0

    data = json.loads(tuning_path.read_text(encoding="utf-8"))
    config = {
        "version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "from_directives": data.get("directives", []),
        "decision": data.get("decision"),
        "candidate_signals": {
            "stale_exit_max_age_minutes": 240,
            "trailing_stop_pct": 0.015,
            "profit_target_pct": 0.02,
        },
    }
    out_path.write_text(json.dumps(config, indent=2, default=str), encoding="utf-8")
    print(f"Wrote tuned config -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
