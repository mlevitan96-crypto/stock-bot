#!/usr/bin/env python3
"""
Activate a tuning overlay for the paper engine by writing it to config/tuning/active.json.
The tuning_loader reads active.json (or GOVERNED_TUNING_CONFIG); this binds the overlay live.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG_TUNING_ACTIVE = REPO / "config" / "tuning" / "active.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Set active tuning config for paper engine")
    ap.add_argument("--mode", default="paper")
    ap.add_argument("--config", required=True, help="Path to overlay (e.g. config/overlays/exit_aggression_paper.json)")
    ap.add_argument("--output", required=True, help="e.g. reports/runtime/ACTIVE_TUNING_CONFIG_<date>.json")
    args = ap.parse_args()

    overlay_path = Path(args.config)
    if not overlay_path.is_absolute():
        overlay_path = (REPO / overlay_path).resolve()
    if not overlay_path.exists():
        print(f"Overlay not found: {overlay_path}", file=sys.stderr)
        return 2

    # Write overlay content to config/tuning/active.json so tuning_loader uses it
    CONFIG_TUNING_ACTIVE.parent.mkdir(parents=True, exist_ok=True)
    content = json.loads(overlay_path.read_text(encoding="utf-8"))
    CONFIG_TUNING_ACTIVE.write_text(json.dumps(content, indent=2), encoding="utf-8")
    now = datetime.now(timezone.utc)

    record = {
        "mode": args.mode,
        "config_path": str(overlay_path),
        "active_path": str(CONFIG_TUNING_ACTIVE),
        "bound_at": now.isoformat(),
        "version": content.get("version"),
    }

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = (REPO / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("Active tuning bound:", CONFIG_TUNING_ACTIVE, "<-", overlay_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
