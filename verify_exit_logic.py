#!/usr/bin/env python3
"""Verify exit logic is working correctly"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("EXIT LOGIC VERIFICATION")
print("="*80)

# Check if positions have exit logic
meta_file = Path("state/position_metadata.json")
if meta_file.exists():
    meta = json.load(open(meta_file))
    print(f"\nPositions tracked: {len(meta)}")
    
    for sym, data in list(meta.items())[:10]:
        entry_ts = data.get("entry_ts", "")
        entry_price = data.get("entry_price", 0)
        entry_score = data.get("entry_score", 0)
        side = data.get("side", "?")
        
        print(f"\n{sym}:")
        print(f"  Entry: {entry_ts[:19] if entry_ts else 'N/A'}")
        print(f"  Price: ${entry_price:.2f}")
        print(f"  Score: {entry_score:.2f}")
        print(f"  Side: {side}")
        
        # Check if exit conditions are configured
        if "targets" in data:
            print(f"  Exit targets configured: ✅")
        else:
            print(f"  Exit targets: Not found")

# Check exit logs
exits_file = Path("logs/exits.jsonl")
if exits_file.exists():
    exit_lines = exits_file.read_text().strip().split('\n')
    if exit_lines:
        print(f"\nRecent exits: {len(exit_lines)}")
        for line in exit_lines[-5:]:
            ex = json.loads(line)
            print(f"  {ex.get('symbol', '?')}: {ex.get('reason', '?')} at {ex.get('ts', '?')[:19]}")
    else:
        print("\nNo exit logs (positions may still be open)")

print("\n" + "="*80)
