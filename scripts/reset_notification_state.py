#!/usr/bin/env python3
"""Reset notification state to pre-dry-run values."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / "state" / "alpaca_trade_notifications.json"
PROMO = REPO / "state" / "alpaca_diagnostic_promotion.json"

if not PROMO.exists():
    print(f"Error: {PROMO} not found", file=sys.stderr)
    sys.exit(1)

with open(PROMO, "r") as f:
    promo = json.load(f)

state = {
    "promotion_tag": promo.get("promotion_tag", ""),
    "activated_utc": promo.get("activated_utc", ""),
    "notified_100": False,
    "notified_500": False,
    "last_count_utc": "",
    "last_count": 0,
}

with open(STATE, "w") as f:
    json.dump(state, f, indent=2)

print(f"Reset {STATE}")
print(json.dumps(state, indent=2))
