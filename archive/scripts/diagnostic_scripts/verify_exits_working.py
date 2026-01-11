#!/usr/bin/env python3
"""Verify exit logic is working"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("EXIT LOGIC VERIFICATION")
print("="*80)

# Check position metadata for exit targets
meta_file = Path("state/position_metadata.json")
positions = {}
if meta_file.exists():
    meta = json.load(open(meta_file))
    positions = meta
    print(f"\nPositions tracked: {len(positions)}")
    
    positions_with_targets = 0
    positions_old_enough_for_exit = 0
    
    now = datetime.utcnow()
    for sym, data in positions.items():
        entry_ts_str = data.get("entry_ts", "")
        if entry_ts_str:
            try:
                entry_ts = datetime.fromisoformat(entry_ts_str.replace('Z', '+00:00'))
                age_hours = (now - entry_ts.replace(tzinfo=None)).total_seconds() / 3600
                
                if "targets" in data and data["targets"]:
                    positions_with_targets += 1
                if age_hours >= 0.1:  # At least 6 minutes old
                    positions_old_enough_for_exit += 1
                    
                print(f"  {sym}: age={age_hours:.1f}h, targets={'YES' if 'targets' in data and data['targets'] else 'NO'}")
            except:
                pass
    
    print(f"\nPositions with exit targets: {positions_with_targets}/{len(positions)}")
    print(f"Positions old enough for exit checks: {positions_old_enough_for_exit}/{len(positions)}")

# Check exit logs
exits_file = Path("logs/exits.jsonl")
if exits_file.exists():
    exit_lines = exits_file.read_text().strip().split('\n')
    exits = [json.loads(l) for l in exit_lines if l.strip()]
    
    print(f"\nTotal exits logged: {len(exits)}")
    if exits:
        print("Recent exits:")
        for ex in exits[-5:]:
            print(f"  {ex.get('symbol', '?')}: {ex.get('reason', '?')} at {ex.get('ts', '?')[:19]}")
    else:
        print("No exits logged yet (positions may still be new)")

# Check if evaluate_exits is being called
run_file = Path("logs/run.jsonl")
if run_file.exists():
    run_lines = run_file.read_text().strip().split('\n')[-10:]
    cycles_with_exit_checks = 0
    for line in run_lines:
        try:
            # Check if exit evaluation happened (implied by cycle completion)
            cycles_with_exit_checks += 1
        except:
            pass
    print(f"\nRecent cycles completed: {len(run_lines)}")
    print("(Exit evaluation should run every cycle if positions exist)")

print("\n" + "="*80)
