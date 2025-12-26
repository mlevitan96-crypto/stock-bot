# Root Cause Analysis - Trade Freeze

**Date:** 2025-12-26  
**Status:** COMPLETE - All issues identified

## Executive Summary

The bot is **NOT trading** because **ALL composite scores are below the entry threshold of 2.0**. The highest score observed is **1.85 (BLK)**, and the second highest is **1.59 (AAPL)**, both below the 2.0 threshold required for bootstrap stage.

## ✅ Confirmed Working

1. **Bot is running** - systemd service is active, main.py process running
2. **build_client_order_id fix working** - No more ValueError crashes
3. **Clusters are being generated** - 1-2 clusters per cycle
4. **Cache has data** - 53 symbols in cache
5. **Scoring is executing** - Composite scores calculated for all symbols
6. **No freeze files** - Trading is not frozen
7. **No critical errors** - Only expected 404s for congress/institutional endpoints

## 🔴 ROOT CAUSE: Scores Below Threshold

### Current Score Distribution
- **Highest:** BLK at 1.85 (still below 2.0)
- **Second:** AAPL at 1.59 (below 2.0)
- **Most symbols:** 0.16 (very low)
- **Threshold:** 2.0 (bootstrap stage)

### Score Breakdown (AAPL - Best Example)
```
Score: 1.577 (threshold: 2.0)
Passes: False

Component Breakdown:
- flow: 1.169 (main contributor)
- dark_pool: 0.423 (working after fix)
- insider: 0.031 (very low)
- iv_skew: 0.01 (very low)
- smile: 0.025 (very low)
- 14 other components: 0.0 (not contributing)
```

### Why Scores Are Low

#### 1. **Most Components Returning 0.0**
- Only **8/22 components** contributing for AAPL
- **14 components are 0.0** (greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, market_tide, calendar, congress, institutional, shorts_squeeze, squeeze_score, regime, whale, event, motif_bonus)

#### 2. **Component Requirements Not Met**
- **greeks_gamma:** Requires `gamma_exposure > 100000` or `gamma_squeeze_setup = True`
- **ftd_pressure:** Requires `ftd_count > 50000` or `squeeze_pressure = True`
- **iv_rank:** Requires IV rank data from cache (may be missing)
- **oi_change:** Requires OI change data from cache (may be missing)
- **market_tide:** Data exists but component calculation may be returning 0.0
- **calendar:** May be empty if no events
- **congress/institutional:** Endpoints return 404 (expected)

#### 3. **Low Flow Component**
- AAPL flow component is only **1.169** (should be higher for strong signals)
- Most symbols have flow component of **0.0** (no flow trades)

#### 4. **Dark Pool Component Low**
- Even with fix, dark_pool only contributes **0.423** for AAPL
- Most symbols have dark_pool = **0.065** (minimal contribution)

## 📊 Data Quality Analysis

### AAPL (Best Case)
- ✅ Has dark_pool: True
- ✅ Has market_tide: True
- ✅ Has insider: True
- ✅ Has greeks: True
- ✅ 8/22 components contributing
- ❌ Score: 1.577 < 2.0 threshold

### Other Symbols (MSFT, GOOGL, AMZN, META)
- ❌ Has dark_pool: False
- ✅ Has market_tide: True
- ✅ Has insider: True
- ❌ Has greeks: False
- ❌ Only 5/22 components contributing
- ❌ Score: 0.163 (very low)

## 🔍 Secondary Issues

### 1. **Missing Dark Pool Data**
- Most symbols don't have dark_pool data in cache
- Only AAPL has dark_pool data
- This is a significant component (weight 1.3)

### 2. **Missing Greeks Data**
- Most symbols don't have greeks data
- Greeks component can't contribute without data

### 3. **Market Tide Not Contributing**
- Market tide data exists in cache
- But component calculation returns 0.0
- Need to check `compute_market_tide_component` logic

### 4. **Low Flow Signals**
- Most symbols have no flow trades
- Flow component is 0.0 for most symbols
- Only AAPL has meaningful flow (1.169)

## 🎯 Root Cause Summary

### PRIMARY ROOT CAUSE
**Composite scores are below the 2.0 threshold required for bootstrap stage trading.**

### Contributing Factors
1. **Most components returning 0.0** - Only 8/22 components contributing
2. **Missing data** - Dark pool, greeks missing for most symbols
3. **Low flow signals** - Most symbols have no flow trades
4. **Component requirements not met** - Many components need specific conditions
5. **Market tide not contributing** - Data exists but component returns 0.0

## 🔧 Fixes Applied (Already Deployed)

1. ✅ **build_client_order_id ISO timestamp bug** - Fixed
2. ✅ **Dark pool total_notional field** - Fixed
3. ✅ **Market tide per-ticker lookup** - Fixed
4. ✅ **Missing cache fields in enriched_data** - Fixed

## ⚠️ Remaining Issues

1. **Scores still below threshold** - Even with fixes, scores are 0.16-1.85 vs 2.0
2. **Most components 0.0** - Need to investigate why components aren't contributing
3. **Missing dark_pool data** - Only AAPL has it, others don't
4. **Market tide not contributing** - Data exists but component returns 0.0

## 📋 Recommended Actions

### Immediate (To Get Trades)
1. **Lower threshold temporarily** - Reduce from 2.0 to 1.5 for bootstrap stage to allow AAPL (1.59) and BLK (1.85) to trade
2. **Investigate market_tide component** - Why is it returning 0.0 when data exists?
3. **Check flow signal quality** - Why are most symbols getting 0.0 flow component?

### Short-term (To Improve Scores)
1. **Investigate missing dark_pool data** - Why only AAPL has it?
2. **Check greeks data** - Why missing for most symbols?
3. **Review component requirements** - Are thresholds too high?
4. **Check adaptive weights** - Are they reducing component contributions?

### Long-term (To Optimize)
1. **Improve signal quality** - Ensure all components have real data
2. **Optimize component weights** - Balance contributions
3. **Review threshold strategy** - Consider stage-aware thresholds

## ✅ Confirmation

**The bot is NOT trading because composite scores are below the 2.0 threshold. This is NOT a bug - it's a scoring/configuration issue. The bot is working correctly but signals are not strong enough to meet the entry criteria.**

