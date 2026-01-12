# Score Stagnation Investigation Results - Complete Analysis

**Date:** 2026-01-12  
**Status:** ✅ Root Cause Confirmed

## Executive Summary

**PROBLEM CONFIRMED:** 19 out of 20 components have adaptive weights reduced by **74.4%** (to 0.25x multiplier), causing scores to drop below trading thresholds.

## Key Findings

### 1. Adaptive Weights Catastrophic Reduction ⚠️

**19 Components Reduced by 74.4%:**
- All components (except `options_flow`) reduced to ~0.25x multiplier
- **Total score reduction: ~6.9 points** (from potential ~10.5 points to ~3.6 points)
- Only `options_flow` protected (confirmed at 2.4)

**Examples:**
- `dark_pool`: 1.3 → 0.333 (-74.4%)
- `iv_term_skew`: 0.6 → 0.154 (-74.4%)
- `whale_persistence`: 0.7 → 0.180 (-74.4%)
- `congress`: 0.9 → 0.231 (-74.4%)

### 2. Score Distribution - All Below Threshold

**Current Scores:**
- Average: **1.232** (below 2.7 threshold)
- Median: **0.799** (extremely low)
- Max: **2.595** (still below 2.7)
- 60% of symbols below 1.0
- 100% of symbols below 2.7 threshold

**This explains why no trades are executing!**

### 3. Stagnation Metrics

**Funnel Stagnation:**
- **137 funnel stagnation detections** (massive!)
- 8 zero score detections
- 8 soft resets triggered (but not fixing the issue)

**Signal Funnel:**
- Total alerts: 114,376
- Total orders: **0** (ZERO!)
- Conversion rate: 0.0% (alerts → orders)
- 8.1% alerts → scored, but all below threshold

### 4. Component Contribution Analysis

**Components NOT Contributing (100% zero):**
- `institutional` - 100% zero
- `motif_bonus` - 100% zero  
- `whale` - 100% zero

**Components Partially Contributing:**
- `iv_skew` - 80% zero (only contributing 20% of the time)
- `smile` - 75% zero (only contributing 25% of the time)

**This indicates:**
- Some components don't have data (institutional, whale, motif)
- Some components rarely contribute (iv_skew, smile)

## Root Cause Analysis

### Why This Happened

1. **Adaptive Learning Learned Bad Weights**
   - System reduced weights based on poor historical performance
   - Historical performance was bad because components weren't contributing (bugs)
   - Even after bugs fixed, weights remained low

2. **No Safety Floors**
   - Only `options_flow` has protection (hardcoded)
   - Other components can be reduced to 0.25x (minimum)
   - No recovery mechanism when weights learned from bad data

3. **Cascade Effect**
   - Multiple reduced components → massive score reduction
   - Scores too low → no trades → no learning feedback
   - System stuck in low-score state

## Impact Calculation

**Before Reduction (theoretical):**
- Base weights total: ~10.5 points potential
- With typical signal strength: ~4-6 points actual scores

**After Reduction (current):**
- Effective weights total: ~3.6 points potential
- With typical signal strength: ~1-2 points actual scores
- **Score drop: ~3-4 points** (explains stagnation)

## Solution

### Immediate Fix: Reset Adaptive Weights

**Action:** Reset all component multipliers to 1.0 (neutral)

**Script:** `FIX_ADAPTIVE_WEIGHTS_REDUCTION.py`

This will:
1. Reset all weight multipliers from 0.25x → 1.0x
2. Reset regime beta distributions to defaults
3. Create backup before changes
4. Preserve weight structure

### Expected Results After Fix

**Score Improvement:**
- Scores should increase by ~3-4 points
- Average score: 1.2 → **4-5** (above 2.7 threshold)
- Median score: 0.8 → **3-4**

**Trading Activity:**
- Signals should start clearing 2.7 threshold
- Orders should start executing
- Stagnation alerts should decrease

### Long-term Safeguards

1. **Add Safety Floors** (similar to options_flow protection)
   - Critical components: min 0.5x multiplier (50% of default)
   - Prevents complete score destruction

2. **Monitor Weight Changes**
   - Alert when weights drop below 0.8x
   - Track weight reduction patterns
   - Auto-recover if multiple components reduced

3. **Reset Mechanism**
   - Automatic reset if >5 components at 0.25x
   - Reset after major bug fixes
   - Manual reset capability

## About Stashed Files

The stashed files were likely diagnostic/troubleshooting scripts:
- `check_current_trading_status.py`
- `check_latest_activity.py`
- `check_positions_and_signals.py`
- `check_worker_status.py`
- `dashboard.py` (may have local changes)
- `investigate_score_bug.py`

**Recommendation:**
- Review stashed changes: `git stash list`
- Apply selectively if needed: `git stash pop` or `git stash show -p`
- Most important: Fix the weights issue first
- Dashboard changes can be reviewed separately

## Next Steps

1. ✅ **Run Fix Script**
   ```bash
   cd /root/stock-bot
   python3 FIX_ADAPTIVE_WEIGHTS_REDUCTION.py
   ```

2. ✅ **Restart Bot Service**
   ```bash
   sudo systemctl restart stockbot
   ```

3. ✅ **Monitor Results**
   - Check scores improve
   - Monitor for trading activity
   - Verify stagnation alerts decrease

4. ⏳ **Review Stashed Files** (after weights fixed)
   - Check if dashboard changes needed
   - Review diagnostic scripts
   - Merge selectively if important

## Files to Review

1. **FIX_ADAPTIVE_WEIGHTS_REDUCTION.py** - Weight reset script
2. **state/signal_weights.json** - Current weight state (will be fixed)
3. **state/signal_weights.backup.*.json** - Backup created before fix

---

**Status:** Ready to fix - Run `FIX_ADAPTIVE_WEIGHTS_REDUCTION.py` on droplet
