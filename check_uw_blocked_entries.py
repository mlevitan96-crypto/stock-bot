#!/usr/bin/env python3
"""Check UW attribution for blocked entries"""
import json
from pathlib import Path

uw_attr_log = Path("data/uw_attribution.jsonl")
if not uw_attr_log.exists():
    print("No UW attribution log found")
    exit(1)

print("=" * 80)
print("UW ATTRIBUTION - BLOCKED ENTRIES CHECK")
print("=" * 80)
print()

blocked = []
approved = []
other = []

with open(uw_attr_log, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            decision = rec.get("decision", "")
            
            if "BLOCKED" in decision.upper() or decision.upper() == "BLOCKED":
                blocked.append(rec)
            elif "APPROVED" in decision.upper():
                approved.append(rec)
            else:
                other.append(rec)
        except:
            continue

print(f"Total UW attribution records: {len(blocked) + len(approved) + len(other)}")
print(f"Blocked entries: {len(blocked)}")
print(f"Approved entries: {len(approved)}")
print(f"Other decisions: {len(other)}")
print()

if blocked:
    print("Sample blocked entry:")
    print(json.dumps(blocked[0], indent=2))
    print()
    
    # Check decision values
    decisions = set(rec.get("decision", "") for rec in blocked)
    print(f"Blocked decision values found: {decisions}")
else:
    print("No blocked entries found in UW attribution log")
    print("Checking all decision values...")
    all_decisions = set()
    with open(uw_attr_log, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    rec = json.loads(line)
                    all_decisions.add(rec.get("decision", ""))
                except:
                    pass
    print(f"All decision values in log: {all_decisions}")
