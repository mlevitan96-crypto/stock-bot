#!/usr/bin/env python3
"""
Extract human-readable promotion details from a learning_promotion overlay.
Outputs JSON: active, config_id, focus, key_changes, expected_impact.
Used by daily Telegram governance update (read-only).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"active": False}))
        return
    config_id = sys.argv[1]
    root = Path(os.getcwd())
    overlay = root / "config" / "tuning" / "overlays" / f"learning_promotion_{config_id}.json"

    if not overlay.exists():
        print(json.dumps({"active": False}))
        return

    with open(overlay, encoding="utf-8") as f:
        cfg = json.load(f)

    weights = cfg.get("weights", {})
    top = sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

    summary = {
        "active": True,
        "config_id": config_id,
        "focus": "Entry aggressiveness" if any("sv_" in k for k, _ in top) else "General tuning",
        "key_changes": [f"{k} → {v:+.2f}" for k, v in top],
        "expected_impact": {
            "trade_frequency": "increase",
            "risk": "moderate",
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
