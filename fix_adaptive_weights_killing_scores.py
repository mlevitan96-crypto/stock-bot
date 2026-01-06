#!/usr/bin/env python3
"""Fix adaptive weights that are killing scores"""

import json
from pathlib import Path

STATE_DIR = Path("state")
weights_file = STATE_DIR / "signal_weights.json"

print("=" * 80)
print("FIXING ADAPTIVE WEIGHTS KILLING SCORES")
print("=" * 80)

if weights_file.exists():
    print(f"\nFound weights file: {weights_file}")
    data = json.load(open(weights_file))
    
    # Check entry_model state
    if "entry_model" in data:
        entry_model = data["entry_model"]
        print(f"\nFound entry_model state")
        
        # Check regime_beta_distributions
        if "regime_beta_distributions" in entry_model:
            regime_betas = entry_model["regime_beta_distributions"]
            if "options_flow" in regime_betas:
                flow_betas = regime_betas["options_flow"]
                print(f"options_flow regime distributions: {json.dumps(flow_betas, indent=2)}")
                
                # Reset all regimes for options_flow
                for regime in flow_betas:
                    flow_betas[regime] = {
                        "alpha": 1.0,
                        "beta": 1.0,
                        "wins": 0,
                        "losses": 0,
                        "total_pnl": 0.0,
                        "sample_count": 0,
                        "last_updated": 0
                    }
                
                print(f"Reset options_flow Beta distributions to defaults (alpha=1.0, beta=1.0)")
        
        # Also check weight_bands (legacy)
        if "weight_bands" in entry_model:
            if "options_flow" in entry_model["weight_bands"]:
                entry_model["weight_bands"]["options_flow"]["current"] = 1.0
                print(f"Reset options_flow weight_band current to 1.0")
        
        # Save
        json.dump(data, open(weights_file, 'w'), indent=2)
        print(f"\nSaved fixed weights to {weights_file}")
    else:
        print("No entry_model in weights file")
else:
    print(f"\nNo weights file found at {weights_file}")
    print("Creating fresh weights file with defaults")
    
    # Create default structure
    default_data = {
        "entry_model": {
            "regime_beta_distributions": {
                "options_flow": {
                    "MIXED": {"alpha": 1.0, "beta": 1.0, "wins": 0, "losses": 0, "total_pnl": 0.0, "sample_count": 0, "last_updated": 0},
                    "RISK_ON": {"alpha": 1.0, "beta": 1.0, "wins": 0, "losses": 0, "total_pnl": 0.0, "sample_count": 0, "last_updated": 0},
                    "RISK_OFF": {"alpha": 1.0, "beta": 1.0, "wins": 0, "losses": 0, "total_pnl": 0.0, "sample_count": 0, "last_updated": 0}
                }
            }
        }
    }
    weights_file.parent.mkdir(parents=True, exist_ok=True)
    json.dump(default_data, open(weights_file, 'w'), indent=2)
    print(f"Created {weights_file} with defaults")

print("\n" + "=" * 80)
print("FIX COMPLETE")
print("=" * 80)
print("\noptions_flow weight should now return to 2.4 (default)")
print("Bot will need restart to reload weights")
