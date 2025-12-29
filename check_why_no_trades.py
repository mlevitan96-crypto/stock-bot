#!/usr/bin/env python3
"""Check why trades aren't happening"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("CHECKING WHY NO TRADES")
print("="*80)

# Check recent signals
attribution_file = Path("data/uw_attribution.jsonl")
if not attribution_file.exists():
    attribution_file = Path("logs/attribution.jsonl")

if attribution_file.exists():
    signals = []
    with attribution_file.open() as f:
        for line in f:
            try:
                s = json.loads(line.strip())
                if s.get("type") == "attribution":
                    signals.append(s)
            except:
                continue
    
    print(f"\nLast 10 signals:")
    for s in signals[-10:]:
        symbol = s.get("symbol", "N/A")
        score = s.get("score", 0)
        decision = s.get("decision", "unknown")
        print(f"  {symbol}: score={score:.2f}, decision={decision}")
else:
    print("\nNo attribution file found")

# Check run.jsonl for cycles
run_file = Path("logs/run.jsonl")
if run_file.exists():
    cycles = []
    with run_file.open() as f:
        for line in f:
            try:
                c = json.loads(line.strip())
                cycles.append(c)
            except:
                continue
    
    print(f"\nLast 5 cycles:")
    for c in cycles[-5:]:
        ts = c.get("ts", 0)
        dt = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else "N/A"
        clusters = c.get("clusters", 0)
        orders = c.get("orders", 0)
        print(f"  {dt}: clusters={clusters}, orders={orders}")
else:
    print("\nNo run.jsonl file found")

# Check MIN_EXEC_SCORE
import os
from dotenv import load_dotenv
load_dotenv()
min_score = float(os.getenv("MIN_EXEC_SCORE", "2.0"))
print(f"\nMIN_EXEC_SCORE: {min_score}")

# Check freeze state
freeze_path = Path("state/pre_market_freeze.flag")
if freeze_path.exists():
    reason = freeze_path.read_text().strip()
    print(f"\n[ERROR] FREEZE ACTIVE: {reason}")
else:
    print("\n[OK] No freeze flag")

print("\n" + "="*80)

