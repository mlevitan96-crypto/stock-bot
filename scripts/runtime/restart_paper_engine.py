#!/usr/bin/env python3
"""
Record intent to run paper engine with exit overlay. Entries and CI unchanged.
Supports: (1) --exit-overlay + --entries-unchanged/--ci-unchanged, or (2) --mode paper + --reason.
On a real droplet this would restart the trading process; here we write runtime state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG_TUNING_ACTIVE = REPO / "config" / "tuning" / "active.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Activate paper engine with exit overlay")
    ap.add_argument("--exit-overlay", default=None, help="Path to exit_aggression_paper.json (optional if active already set)")
    ap.add_argument("--mode", default=None, help="e.g. paper")
    ap.add_argument("--reason", default=None, help="Restart reason (e.g. Activate exit aggression promotion)")
    ap.add_argument("--entries-unchanged", action="store_true", default=True)
    ap.add_argument("--ci-unchanged", action="store_true", default=True)
    args = ap.parse_args()

    overlay_path = None
    if args.exit_overlay:
        overlay_path = Path(args.exit_overlay)
        if not overlay_path.is_absolute():
            overlay_path = (REPO / overlay_path).resolve()
        if not overlay_path.exists():
            print(f"Exit overlay missing: {overlay_path}", file=sys.stderr)
            return 2
    else:
        # Resolve from active.json or env
        env_path = os.environ.get("GOVERNED_TUNING_CONFIG")
        if env_path:
            overlay_path = Path(env_path)
            if not overlay_path.is_absolute():
                overlay_path = (REPO / overlay_path).resolve()
        elif CONFIG_TUNING_ACTIVE.exists():
            overlay_path = CONFIG_TUNING_ACTIVE

    state = {
        "exit_overlay_path": str(overlay_path.resolve()) if overlay_path and overlay_path.exists() else None,
        "entries_unchanged": args.entries_unchanged,
        "ci_unchanged": args.ci_unchanged,
        "reason": args.reason or "Activate exit overlay",
        "mode": args.mode or "paper",
        "restart_requested_at": datetime.now(timezone.utc).isoformat(),
        "instruction": "Paper engine should use config/tuning/active.json or GOVERNED_TUNING_CONFIG; restart process to pick up overlay.",
    }

    runtime_dir = REPO / "reports" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    state_path = runtime_dir / "PAPER_ENGINE_OVERLAY_STATE.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("Paper engine overlay state written:", state_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
