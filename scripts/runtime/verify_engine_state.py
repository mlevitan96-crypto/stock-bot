#!/usr/bin/env python3
"""
Verify the paper engine state: active tuning matches the expected overlay.
Output: PAPER_ENGINE_VERIFIED_<date>.json with verified flag and details.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG_TUNING_ACTIVE = REPO / "config" / "tuning" / "active.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify paper engine state")
    ap.add_argument("--mode", default="paper")
    ap.add_argument("--expect-overlay", required=True, help="Expected overlay path (e.g. config/overlays/exit_aggression_paper.json)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    expect_path = Path(args.expect_overlay)
    if not expect_path.is_absolute():
        expect_path = (REPO / expect_path).resolve()

    verified = False
    details = {}

    if not CONFIG_TUNING_ACTIVE.exists():
        details["error"] = "config/tuning/active.json missing"
    else:
        active_content = json.loads(CONFIG_TUNING_ACTIVE.read_text(encoding="utf-8"))
        details["active_version"] = active_content.get("version")
        details["active_exit_weights_keys"] = list((active_content.get("exit_weights") or {}).keys())
        # Compare content with expected overlay
        if expect_path.exists():
            expect_content = json.loads(expect_path.read_text(encoding="utf-8"))
            if active_content.get("version") == expect_content.get("version"):
                verified = True
            elif active_content.get("exit_weights") == expect_content.get("exit_weights"):
                verified = True
        else:
            details["note"] = "Expected overlay file not found; verified active.json present."

    out = {
        "mode": args.mode,
        "verified": verified,
        "expect_overlay": str(expect_path),
        "active_path": str(CONFIG_TUNING_ACTIVE),
        "details": details,
    }

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = (REPO / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Engine state verified:", verified, details.get("active_version", ""))
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
