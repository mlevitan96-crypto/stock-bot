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

# OLD component names from historical attribution.jsonl (legacy format)
# Map old names to new SIGNAL_COMPONENTS
LEGACY_COMPONENT_MAP = {
    "flow_count": "options_flow",      # Old flow metric -> options_flow
    "flow_premium": "options_flow",     # Old flow metric -> options_flow
    "darkpool": "dark_pool",            # Old dark pool name -> dark_pool
    "gamma": "greeks_gamma",            # Old gamma -> greeks_gamma
    "net_premium": "options_flow",      # Old premium metric -> options_flow
    "volatility": "iv_term_skew",       # Old volatility -> iv_term_skew (closest match)
    # Note: Many old components don't map cleanly to new ones
    # We'll aggregate them to the closest match
}

# Additional mappings for components that might appear with different names
ADDITIONAL_NAME_MAP = {
    "whale_persistence": "whale_persistence",  # Direct match
    "temporal_motif": "temporal_motif",  # Direct match
    "regime_modifier": "regime_modifier",  # Direct match
    "calendar_catalyst": "calendar_catalyst",  # Direct match
}

def normalize_components_for_learning(components_dict: dict) -> dict:
    """
    Normalize component names from composite_score_v3 format OR legacy format to SIGNAL_COMPONENTS format.
    Handles both:
    1. New format: composite_score_v3 component names
    2. Legacy format: Old attribution.jsonl component names (flow_count, darkpool, etc.)
    
    Ensures ALL SIGNAL_COMPONENTS are included, even if value is 0.
    
    Args:
        components_dict: Components dict from compute_composite_score_v3 OR legacy attribution.jsonl
        
    Returns:
        Normalized dict with all SIGNAL_COMPONENTS, using correct names
    """
    normalized = {}
    
    # First, try new format mapping (composite_score_v3)
    for comp_name, value in components_dict.items():
        mapped_name = COMPONENT_NAME_MAP.get(comp_name)
        if mapped_name and mapped_name in SIGNAL_COMPONENTS:
            # Aggregate if multiple old components map to same new component
            if mapped_name in normalized:
                # Take the maximum value (most significant contribution)
                normalized[mapped_name] = max(normalized[mapped_name], float(value) if value is not None else 0.0)
            else:
                normalized[mapped_name] = float(value) if value is not None else 0.0
    
    # Second, try legacy format mapping (old attribution.jsonl)
    for comp_name, value in components_dict.items():
        if comp_name in LEGACY_COMPONENT_MAP:
            mapped_name = LEGACY_COMPONENT_MAP[comp_name]
            if mapped_name in SIGNAL_COMPONENTS:
                try:
                    val = float(value) if value is not None else 0.0
                    # Aggregate if multiple old components map to same new component
                    if mapped_name in normalized:
                        # Sum the values (multiple legacy components contribute to same signal)
                        # Use absolute value to ensure positive contribution
                        normalized[mapped_name] = normalized[mapped_name] + abs(val)
                    else:
                        # For legacy components, use absolute value
                        # Legacy values might be in different scale, so we normalize
                        normalized[mapped_name] = abs(val) if val != 0 else 0.0
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
    
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
