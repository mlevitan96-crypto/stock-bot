#!/usr/bin/env python3
"""
Fix Component Tracking - Ensure ALL components are tracked with correct names

Maps component names from composite_score_v3 to SIGNAL_COMPONENTS names.
Ensures ALL components are included in learning, even if value is 0.
"""

from adaptive_signal_optimizer import SIGNAL_COMPONENTS

# Component name mapping: composite_score_v3 -> SIGNAL_COMPONENTS
COMPONENT_NAME_MAP = {
    "flow": "options_flow",
    "dark_pool": "dark_pool",  # Same
    "insider": "insider",  # Same
    "iv_skew": "iv_term_skew",
    "smile": "smile_slope",
    "whale": "whale_persistence",
    "event": "event_alignment",
    "motif_bonus": "temporal_motif",  # Close mapping
    "toxicity_penalty": "toxicity_penalty",  # Same
    "regime": "regime_modifier",
    "congress": "congress",  # Same
    "shorts_squeeze": "shorts_squeeze",  # Same
    "institutional": "institutional",  # Same
    "market_tide": "market_tide",  # Same
    "calendar": "calendar_catalyst",
    "greeks_gamma": "greeks_gamma",  # Same
    "ftd_pressure": "ftd_pressure",  # Same
    "iv_rank": "iv_rank",  # Same
    "oi_change": "oi_change",  # Same
    "etf_flow": "etf_flow",  # Same
    "squeeze_score": "squeeze_score",  # Same
    "freshness_factor": None  # Not a signal component, just metadata
}

def normalize_components_for_learning(components_dict: dict) -> dict:
    """
    Normalize component names from composite_score_v3 format to SIGNAL_COMPONENTS format.
    Ensures ALL SIGNAL_COMPONENTS are included, even if value is 0.
    
    Args:
        components_dict: Components dict from compute_composite_score_v3
        
    Returns:
        Normalized dict with all SIGNAL_COMPONENTS, using correct names
    """
    normalized = {}
    
    # First, map existing components
    for comp_name, value in components_dict.items():
        mapped_name = COMPONENT_NAME_MAP.get(comp_name)
        if mapped_name and mapped_name in SIGNAL_COMPONENTS:
            normalized[mapped_name] = float(value) if value is not None else 0.0
    
    # Then, ensure ALL SIGNAL_COMPONENTS are present (even if 0)
    for component in SIGNAL_COMPONENTS:
        if component not in normalized:
            normalized[component] = 0.0
    
    return normalized

if __name__ == "__main__":
    # Test the mapping
    test_components = {
        "flow": 1.5,
        "dark_pool": 0.8,
        "iv_skew": 0.3,
        "smile": 0.2,
        "whale": 0.0,
        "event": 0.0,
        "regime": 0.1,
        "calendar": 0.0
    }
    
    normalized = normalize_components_for_learning(test_components)
    print("Original:", test_components)
    print("Normalized:", normalized)
    print()
    print("All SIGNAL_COMPONENTS included:", len(normalized) == len(SIGNAL_COMPONENTS))
    print("Missing components:", set(SIGNAL_COMPONENTS) - set(normalized.keys()))
