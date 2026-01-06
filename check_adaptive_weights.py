#!/usr/bin/env python3
"""Check adaptive weights"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Check adaptive weights file
weights_file = Path("data/signal_weights.json")
if weights_file.exists():
    data = json.load(open(weights_file))
    print(f"Adaptive weights file exists: {weights_file}")
    print(f"Contents:")
    print(json.dumps(data, indent=2)[:2000])
    
    # Check if options_flow is too low
    if "options_flow" in data:
        flow_weight = data["options_flow"]
        print(f"\nWARNING: options_flow weight is {flow_weight} (should be ~2.4)")
        if flow_weight < 1.0:
            print(f"CRITICAL: Flow weight too low! This is killing all scores!")
else:
    print("No adaptive weights file - using defaults")

# Check what get_weight returns
import uw_composite_v2
flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
print(f"\nActual weight from get_weight('options_flow', 'mixed'): {flow_weight}")
print(f"Expected (WEIGHTS_V3): {uw_composite_v2.WEIGHTS_V3.get('options_flow', 2.4)}")

if flow_weight < 1.0:
    print(f"\nCRITICAL: Flow weight is {flow_weight} instead of 2.4!")
    print("This is why scores are so low!")
