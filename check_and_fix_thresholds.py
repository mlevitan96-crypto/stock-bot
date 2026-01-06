#!/usr/bin/env python3
"""Check and fix threshold file"""

import json
from pathlib import Path

threshold_file = Path("state/uw_thresholds_hierarchical.json")

if threshold_file.exists():
    print(f"Threshold file exists: {threshold_file}")
    data = json.load(open(threshold_file))
    print(f"Contents: {json.dumps(data, indent=2)}")
    
    # Check if any thresholds are > 3.0
    high_thresholds = {}
    for symbol, thresh in data.items():
        if isinstance(thresh, (int, float)) and thresh > 3.0:
            high_thresholds[symbol] = thresh
    
    if high_thresholds:
        print(f"\nWARNING: Found high thresholds: {high_thresholds}")
        print("Deleting threshold file to use defaults (2.7)")
        threshold_file.unlink()
        print("Threshold file deleted - will use defaults from ENTRY_THRESHOLDS")
    else:
        print("\nThresholds look OK")
else:
    print("No threshold file - will use defaults from ENTRY_THRESHOLDS (2.7)")
