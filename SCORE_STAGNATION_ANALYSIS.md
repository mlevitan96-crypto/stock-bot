# Score Stagnation & Low Scores Analysis
**Date:** 2026-01-10  
**Issue:** Stagnation alerts and very low scores observed

## Executive Summary

The stagnation alerts and low scores are likely caused by **adaptive weights reducing component weights too aggressively**, even though `options_flow` is protected. Other critical components may have their multipliers reduced, causing overall scores to drop significantly.

## Key Findings

### 1. Adaptive Weights Protection Status

**✅ Protected:**
- `options_flow` - Hardcoded to always return 2.4 (default weight) in `uw_composite_v2.py:83-85`

**⚠️ NOT Protected:**
- All other 21 components can still have adaptive multipliers applied (0.25x to 2.5x)
- If multiple components are reduced to 0.25x, this can cause significant score reduction

### 2. Adaptive Weight Application

**Current Behavior:**
- `compute_composite_score_v3()` defaults to `use_adaptive_weights=True`
- All calls in `main.py` do NOT explicitly disable adaptive weights
- All components (except `options_flow`) can be affected by adaptive learning

**Example Impact:**
If `dark_pool` (base weight 1.3) has multiplier 0.25x → effective weight = 0.325 (75% reduction)
If `iv_term_skew` (base weight 0.6) has multiplier 0.25x → effective weight = 0.15 (75% reduction)
If 5 components are reduced → total potential score reduction = 3-4 points

### 3. Stagnation Detection Thresholds

**Current Thresholds (from `logic_stagnation_detector.py`):**
- `SIGNAL_ZERO_SCORE_THRESHOLD = 20` - Triggers after 20 signals with score=0.00
- `MOMENTUM_BLOCK_THRESHOLD = 10` - Triggers after 10 consecutive momentum blocks
- `STAGNATION_ALERT_THRESHOLD = 50` - Funnel stagnation (>50 alerts, 0 trades in 30min)

### 4. Historical Context

**Previous Fixes (from `HONEST_FINAL_ASSESSMENT.md`):**
- ✅ Fixed: Flow weight learned to 0.612 instead of 2.4 → Fixed by hardcoding `options_flow`
- ✅ Fixed: Freshness decay too aggressive → Fixed by enforcing minimum 0.9
- ⚠️ Still Active: Adaptive weights reducing other components

**From `COMPLETE_BOT_REFERENCE.md`:**
- "15 components reduced by 75% (to 0.25x multiplier) due to historical poor performance"
- "Root cause: Bugs prevented components from contributing (always 0.0)"
- "Impact: Even with bugs fixed, weights remain low"

## Root Cause Analysis

### Primary Suspect: Adaptive Weights Still Reducing Scores

**Mechanism:**
1. Adaptive learning system tracks component performance
2. Components with poor historical performance get multipliers reduced to 0.25x
3. Even though `options_flow` is protected, other components can be reduced
4. Multiple reduced components → lower composite scores → stagnation alerts

**Evidence:**
- Code shows `options_flow` is hardcoded but other components are not
- Historical documentation mentions 15 components at 0.25x multiplier
- Adaptive weights are enabled by default in all score calculations

## Recommended Actions

### Immediate Actions

1. **Check Current Adaptive Weight State**
   ```bash
   # Run on droplet
   python3 comprehensive_score_diagnostic.py
   ```

2. **Verify Current Component Weights**
   - Check `state/signal_weights.json` on droplet
   - Verify which components have multipliers < 1.0
   - Calculate effective weights: `base_weight * multiplier`

3. **Temporarily Disable Adaptive Weights (if needed)**
   - Modify calls to `compute_composite_score_v3()` to pass `use_adaptive_weights=False`
   - OR: Update `get_weight()` to return default weights for all components temporarily

### Long-term Solutions

1. **Add Safety Floor to All Critical Components**
   - Similar to `options_flow` protection, add minimum weights for:
     - `dark_pool` (min 0.65 = 50% of 1.3)
     - `iv_term_skew` (min 0.30 = 50% of 0.6)
     - `whale_persistence` (min 0.35 = 50% of 0.7)
   - This prevents complete score destruction

2. **Review Adaptive Learning Data**
   - Check if weight reductions were based on buggy component behavior
   - Reset adaptive weights if they learned from incorrect data
   - Re-evaluate component performance with fixed scoring logic

3. **Add Component Contribution Monitoring**
   - Track component contributions to scores
   - Alert when component contributions drop below thresholds
   - Monitor adaptive multiplier changes

## Diagnostic Steps

### Step 1: Check Current Weights
```python
from uw_composite_v2 import get_weight, WEIGHTS_V3

regimes = ["RISK_ON", "RISK_OFF", "NEUTRAL", "mixed"]
for component in WEIGHTS_V3.keys():
    default = WEIGHTS_V3[component]
    for regime in regimes:
        current = get_weight(component, regime)
        if abs(current - default) > default * 0.1:  # >10% difference
            print(f"{component} ({regime}): default={default:.3f}, current={current:.3f}, diff={((current-default)/default*100):.1f}%")
```

### Step 2: Check Recent Scores
- Review `state/logic_stagnation_state.json` for stagnation history
- Review `logs/trading.log` for recent score calculations
- Check dashboard for score distribution

### Step 3: Test Score Calculation
```python
# Test with sample data
from uw_composite_v2 import compute_composite_score_v3
# ... load enriched data from cache
result = compute_composite_score_v3(symbol, enriched, "mixed", use_adaptive_weights=False)
# Compare with use_adaptive_weights=True
```

## Files to Review

1. **`uw_composite_v2.py`** - Weight accessor and scoring logic
2. **`state/signal_weights.json`** - Current adaptive weight state
3. **`logic_stagnation_detector.py`** - Stagnation detection logic
4. **`adaptive_signal_optimizer.py`** - Adaptive learning system
5. **`main.py`** - Where scores are calculated (lines 7460, 5455, 4809, etc.)

## Next Steps

1. ✅ Review this analysis
2. ⏳ Run diagnostic on droplet to check current state
3. ⏳ Verify adaptive weight multipliers
4. ⏳ Determine if weights need reset or protection
5. ⏳ Implement fixes if needed
