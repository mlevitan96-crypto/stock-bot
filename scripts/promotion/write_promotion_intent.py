#!/usr/bin/env python3
"""
Write promotion intent (audit trail) before applying a paper promotion.
Read-only audit; no config changes.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write promotion intent for audit.")
    parser.add_argument("--config-id", required=True, help="Promoted config_id (e.g. from Top-3).")
    parser.add_argument("--date", required=True, help="Date YYYY-MM-DD.")
    parser.add_argument("--mode", default="paper", help="Target mode (paper only).")
    parser.add_argument("--intent", default="learning_promotion", help="Intent label.")
    parser.add_argument("--rationale", required=True, help="Human-readable rationale.")
    parser.add_argument("--output", required=True, help="Output PROMOTION_INTENT_${CONFIG_ID}_${DATE}.json path.")
    args = parser.parse_args()

    if args.mode != "paper":
        raise SystemExit("Only mode=paper is allowed for this promotion path.")

    intent = {
        "config_id": args.config_id,
        "date": args.date,
        "mode": args.mode,
        "intent": args.intent,
        "rationale": args.rationale,
        "written_at": datetime.now(timezone.utc).isoformat(),
    }

    root = Path(os.getcwd())
    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(intent, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
