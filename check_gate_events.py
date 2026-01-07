#!/usr/bin/env python3
import json
from pathlib import Path

print("="*80)
print("CHECKING GATE EVENTS")
print("="*80)

gate_file = Path("logs/gate.jsonl")
if gate_file.exists():
    lines = gate_file.read_text().strip().split('\n')[-20:]
    print(f"\nLast {len(lines)} gate events:\n")
    
    blocker_counts = {}
    for line in lines:
        if line.strip():
            try:
                event = json.loads(line)
                reason = event.get("reason", event.get("msg", "unknown"))
                blocker_counts[reason] = blocker_counts.get(reason, 0) + 1
                print(f"{event.get('symbol', '?')}: {reason} (score={event.get('score', 'N/A')}, expectancy={event.get('expectancy', 'N/A')})")
            except:
                pass
    
    print("\n" + "="*80)
    print("BLOCKER SUMMARY:")
    for blocker, count in sorted(blocker_counts.items(), key=lambda x: -x[1]):
        print(f"  {blocker}: {count}")
