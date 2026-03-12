#!/usr/bin/env python3
"""
Assert that an explicit human promotion decision is required.
Reads PROMOTION_STATUS_${DATE}.json; writes PROMOTION_DECISION_REQUIRED_${DATE}.json.
No auto-promotion; checkpoint only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Assert promotion decision required (no auto-promotion).")
    parser.add_argument(
        "--status",
        required=True,
        help="Path to PROMOTION_STATUS_${DATE}.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output PROMOTION_DECISION_REQUIRED_${DATE}.json path.",
    )
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.status, encoding="utf-8") as f:
        status = json.load(f)

    decision_required = status.get("decision_required", False)
    result = {
        "promotion_decision_required": decision_required,
        "shortlist_count": status.get("shortlist_count", 0),
        "top_config_id": status.get("top_config_id"),
        "message": "Explicit human decision required. No auto-promotion."
            if decision_required else "No shortlist; no decision required.",
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")
    if decision_required:
        print("AWAIT HUMAN DECISION — promotion shortlist present.")


if __name__ == "__main__":
    main()
