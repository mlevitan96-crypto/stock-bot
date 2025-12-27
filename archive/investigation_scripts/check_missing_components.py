#!/usr/bin/env python3
"""
Check why some components have 0 samples

Analyzes attribution.jsonl to see what component names are actually being used.
"""

import json
from pathlib import Path
from collections import Counter

def check_component_names():
    """Check what component names appear in actual trade data"""
    print("=" * 80)
    print("CHECKING COMPONENT NAMES IN TRADE DATA")
    print("=" * 80)
    print()
    
    attr_log = Path("logs/attribution.jsonl")
    if not attr_log.exists():
        print("❌ attribution.jsonl not found")
        return
    
    component_names = Counter()
    sample_records = []
    
    with open(attr_log, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 100:  # Check first 100 trades
                break
            if line.strip():
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "attribution":
                        ctx = rec.get("context", {})
                        comps = ctx.get("components", {}) or rec.get("components", {})
                        if comps:
                            for comp_name in comps.keys():
                                component_names[comp_name] += 1
                            if len(sample_records) < 3:
                                sample_records.append({
                                    "symbol": rec.get("symbol"),
                                    "components": list(comps.keys())
                                })
                except:
                    pass
    
    print("Component names found in trade data:")
    print()
    for comp_name, count in component_names.most_common():
        print(f"  {comp_name:25s}: {count} occurrences")
    
    print()
    print("Sample records:")
    for rec in sample_records:
        print(f"  {rec['symbol']}: {len(rec['components'])} components")
        print(f"    {', '.join(rec['components'][:10])}")
        if len(rec['components']) > 10:
            print(f"    ... and {len(rec['components']) - 10} more")
        print()
    
    # Check for missing components
    from adaptive_signal_optimizer import SIGNAL_COMPONENTS
    missing_components = set(SIGNAL_COMPONENTS) - set(component_names.keys())
    
    if missing_components:
        print("⚠ Components in SIGNAL_COMPONENTS but NOT found in trade data:")
        for comp in sorted(missing_components):
            print(f"    - {comp}")
        print()
        print("These components may:")
        print("  1. Not be included in composite_score_v3 return")
        print("  2. Have different names in the actual data")
        print("  3. Always be 0 (never contribute to trades)")
    else:
        print("✓ All SIGNAL_COMPONENTS found in trade data")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    check_component_names()
