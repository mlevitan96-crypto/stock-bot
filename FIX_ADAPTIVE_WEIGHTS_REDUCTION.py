#!/usr/bin/env python3
"""
Fix Adaptive Weights Reduction - Reset weights that are killing scores

This script will:
1. Reset adaptive weight multipliers to 1.0 (neutral) for all components
2. Preserve the weights file structure
3. Optionally add safety floors for critical components
"""

import json
import sys
from pathlib import Path
from datetime import datetime

STATE_DIR = Path("state")
WEIGHTS_FILE = STATE_DIR / "signal_weights.json"

def reset_adaptive_weights(add_safety_floors=True):
    """Reset adaptive weights to defaults."""
    
    print("=" * 80)
    print("FIXING ADAPTIVE WEIGHTS REDUCTION")
    print("=" * 80)
    print()
    
    # Load current weights
    if not WEIGHTS_FILE.exists():
        print(f"❌ Weights file not found: {WEIGHTS_FILE}")
        return False
    
    print(f"Loading weights from: {WEIGHTS_FILE}")
    try:
        with open(WEIGHTS_FILE, 'r') as f:
            weights_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading weights: {e}")
        return False
    
    print("✅ Weights loaded")
    print()
    
    # Backup original file
    backup_file = STATE_DIR / f"signal_weights.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(weights_data, f, indent=2)
    print(f"✅ Backup created: {backup_file.name}")
    print()
    
    # Fix weight_bands
    if "entry_weights" in weights_data and "weight_bands" in weights_data["entry_weights"]:
        weight_bands = weights_data["entry_weights"]["weight_bands"]
        print(f"Found {len(weight_bands)} components in weight_bands")
        
        fixed_count = 0
        for component, band_data in weight_bands.items():
            current_mult = band_data.get("current", 1.0)
            
            # Check if weight is significantly reduced
            if current_mult < 0.8:  # More than 20% reduction
                print(f"  Fixing {component}: {current_mult:.3f} → 1.0")
                band_data["current"] = 1.0
                fixed_count += 1
            elif add_safety_floors and current_mult < 1.0:
                # Add safety floor at 0.5x (50% minimum)
                safety_floor = 0.5
                if current_mult < safety_floor:
                    print(f"  Raising {component}: {current_mult:.3f} → {safety_floor:.3f} (safety floor)")
                    band_data["current"] = safety_floor
                    fixed_count += 1
        
        print(f"\n✅ Fixed {fixed_count} components")
        print()
    else:
        print("⚠️  No weight_bands found in entry_weights")
        print()
    
    # Also check and fix regime_beta_distributions if they exist
    if "entry_weights" in weights_data and "regime_beta_distributions" in weights_data["entry_weights"]:
        regime_betas = weights_data["entry_weights"]["regime_beta_distributions"]
        print(f"Found regime_beta_distributions for {len(regime_betas)} components")
        
        # Reset beta distributions to defaults (alpha=1.0, beta=1.0)
        # This will cause weights to return to neutral
        reset_count = 0
        for component, regimes_data in regime_betas.items():
            if isinstance(regimes_data, dict):
                for regime, regime_data in regimes_data.items():
                    if isinstance(regime_data, dict):
                        # Reset to uniform prior (alpha=1, beta=1)
                        regime_data["alpha"] = 1.0
                        regime_data["beta"] = 1.0
                        regime_data["wins"] = 0
                        regime_data["losses"] = 0
                        regime_data["total_pnl"] = 0.0
                        regime_data["sample_count"] = 0
                        reset_count += 1
        
        if reset_count > 0:
            print(f"✅ Reset {reset_count} regime beta distributions to defaults")
        print()
    
    # Save fixed weights
    weights_data["saved_at"] = int(datetime.now().timestamp())
    weights_data["saved_dt"] = datetime.now().isoformat()
    weights_data["reset_reason"] = "Fixed 74.4% weight reductions causing stagnation"
    
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(weights_data, f, indent=2)
    
    print("✅ Fixed weights saved")
    print()
    print("=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart the bot service to reload weights")
    print("2. Monitor scores - they should increase significantly")
    print("3. Check stagnation alerts - they should decrease")
    print()
    
    return True

if __name__ == "__main__":
    success = reset_adaptive_weights(add_safety_floors=False)  # Full reset to 1.0
    sys.exit(0 if success else 1)
