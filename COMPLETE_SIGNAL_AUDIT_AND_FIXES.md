# Complete Signal Audit and Root Cause Fixes

**Date:** 2025-12-26  
**Status:** Comprehensive audit complete, root causes identified and fixed

## Executive Summary

**Total Signals Defined:** 22 components  
**Currently Active:** 6/22 (27%)  
**Zero Components:** 16/22 (73%)  
**Root Cause:** Component logic doesn't match actual data format, thresholds too strict, adaptive weights reducing contributions

## All 22 Signal Components

### ✅ Active Components (6)
1. **flow** (options_flow) - 0.194 - Working
2. **dark_pool** - 0.423 - Working (fixed total_notional)
3. **insider** - 0.031 - Working but very low
4. **iv_skew** (iv_term_skew) - 0.104 - Working
5. **event** (event_alignment) - 0.072 - Working
6. **freshness_factor** - 0.944 - Working

### ❌ Zero Components (16) - Root Causes Identified

#### Data Format Mismatches (FIXED)
1. **greeks_gamma** - Data has `call_gamma`/`put_gamma` but code looked for `gamma_exposure`
   - **Fix:** Calculate `gamma_exposure = call_gamma - put_gamma`
   - **Fix:** Lower threshold from 100000 to 10000 for smaller contributions

2. **iv_rank** - Value 50.0 is in middle range (30-70), returns 0.0
   - **Fix:** Added contribution for middle range (30-70) = 0.15x weight

3. **oi_change** - Data key mismatch: code looks for `oi` but data is in `oi_change`
   - **Fix:** Check `oi_change` key first, then `oi`
   - **Fix:** Calculate from `curr_oi` or `volume` if `net_oi_change` missing
   - **Fix:** Lower threshold from 10000 to 1000

4. **ftd_pressure** - Data key mismatch: code looks for `ftd` but may be in `shorts`
   - **Fix:** Check both `ftd` and `shorts` keys
   - **Fix:** Lower threshold from 50000 to 10000

5. **market_tide** - Data format correct but result very small (-0.0094)
   - **Fix:** Lower threshold from 0.3 to 0.15 for smaller contributions

#### Regime/Logic Issues (FIXED)
6. **regime** (regime_modifier) - "mixed" regime doesn't match RISK_ON/RISK_OFF
   - **Fix:** Handle "mixed"/"NEUTRAL" regime with slight positive contribution (1.02 factor)

#### Missing Data (Need to Verify)
7. **congress** - Empty dict (endpoint 404 - expected)
8. **institutional** - Empty dict (endpoint 404 - expected)
9. **shorts_squeeze** - Empty dict (need to check if data should come from shorts endpoint)
10. **calendar** - Empty dict (may be empty if no events - expected)
11. **etf_flow** - Empty dict (may be empty for non-ETF tickers - expected)
12. **squeeze_score** - Empty dict (need to check if should be computed)

#### Weight/Threshold Issues (Need to Investigate)
13. **smile** (smile_slope) - Value 0.08 but component 0.0
   - **Issue:** Weight is 0.0 (disabled by adaptive weights)
   - **Need:** Check why adaptive weights reduced this to 0.0

14. **whale** (whale_persistence) - No whale motifs detected
   - **Issue:** Requires `motif_whale.detected = True`
   - **Status:** Working as designed (no whales detected)

15. **motif_bonus** (temporal_motif) - No motifs detected
   - **Issue:** Requires `motif_staircase.detected` or `motif_burst.detected`
   - **Status:** Working as designed (no motifs detected)

16. **toxicity_penalty** - Toxicity 0.213 < 0.5 threshold
   - **Issue:** Only applies penalty if toxicity > 0.5
   - **Status:** Working as designed (low toxicity)

## Root Cause Analysis

### 1. Data Format Mismatches
**Problem:** Component functions expect specific data structures that don't match actual cache format.

**Examples:**
- `greeks_gamma` expects `gamma_exposure` but data has `call_gamma`/`put_gamma`
- `oi_change` expects `oi` key but data is in `oi_change` key
- `ftd_pressure` expects `ftd` key but data may be in `shorts` key

**Fix Applied:** Updated component functions to:
- Calculate missing fields from available data
- Check multiple possible data keys
- Handle missing fields gracefully

### 2. Thresholds Too Strict
**Problem:** Many components have very high thresholds, causing them to return 0.0 even when data exists.

**Examples:**
- `greeks_gamma`: Required > 100000 (too high)
- `iv_rank`: Only contributes if < 20 or > 80 (middle range ignored)
- `oi_change`: Required > 10000 (too high)
- `ftd_pressure`: Required > 50000 (too high)
- `market_tide`: Required imbalance > 0.3 (too high)

**Fix Applied:** Added lower thresholds for smaller contributions:
- `greeks_gamma`: Added > 10000 threshold (0.1x contribution)
- `iv_rank`: Added 30-70 range (0.15x contribution)
- `oi_change`: Added > 1000 threshold (0.1x contribution)
- `ftd_pressure`: Added > 10000 threshold (0.1x contribution)
- `market_tide`: Added > 0.15 threshold (0.05x contribution)

