#!/usr/bin/env python3
"""Reset adaptive weights that are killing scores"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Check entry_model state
try:
    from adaptive_signal_optimizer import AdaptiveSignalOptimizer
    optimizer = AdaptiveSignalOptimizer()
    
    if hasattr(optimizer, 'entry_model'):
        print("Found entry_model")
        
        # Check current weight
        current_weight = optimizer.entry_model.get_effective_weight("options_flow", "mixed")
        print(f"Current options_flow weight: {current_weight}")
        
        # Reset to default
        if hasattr(optimizer.entry_model, 'reset_component_weight'):
            optimizer.entry_model.reset_component_weight("options_flow")
            print("Reset options_flow weight")
        elif hasattr(optimizer.entry_model, 'set_weight'):
            optimizer.entry_model.set_weight("options_flow", 2.4)
            print("Set options_flow weight to 2.4")
        else:
            # Try to clear the state
            state_file = Path("state/adaptive_entry_weights.json")
            if state_file.exists():
                state_file.unlink()
                print(f"Deleted {state_file}")
            
            # Also try signal_weights.json
            weights_file = Path("data/signal_weights.json")
            if weights_file.exists():
                data = json.load(open(weights_file))
                if "options_flow" in data:
                    del data["options_flow"]
                    json.dump(data, open(weights_file, 'w'), indent=2)
                    print(f"Removed options_flow from {weights_file}")
        
        # Verify reset
        new_weight = optimizer.entry_model.get_effective_weight("options_flow", "mixed")
        print(f"New options_flow weight: {new_weight}")
    else:
        print("No entry_model found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Fallback: Delete adaptive weight files
    print("\nTrying fallback: Delete adaptive weight files")
    for path in [
        Path("state/adaptive_entry_weights.json"),
        Path("data/signal_weights.json"),
        Path("state/entry_model_state.json"),
    ]:
        if path.exists():
            path.unlink()
            print(f"Deleted {path}")
