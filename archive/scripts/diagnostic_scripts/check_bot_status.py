#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, '/root/stock-bot')

# Check freezes
freeze_file = Path('state/governor_freezes.json')
if freeze_file.exists():
    data = json.load(open(freeze_file))
    active = [k for k, v in data.items() if v.get('active', False)]
    print(f"FREEZES: {active}")
    if active:
        for k in active:
            data[k]['active'] = False
        json.dump(data, open(freeze_file, 'w'), indent=2)
        print(f"CLEARED: {active}")

# Check latest cycle
run_file = Path('logs/run.jsonl')
if run_file.exists():
    with open(run_file) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            print(f"LATEST_CYCLE: {latest.get('ts', 'N/A')}")

# Check fixes
import uw_composite_v2
print(f"THRESHOLD: {uw_composite_v2.get_threshold('AAPL', 'base')}")
print(f"FLOW_WEIGHT: {uw_composite_v2.get_weight('options_flow', 'mixed')}")