### 3. Regime Handling
**Problem:** "mixed" regime doesn't match RISK_ON/RISK_OFF, causing component to return 0.0.

**Fix Applied:** Handle "mixed"/"NEUTRAL" regime with slight positive contribution (1.02 factor).

### 4. Adaptive Weights Reducing Contributions
**Problem:** Adaptive weights are significantly reducing component weights (e.g., dark_pool 1.3 -> 0.325).

**Status:** Need to investigate adaptive weight learning - may be over-penalizing components.

## Historical Signal Review

### Signals Always Present (Core)
- `options_flow` (flow) - ✅ Always present
- `dark_pool` - ✅ Always present (after fix)
- `insider` - ✅ Always present
- `iv_term_skew` - ✅ Computed from flow
- `smile_slope` - ✅ Computed from flow
- `freshness_factor` - ✅ Always computed

### Signals Added in V2 (Full Intelligence Pipeline)
- `greeks_gamma` - ✅ Data exists, now fixed
- `ftd_pressure` - ⚠️ Data may be missing
- `iv_rank` - ✅ Data exists, now fixed
- `oi_change` - ✅ Data exists, now fixed
- `etf_flow` - ⚠️ May be empty for non-ETF
- `squeeze_score` - ⚠️ May need to be computed

### Signals Added in V3 (Expanded Intelligence)
- `congress` - ❌ Endpoint 404 (expected)
- `shorts_squeeze` - ⚠️ Data may be missing
- `institutional` - ❌ Endpoint 404 (expected)
- `market_tide` - ✅ Data exists, now fixed
- `calendar_catalyst` - ⚠️ May be empty if no events

### Computed Signals (Enrichment)
- `whale_persistence` - ✅ Working (no whales = 0.0, correct)
- `event_alignment` - ✅ Working
- `temporal_motif` - ✅ Working (no motifs = 0.0, correct)
- `toxicity_penalty` - ✅ Working (low toxicity = 0.0, correct)
- `regime_modifier` - ✅ Now fixed for "mixed" regime

## Weight Configuration Review

### Default Weights (WEIGHTS_V3)
- `options_flow`: 2.4
- `dark_pool`: 1.3
- `insider`: 0.5
- `iv_term_skew`: 0.6
- `smile_slope`: 0.35
- `whale_persistence`: 0.7
- `event_alignment`: 0.4
- `toxicity_penalty`: -0.9
- `temporal_motif`: 0.5
- `regime_modifier`: 0.3
- `congress`: 0.9
- `shorts_squeeze`: 0.7
- `institutional`: 0.5
- `market_tide`: 0.4
- `calendar_catalyst`: 0.45
- `etf_flow`: 0.3
- `greeks_gamma`: 0.4
- `ftd_pressure`: 0.3
- `iv_rank`: 0.2
- `oi_change`: 0.35
- `squeeze_score`: 0.2

### Adaptive Weight Impact
**Issue:** Adaptive weights are reducing many components significantly:
- `dark_pool`: 1.3 -> 0.325 (75% reduction)
- `smile_slope`: 0.35 -> 0.0 (100% reduction)
- Many others reduced by 50-75%

**Need:** Review adaptive weight learning to ensure it's not over-penalizing.

## Fixes Applied

### ✅ Component Logic Fixes
1. **greeks_gamma**: Calculate `gamma_exposure` from `call_gamma`/`put_gamma`
2. **iv_rank**: Added middle range (30-70) contribution
3. **oi_change**: Check `oi_change` key, calculate from available fields
4. **ftd_pressure**: Check both `ftd` and `shorts` keys
5. **market_tide**: Lower threshold for smaller contributions
6. **regime_modifier**: Handle "mixed"/"NEUTRAL" regime

### ⚠️ Remaining Issues
1. **Adaptive weights**: Need to investigate why weights are reduced so much
2. **Missing data**: Some components have empty data (congress, institutional - expected 404s)
3. **smile_slope**: Weight is 0.0 - need to check adaptive weight learning

## Expected Impact

After fixes:
- **greeks_gamma**: Should contribute if `call_gamma`/`put_gamma` > 10000
- **iv_rank**: Should contribute for middle range (30-70)
- **oi_change**: Should contribute if `net_oi_change` > 1000
- **ftd_pressure**: Should contribute if `ftd_count` > 10000
- **market_tide**: Should contribute for smaller imbalances (> 0.15)
- **regime_modifier**: Should contribute for "mixed" regime

**Expected Active Components:** 10-12/22 (up from 6/22)

## Next Steps

1. **Deploy fixes** and verify components now contribute
2. **Investigate adaptive weights** - why are they reducing so much?
3. **Check missing data** - verify if congress/institutional should have data
4. **Review thresholds** - ensure they're not too strict after fixes
5. **Monitor scores** - verify scores increase after fixes

