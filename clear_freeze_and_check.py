#!/usr/bin/env python3
"""Clear freeze flag and check actual positions"""

from pathlib import Path
import json

# Clear freeze flag
freeze_file = Path("state/pre_market_freeze.flag")
if freeze_file.exists():
    content = freeze_file.read_text()
    print(f"Freeze flag content: {content[:200]}")
    freeze_file.unlink()
    print("✅ Freeze flag cleared")
else:
    print("No freeze flag found")

# Check positions from metadata
metadata_file = Path("state/positions_metadata.json")
if metadata_file.exists():
    metadata = json.loads(metadata_file.read_text())
    print(f"\nPositions in metadata: {len(metadata)}")
    for symbol, info in list(metadata.items())[:10]:
        print(f"  {symbol}: {info.get('qty', 0)} @ ${info.get('entry_price', 0):.2f}")
else:
    print("\nMetadata file not found")

