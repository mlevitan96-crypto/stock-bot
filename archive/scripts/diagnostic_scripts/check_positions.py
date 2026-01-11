#!/usr/bin/env python3
import json
from pathlib import Path

print("="*80)
print("CHECKING CURRENT POSITIONS")
print("="*80)

# Check metadata
meta_file = Path("state/position_metadata.json")
if meta_file.exists():
    meta = json.load(open(meta_file))
    print(f"\nPositions in metadata: {len(meta)}")
    for sym, data in list(meta.items())[:10]:
        print(f"  {sym}: qty={data.get('qty', 0)}, side={data.get('side', '?')}")

# Check opens
opens_file = Path("state/opens.json")
if opens_file.exists():
    opens = json.load(open(opens_file))
    print(f"\nPositions in opens.json: {len(opens)}")
    for sym in list(opens.keys())[:10]:
        print(f"  {sym}")

print("\n" + "="*80)
