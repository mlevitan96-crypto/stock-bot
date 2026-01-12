# Score Pipeline Audit - Executive Summary

## Quick Reference

**Date:** 2026-01-10  
**Issue:** All scores are extremely low  
**Root Causes Identified:** 10 critical issues

---

## Critical Findings

### 🔴 CRITICAL: Freshness Decay Too Aggressive
- **Location:** `uw_enrichment_v2.py:245`, `uw_composite_v2.py:869`
- **Issue:** `freshness = exp(-age_min / 45)` decays to 0.5 after 45 minutes
- **Impact:** Final score = `composite_raw * freshness` → 50-90% reduction
- **Fix:** Increase `decay_min` from 45 to 180 minutes

### 🔴 CRITICAL: Missing Expanded Intel Data
- **Location:** `uw_composite_v2.py:545-548`
- **Issue:** 11 V3 components return 0.0 if `expanded_intel` is empty
- **Impact:** Potential 4.0 points lost (congress, shorts, institutional, tide, calendar, greeks, ftd, iv_rank, oi_change, etf_flow, squeeze_score)
- **Fix:** Provide neutral defaults for missing data

### 🟠 HIGH: Missing Core Signal Features
- **Location:** `uw_composite_v2.py:565-569`
- **Issue:** `iv_term_skew`, `smile_slope`, `event_alignment` default to 0.0
- **Impact:** Potential 1.35 points lost (0.6 + 0.35 + 0.4)
- **Fix:** Ensure enrichment always computes these features

### 🟠 HIGH: Missing Flow Conviction
- **Location:** `uw_composite_v2.py:552`
- **Issue:** `flow_conv` defaults to 0.0 if missing
- **Impact:** Primary component (weight 2.4) = 0.0
- **Fix:** Default to 0.5 (neutral) instead of 0.0

### 🟡 MEDIUM: Neutral Sentiment Defaults
- **Location:** `uw_composite_v2.py:605-624`
- **Issue:** Dark pool and insider contribute minimally when sentiment is NEUTRAL
- **Impact:** Components reduced by 50-75%

---

## Score Calculation Formula

```
composite_raw = (
    flow_component +           # 2.4 * flow_conv (0.0 if missing)
    dp_component +             # 1.3 * dp_strength (0.26 if neutral)
    insider_component +        # 0.5 * (0.25-0.75) (0.125 if neutral)
    iv_component +             # 0.6 * abs(iv_skew) (0.0 if missing)
    smile_component +          # 0.35 * abs(smile_slope) (0.0 if missing)
    whale_score +              # 0.7 * avg_conv (0.0 if not detected)
    event_component +          # 0.4 * event_align (0.0 if missing)
    motif_bonus +              # 0.6 * motif_strength (0.0 if not detected)
    toxicity_component +       # -0.9 * (toxicity - 0.5) (0.0 if toxicity <= 0.5)
    regime_component +         # 0.3 * (regime_factor - 1.0) * 2.0 (~0.012 if mixed)
    # V3 expanded (11 components, all 0.0 if data missing)
    congress_component +       # 0.9 * strength (0.0 if missing)
    shorts_component +         # 0.7 * strength (0.0 if missing)
    inst_component +          # 0.5 * strength (0.0 if missing)
    tide_component +           # 0.4 * strength (0.0 if missing)
    calendar_component +       # 0.45 * strength (0.0 if missing)
    greeks_gamma_component +   # 0.4 * strength (0.0 if missing)
    ftd_pressure_component +   # 0.3 * strength (0.0 if missing)
    iv_rank_component +        # 0.2 * strength (0.0 if missing, or 0.15 if default 50)
    oi_change_component +      # 0.35 * strength (0.0 if missing)
    etf_flow_component +       # 0.3 * strength (0.0 if missing)
    squeeze_score_component    # 0.2 * strength (0.0 if missing)
)

composite_score = composite_raw * freshness  # ⚠️ CRITICAL: Can reduce by 50-90%
composite_score += whale_conviction_boost   # +0.5 if whale detected
composite_score = max(0.0, min(8.0, composite_score))  # Clamp to 0-8
```

**Typical Score Breakdown (with missing data):**
- Flow (if conviction=0.3): 0.72
- Dark pool (neutral): 0.26
- Insider (neutral): 0.125
- Regime (mixed): 0.012
- **Subtotal:** ~1.1
- **After freshness (0.25):** ~0.28
- **After whale boost (+0.5):** ~0.78
- **Final:** ~0.78 (well below 2.7 threshold)

**Typical Score Breakdown (with all data):**
- Flow (conviction=0.7): 1.68
- Dark pool (bullish): 0.65
- Insider (bullish): 0.375
- IV skew (0.1): 0.078
- Smile slope (0.08): 0.028
- Event alignment (0.8): 0.32
- Regime (mixed): 0.012
- V3 expanded (if available): +2.0-4.0
- **Subtotal:** ~5.0-7.0
- **After freshness (0.9):** ~4.5-6.3
- **After whale boost (+0.5):** ~5.0-6.8
- **Final:** ~5.0-6.8 (above 2.7 threshold)

---

## Immediate Action Items

1. **Fix freshness decay** (Priority 1)
   - Change `decay_min` from 45 to 180 in `uw_enrichment_v2.py:234`
   - Or remove freshness multiplication from final score

2. **Default flow conviction to 0.5** (Priority 2)
   - Change `flow_conv = _to_num(enriched_data.get("conviction", 0.5))` in `uw_composite_v2.py:552`

3. **Ensure core features are computed** (Priority 3)
   - Verify `main.py:7395-7407` always computes iv_skew, smile_slope, event_align
   - Add validation to ensure they're never None

4. **Provide defaults for missing expanded intel** (Priority 4)
   - Modify component functions to return small neutral contributions instead of 0.0
   - Or reduce weights for frequently missing components

5. **Run diagnostic script** (Priority 5)
   - Execute `python3 diagnose_score_pipeline.py --symbol all`
   - Review report to identify which symbols have which issues

---

## Files to Review

- `uw_composite_v2.py` - Composite scoring logic
- `uw_enrichment_v2.py` - Feature enrichment and freshness
- `main.py:7367-7766` - Composite scoring integration
- `main.py:5439-5506` - Score usage in decision logic
- `data/uw_flow_cache.json` - Check for missing data
- `data/uw_expanded_intel.json` - Check for missing expanded intel

---

## Expected Score Improvement

After fixes:
- **Current typical score:** 0.5-2.0
- **Expected typical score:** 2.5-5.0
- **Improvement:** +2.0-3.0 points

This should bring most signals above the 2.7 threshold.
