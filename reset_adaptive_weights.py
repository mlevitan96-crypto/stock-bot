#!/usr/bin/env python3
"""
Reset all adaptive weight multipliers to 1.0 (neutral)
For high-velocity learning after component bug fixes
"""

import json
from pathlib import Path

def reset_multipliers():
    """Reset all multipliers in signal_weights.json to 1.0"""
    state_file = Path("state/signal_weights.json")
    
    if not state_file.exists():
        print(f"[WARN] State file not found: {state_file}")
        return False
    
    # Load current state
    with state_file.open() as f:
        state = json.load(f)
    
    # Reset all multipliers to 1.0
    weight_bands = state.get("weight_bands", {})
    reset_count = 0
    
    for component, band in weight_bands.items():
        if isinstance(band, dict):
            old_mult = band.get("current", 1.0)
            band["current"] = 1.0
            band["last_updated"] = 0  # Reset update timestamp
            reset_count += 1
            print(f"  {component:25} = {old_mult:6.3f} -> 1.000")
    
    # Save updated state
    state["reset_at"] = int(time.time())
    state["reset_reason"] = "High-velocity learning: reset after component bug fixes"
    
    with state_file.open("w") as f:
        json.dump(state, f, indent=2)
    
    print(f"\n[OK] Reset {reset_count} multipliers to 1.0")
    return True

if __name__ == "__main__":
    import time
    print("=" * 80)
    print("RESET ADAPTIVE WEIGHTS TO 1.0")
    print("=" * 80)
    print()
    reset_multipliers()

