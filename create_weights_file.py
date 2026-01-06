#!/usr/bin/env python3
"""Create default weights file on droplet"""

import json
import time
from pathlib import Path

weights = {
    "weights": {
        "options_flow": 2.4,
        "dark_pool": 1.3,
        "insider": 0.5,
        "iv_term_skew": 0.6,
        "smile_slope": 0.35,
        "whale_persistence": 0.7,
        "event_alignment": 0.4,
        "toxicity_penalty": -0.9,
        "temporal_motif": 0.6,
        "regime_modifier": 0.3,
        "congress": 0.9,
        "shorts_squeeze": 0.7,
        "institutional": 0.5,
        "market_tide": 0.4,
        "calendar_catalyst": 0.45,
        "etf_flow": 0.3,
        "greeks_gamma": 0.4,
        "ftd_pressure": 0.3,
        "iv_rank": 0.2,
        "oi_change": 0.35,
        "squeeze_score": 0.2
    },
    "updated_at": int(time.time()),
    "updated_dt": "2026-01-06 00:00:00 UTC",
    "source": "default_weights_v3"
}

# Write to data/uw_weights.json
Path("data").mkdir(exist_ok=True)
with open("data/uw_weights.json", "w") as f:
    json.dump(weights, f, indent=2)

print("Created data/uw_weights.json")
