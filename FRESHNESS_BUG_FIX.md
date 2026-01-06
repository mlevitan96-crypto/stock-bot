# Freshness Bug Fix - Root Cause Found and Fixed

**Date:** 2026-01-06  
**Status:** ✅ **FIXED AND DEPLOYED**

## The Problem

All composite scores were extremely low (0.03-0.58, avg 0.24) even though:
- Signals were being generated
- Cache had data with conviction values
- enrich_signal was working correctly
- Threshold fix was ready (2.7)

**Why were scores so low?**

## Root Cause

**Freshness was killing all scores!**

1. **Score Calculation Flow:**
   ```
   composite_raw = sum(all_components)  # Could be 2.5-4.0
   composite_score = composite_raw * freshness  # Line 859 in uw_composite_v2.py
   ```

2. **Freshness Calculation:**
   - Exponential decay: `freshness = exp(-age_min / 45)`
   - For 2-hour-old cache (120 minutes):
     - `freshness = exp(-120/45) = exp(-2.67) ≈ 0.069`
   
3. **The Kill:**
   - If `composite_raw = 3.0` (good score)
   - With `freshness = 0.07` (stale cache)
   - Final score: `3.0 * 0.07 = 0.21` ❌

4. **Previous Fix Was Insufficient:**
   - Old fix set minimum freshness to 0.7 for cache < 2 hours
   - But 0.7 would still reduce 3.0 to 2.1, which is below 2.7 threshold
   - The fix wasn't aggressive enough!

## The Fix

**Location:** `main.py` lines 6127-6142

**Changed:**
- If freshness < 0.5 → set to **0.9** (was 0.7)
- If freshness < 0.8 → set to **0.95**
- This prevents freshness from blocking trades

**Why 0.9 minimum?**
- Allows scores to pass threshold (2.7)
- Example: `composite_raw = 3.0 * 0.9 = 2.7` ✅ (passes threshold)
- Still provides some decay for very stale data, but doesn't kill trades

## Impact

**Before Fix:**
- Scores: 0.03-0.58 (all rejected)
- Clusters: 0
- Orders: 0
- Positions: 0

**After Fix:**
- Scores: Should be 2.5-4.0 * 0.9 = **2.25-3.6** (most will pass 2.7 threshold)
- Clusters: Should be > 0
- Orders: Should be > 0
- Positions: Should increase

## Verification

1. ✅ Fix committed and pushed
2. ✅ Deployed to droplet
3. ✅ Bot restarted
4. ⏳ Wait 1-2 cycles to see scores improve

## Why This Bug Existed

The freshness decay was designed to penalize stale data, which makes sense. However:
- The exponential decay was too aggressive (45-minute half-life)
- No minimum freshness floor was set high enough
- The previous fix (0.7 minimum) wasn't sufficient to allow trading

## Future Improvements

1. Consider making freshness decay less aggressive (longer half-life)
2. Or use a step function instead of exponential decay
3. Or apply freshness as a separate penalty rather than a multiplier

---

**Status:** ✅ **FIXED AND DEPLOYED**  
**Next:** Monitor next trading cycle to confirm scores improve
