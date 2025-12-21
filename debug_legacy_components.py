#!/usr/bin/env python3
"""
Debug Legacy Components - Check actual values in historical data
"""

import json
from pathlib import Path
from fix_component_tracking import normalize_components_for_learning

def debug_legacy_components():
    """Check what values legacy components have and how they normalize"""
    print("=" * 80)
    print("DEBUGGING LEGACY COMPONENT VALUES")
    print("=" * 80)
    print()
    
    attr_log = Path("logs/attribution.jsonl")
    if not attr_log.exists():
        print("❌ attribution.jsonl not found")
        return
    
    sample_count = 0
    with open(attr_log, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10:  # Check first 10 trades
                break
            if line.strip():
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "attribution":
                        ctx = rec.get("context", {})
                        comps = ctx.get("components", {}) or rec.get("components", {})
                        if comps:
                            sample_count += 1
                            print(f"Trade {sample_count}: {rec.get('symbol')}")
                            print(f"  Original components: {comps}")
                            
                            # Normalize
                            normalized = normalize_components_for_learning(comps)
                            
                            # Show which components have non-zero values
                            non_zero = {k: v for k, v in normalized.items() if v != 0}
                            print(f"  Normalized (non-zero only): {non_zero}")
                            print(f"  P&L: {rec.get('pnl_pct', 0)}%")
                            print()
                except Exception as e:
                    print(f"Error processing record: {e}")
                    import traceback
                    traceback.print_exc()
    
    print("=" * 80)

if __name__ == "__main__":
    debug_legacy_components()
