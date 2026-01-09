# Forensic Signal Interrogation Results

**Date**: 2026-01-09  
**Issue**: 530 alerts but 0 trades - system blind or over-filtering  
**Diagnostic**: Deep trace on next 10 incoming alerts

---

## Executive Summary

The forensic interrogation identified **TWO PRIMARY BLOCKING GATES** preventing trades:

1. **Momentum Gate (ATR Exhaustion)**: Blocking 6 out of 10 symbols
   - Threshold: 0.01% (1 basis point) price movement in 2 minutes
   - Most symbols showing negative or near-zero price movement
   - This is the **PRIMARY CULPRIT** for stagnation

2. **Score Gate**: Blocking ALL 10 symbols
   - Threshold: 2.7 (base entry threshold)
   - All traced symbols scored below 2.7 (range: 0.25 - 2.54)
   - AAPL came closest at 2.54 (just 0.16 below threshold)

---

## Detailed Findings

### Step 1: Enrichment Pipeline Trace ✅

**Status**: **WORKING CORRECTLY**

- ✅ No field name mismatches found
- ✅ All expected fields present in raw cache data
- ✅ Enrichment successful for all symbols (33-34 fields enriched)
- ✅ No "0.00 score" bug detected

**Key Fields Verified**:
- `sentiment`: Present ✓
- `conviction`: Present ✓
- `dark_pool`: Present (most symbols) ✓
- `insider`: Present ✓
- `iv_term_skew`: Present ✓
- `smile_slope`: Present ✓

**Missing Fields (Computed by Enrichment)**:
- `toxicity`: Computed on-the-fly ✓
- `event_alignment`: Computed on-the-fly ✓
- `freshness`: Computed on-the-fly ✓
- `motif_*`: Computed on-the-fly ✓

**Conclusion**: Enrichment pipeline is healthy. No field name mismatches causing 0.00 scores.

---

### Step 2: ATR Exhaustion Gate (Momentum Filter) ⚠️

**Status**: **PRIMARY BLOCKER**

The momentum filter requires **0.01% (1 basis point) price movement in 2 minutes** before allowing entry.

**Results from 10 Symbols**:
- **6 BLOCKED** by momentum gate:
  - TSLA: -0.0002% (needs +0.01%)
  - AAPL: -0.0019% (needs +0.01%)
  - AMZN: -0.0111% (needs +0.01%)
  - META: +0.0023% (needs +0.01%)
  - NVDA: 0.0000% (needs +0.01%)
  - (Additional symbols in full trace)

- **4 PASSED** momentum gate:
  - MSFT: +0.0189% ✓
  - GOOGL: +0.0349% ✓
  - (Additional symbols in full trace)

**Analysis**:
- During low volatility periods, price movement < 0.01% is common
- The 0.01% threshold (1 basis point) may be **too tight for opening volatility**
- Current market conditions show minimal price movement (< 0.01% in 2 minutes)

**Recommendation**:
- Consider lowering threshold to 0.005% (0.5 basis points) during low volatility
- Or implement dynamic threshold based on VIX/volatility regime
- The filter already has soft-fail mode for scores > 4.0, but no symbols reached that threshold

---

### Step 3: Score Consistency Audit ✅

**Status**: **CONSISTENT**

- ✅ Entry scoring and current score calculation use **same function**: `compute_composite_score_v3()`
- ✅ Version: V3.1 (with adaptive weights)
- ✅ No version mismatch detected
- ✅ Score differences: 0.000 (perfectly consistent)

**Conclusion**: Dashboard and bot are "speaking the same language". No phantom stagnations from score version mismatch.

---

## Last 5 Blocked Symbols (by Score, Lowest First)

| Symbol | Score | Blocking Gate(s) | Momentum | Enrichment |
|--------|-------|------------------|----------|------------|
| TSLA   | 0.251 | Score Gate + Momentum Gate + Freshness Gate | BLOCKED | OK |
| GOOGL  | 0.270 | Score Gate + Freshness Gate | OK | OK |
| MSFT   | 0.715 | Score Gate | OK | OK |
| AMZN   | 0.930 | Score Gate + Momentum Gate | BLOCKED | OK |
| META   | 1.105 | Score Gate + Momentum Gate | BLOCKED | OK |

**Note**: AAPL scored 2.54 (closest to threshold) but was blocked by:
- Score Gate (2.54 < 2.7)
- Momentum Gate (insufficient bullish momentum)

---

## Statistics Summary

**Total Traced**: 10 symbols

**Blocking Gates Breakdown**:
- **Blocked by Score**: 10/10 (100%) - ALL symbols below 2.7 threshold
- **Blocked by Momentum**: 6/10 (60%) - Price movement < 0.01%
- **Blocked by Toxicity**: 0/10 (0%)
- **Blocked by Freshness**: 2/10 (20%) - Stale data (freshness < 0.3)
- **Blocked by Conviction**: 0/10 (0%)

---

## Root Cause Analysis

### Primary Issue: **Dual Gate Blocking**

1. **Score Gate**: All symbols scoring below 2.7 threshold
   - Highest score: AAPL at 2.54 (0.16 below threshold)
   - This suggests signals are weak OR threshold is too high

2. **Momentum Gate**: 60% of symbols blocked by insufficient price movement
   - Threshold: 0.01% (1 basis point) in 2 minutes
   - During low volatility, this threshold is difficult to meet
   - Even symbols with good scores (e.g., AAPL at 2.54) are blocked

### Secondary Issue: **Stale Data**

- 2 symbols (TSLA, GOOGL) have freshness < 0.3
- This suggests cache update frequency may need review

---

## Recommendations

### Immediate Actions (No Threshold Changes)

1. **Add Detailed Logging to Momentum Filter**
   - Log exact math: `Price ({price}) change is {change_pct}%, threshold is {threshold}%`
   - This will help diagnose if threshold is appropriate for current volatility

2. **Monitor Score Distribution**
   - Track how many signals score 2.5-2.7 (just below threshold)
   - If many signals cluster just below 2.7, consider adaptive threshold

3. **Review Cache Freshness**
   - Investigate why some symbols have freshness < 0.3
   - Ensure cache update service is running correctly

### Future Considerations (Requires Threshold Changes)

1. **Dynamic Momentum Threshold**
   - Scale threshold based on VIX or realized volatility
   - Lower threshold (0.005%) during low volatility periods
   - Higher threshold (0.02%) during high volatility

2. **Adaptive Score Threshold**
   - Lower threshold if many signals score 2.5-2.7
   - Use learning system to optimize threshold based on outcomes

---

## Files Created

1. `FORENSIC_SIGNAL_INTERROGATION.py` - Main diagnostic script
2. `RUN_FORENSIC_ON_DROPLET.py` - Remote execution wrapper
3. `data/forensic_interrogation_results.json` - Detailed results (on droplet)

---

## Next Steps

1. ✅ **COMPLETE**: Forensic interrogation performed
2. ⏳ **PENDING**: Review momentum filter threshold appropriateness
3. ⏳ **PENDING**: Add detailed logging to momentum filter (as requested)
4. ⏳ **PENDING**: Monitor next batch of alerts to confirm findings

---

**Conclusion**: The system is **NOT blind** - enrichment pipeline works correctly. The issue is **over-filtering** by:
1. Score threshold (2.7) - all symbols below threshold
2. Momentum filter (0.01%) - 60% blocked by insufficient price movement

The momentum filter is the **PRIMARY CULPRIT** for the stagnation, especially during low volatility periods.
