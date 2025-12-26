#!/usr/bin/env python3
"""
Fix adaptive weights initialization - ensure all components are initialized
"""

import json
from pathlib import Path

def fix_weights():
    """Initialize weight bands for all components"""
    state_file = Path("state/signal_weights.json")
    
    # Component list
    SIGNAL_COMPONENTS = [
        "options_flow", "dark_pool", "insider", "iv_term_skew", "smile_slope",
        "whale_persistence", "event_alignment", "temporal_motif", "toxicity_penalty",
        "regime_modifier", "congress", "shorts_squeeze", "institutional", "market_tide",
        "calendar_catalyst", "etf_flow", "greeks_gamma", "ftd_pressure", "iv_rank",
        "oi_change", "squeeze_score"
    ]
    
    # Load or create state
    if state_file.exists():
        with state_file.open() as f:
            state = json.load(f)
    else:
        state = {}
    
    # Initialize weight_bands if missing or empty
    if "weight_bands" not in state or not state["weight_bands"]:
        state["weight_bands"] = {}
    
    # Initialize all components
    for component in SIGNAL_COMPONENTS:
        if component not in state["weight_bands"]:
            state["weight_bands"][component] = {
                "min_weight": 0.25,
                "max_weight": 2.5,
                "neutral": 1.0,
                "current": 1.0,
                "ewma_performance": 0.5,
                "sample_count": 0,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "last_updated": 0
            }
    
    # Save
    state_file.parent.mkdir(exist_ok=True)
    with state_file.open("w") as f:
        json.dump(state, f, indent=2)
    
    print(f"Initialized {len(SIGNAL_COMPONENTS)} weight bands")
    print(f"Components: {', '.join(SIGNAL_COMPONENTS[:5])}... ({len(SIGNAL_COMPONENTS)} total)")

if __name__ == "__main__":
    fix_weights()

