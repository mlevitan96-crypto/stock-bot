#!/usr/bin/env python3
"""
Assert that a promotion was applied: verify PROMOTION_APPLIED artifact and overlay path.
Writes ASSERT_PROMOTION_APPLIED_${CONFIG_ID}_${DATE}.json.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Assert promotion applied.")
    parser.add_argument("--applied", required=True, help="Path to PROMOTION_APPLIED_${CONFIG_ID}_${DATE}.json.")
    parser.add_argument("--output", required=True, help="Output ASSERT_PROMOTION_APPLIED_${CONFIG_ID}_${DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.applied, encoding="utf-8") as f:
        applied = json.load(f)

    overlay_path = root / applied.get("overlay_path", "")
    overlay_exists = overlay_path.exists()
    result = {
        "config_id": applied.get("config_id"),
        "date": applied.get("date"),
        "applied_path": args.applied,
        "overlay_path": applied.get("overlay_path"),
        "overlay_exists": overlay_exists,
        "passed": overlay_exists,
        "message": "Promotion applied; overlay present." if overlay_exists else "Overlay file missing.",
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")
    if not overlay_exists:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
