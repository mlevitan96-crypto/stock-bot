# Causal Analysis Engine - Component Name Normalization Fix

## Problem Identified

The causal analysis engine was not finding data for components like "options_flow" because:

1. **Component Name Mismatch**: Attribution data stores components as "flow", "iv_skew", "smile" (short names from composite_score_v3), but the engine was looking for "options_flow", "iv_term_skew", "smile_slope" (SIGNAL_COMPONENTS names).

2. **Component Structure**: Some components are stored as dicts (e.g., `{"flow": {"conviction": 0.5}}`) which weren't being extracted correctly.

3. **Success Pattern Thresholds**: Thresholds were too high (60% win rate, 1% P&L), preventing identification of success patterns.

## Fixes Applied

### 1. Component Name Normalization

Added `_normalize_component_names()` method that:
- Maps "flow" → "options_flow"
- Maps "iv_skew" → "iv_term_skew"
- Maps "smile" → "smile_slope"
- Handles components stored as dicts (extracts numeric values)
- Only includes valid SIGNAL_COMPONENTS

### 2. Lower Success Pattern Thresholds

- Win rate threshold: 0.6 → 0.55 (55%)
- P&L threshold: 0.01 → 0.005 (0.5%)

This allows identification of more success patterns with the current data.

### 3. Enhanced Component Extraction

- Handles both "flow" and "options_flow" names
- Extracts values from nested dicts
- Safely handles missing or malformed data

## Expected Results

After this fix:
- Components like "options_flow" will be found (mapped from "flow")
- More success patterns will be identified
- Better insights into when signals work best
- More accurate failure pattern analysis

## Next Steps

1. Re-run causal analysis on droplet:
   ```bash
   python3 causal_analysis_engine.py
   python3 query_why_analysis.py --all
   ```

2. Check if more components are now found and more patterns identified.

3. If still limited, may need to:
   - Lower thresholds further
   - Check actual attribution data structure
   - Add more context dimensions
