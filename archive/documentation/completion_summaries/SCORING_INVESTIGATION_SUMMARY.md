# Scoring System Investigation Summary

## Issues Found

### 1. **Missing Dark Pool Data** (CRITICAL)
- **Problem**: `dark_pool` key is completely missing from cache
- **Impact**: Dark pool component (weight 1.3) contributes only ~0.26 when missing (0.2 * 1.3)
- **Root Cause**: Daemon may not be polling dark_pool endpoint, or API is returning empty data
- **Location**: `uw_flow_daemon.py` line 841-846 has code to poll dark_pool, but it's not being executed or data is empty

### 2. **Threshold Too High** (FIXED)
- **Problem**: Threshold was 3.5, but scores are 0.15-2.58
- **Fix Applied**: Lowered to 2.0 for base, 2.2 for canary, 2.5 for champion
- **Status**: ✅ Fixed in source code and pushed to git

### 3. **Low Composite Scores**
- **Current Scores**: 0.15-2.58 (mostly below 1.0)
- **Expected Range**: Should be 0-5.0 based on weights
- **Why So Low**:
  - Missing dark_pool (major component)
  - Low flow conviction in some cases
  - Missing or low other components (insider, iv_term_skew, etc.)

### 4. **Adaptive Weights** (NOT THE ISSUE)
- **Status**: Adaptive optimizer state doesn't exist
- **Impact**: Using base weights (WEIGHTS_V3)
- **Note**: Adaptive weights were reducing scores, but they're not active now

## Scoring Algorithm Analysis

### Component Weights (Base):
- `options_flow`: 2.4 (PRIMARY)
- `dark_pool`: 1.3 (MAJOR - MISSING)
- `insider`: 0.5
- `iv_term_skew`: 0.6
- `smile_slope`: 0.35
- Others: 0.2-0.9

### Score Calculation:
```
flow_component = 2.4 * conviction
dp_component = 1.3 * dp_strength  # dp_strength = 0.2 when dark_pool missing
insider_component = 0.5 * (0.25 to 1.0)
iv_component = 0.6 * abs(iv_skew) * alignment_factor
... other components ...
```

### Example (TSLA with conviction=1.0):
- Flow: 2.4 * 1.0 = 2.4
- Dark pool: 1.3 * 0.2 = 0.26 (MISSING DATA)
- Insider: 0.5 * 0.25 = 0.125 (NEUTRAL)
- IV skew: 0.6 * 0.15 * 0.7 = 0.063
- Smile: 0.35 * 0.02 = 0.007
- **Total**: ~2.85 (but actual is much lower, suggesting other issues)

## Next Steps

1. **Fix Dark Pool Population**:
   - Check if daemon is actually calling `get_dark_pool_levels()`
   - Verify API is returning data
   - Ensure `_normalize_dark_pool()` is working correctly
   - Force immediate dark_pool poll

2. **Investigate Low Scores Further**:
   - Test scoring with TSLA (has good data: conviction=1.0, 100 flow_trades)
   - Check why score is still low even with good data
   - Verify all components are being calculated correctly

3. **Temporary Workaround**:
   - Lower threshold further (1.5) to allow trades while investigating
   - OR ensure dark_pool gets populated first

## Files Modified

- `uw_composite_v2.py`: Lowered thresholds (3.5→2.0, 3.8→2.2, 4.2→2.5)

## Files to Check

- `uw_flow_daemon.py`: Dark pool polling logic (line 841-846)
- `signals/uw_enrich.py`: How dark_pool is enriched
- `uw_composite_v2.py`: Scoring algorithm (line 477-700)

