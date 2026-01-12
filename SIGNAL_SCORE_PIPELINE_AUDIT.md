# Signal → Score → Decision → Execution Pipeline Audit

## Executive Summary

This audit traces the complete signal-to-execution pipeline to identify why scores are extremely low. The analysis covers signal generation, enrichment, scoring, decision logic, and execution paths.

**Date:** 2026-01-10  
**Scope:** Full-stack audit of scoring pipeline  
**Goal:** Identify root causes of low scores

---

## A. Dependency Graph: Signal → Score → Decision → Execution Flow

```
UW API (uw_flow_daemon.py)
    ↓
uw_flow_cache.json (data/)
    ↓
enrich_signal() (uw_enrichment_v2.py)
    ├─→ compute_iv_term_skew()
    ├─→ compute_smile_slope()
    ├─→ compute_toxicity()
    ├─→ compute_event_alignment()
    ├─→ compute_freshness() ⚠️ CRITICAL: Can decay to 0.1
    └─→ Temporal motif detection
    ↓
enriched_data (Dict)
    ↓
compute_composite_score_v3() (uw_composite_v2.py)
    ├─→ Get adaptive weights (if available)
    ├─→ Load expanded_intel
    ├─→ Calculate 21 components:
    │   ├─→ flow_component = weight * flow_conv
    │   ├─→ dp_component = weight * dp_strength
    │   ├─→ insider_component = weight * (0.25-0.75)
    │   ├─→ iv_component = weight * abs(iv_skew) * alignment_factor
    │   ├─→ smile_component = weight * abs(smile_slope)
    │   ├─→ whale_score = weight * avg_conv (if detected)
    │   ├─→ event_component = weight * event_align
    │   ├─→ motif_bonus = weight * motif_strength
    │   ├─→ toxicity_component = weight * (toxicity - 0.5) * 1.5 (if > 0.5)
    │   ├─→ regime_component = weight * (regime_factor - 1.0) * 2.0
    │   ├─→ congress_component (if data available)
    │   ├─→ shorts_component (if data available)
    │   ├─→ inst_component (if data available)
    │   ├─→ tide_component (if data available)
    │   ├─→ calendar_component (if data available)
    │   ├─→ greeks_gamma_component (if data available)
    │   ├─→ ftd_pressure_component (if data available)
    │   ├─→ iv_rank_component (if data available)
    │   ├─→ oi_change_component (if data available)
    │   ├─→ etf_flow_component (if data available)
    │   └─→ squeeze_score_component (if data available)
    ├─→ Sum all components → composite_raw
    ├─→ Apply freshness decay: composite_score = composite_raw * freshness ⚠️ CRITICAL
    ├─→ Apply whale_conviction_boost (+0.5 if whale detected)
    └─→ Clamp: max(0.0, min(8.0, composite_score))
    ↓
composite result (Dict with "score" field)
    ↓
should_enter_v2() (uw_composite_v2.py)
    ├─→ Check threshold (base=2.7, canary=2.9, champion=3.2)
    ├─→ Check freshness >= 0.30
    ├─→ Check toxicity < 0.90
    └─→ Return True/False
    ↓
If gate_result == True:
    Create cluster with:
        - composite_score = composite["score"]
        - source = "composite_v3"
        - composite_meta = composite
    ↓
decide_and_execute() (main.py)
    ├─→ Sort clusters by composite_score DESC
    ├─→ For each cluster:
    │   ├─→ score = cluster.get("composite_score", 0.0)
    │   ├─→ If score > 0.0 and source == "composite_v3":
    │   │   ├─→ Apply structural_intelligence multipliers
    │   │   │   ├─→ regime_mult (from regime_detector)
    │   │   │   └─→ macro_mult (from macro_gate)
    │   │   │   → score = base_score * regime_mult * macro_mult
    │   │   └─→ Validate score (score_validation.py)
    │   ├─→ Check gates (regime, concentration, theme, etc.)
    │   ├─→ Check expectancy gate (V3.2)
    │   ├─→ Check momentum ignition filter
    │   ├─→ Check cooldown
    │   ├─→ Check position exists
    │   ├─→ Apply trade_guard.evaluate_order() ⚠️ NEW
    │   └─→ If all pass: submit_entry()
    ↓
submit_entry() (main.py AlpacaExecutor)
    ├─→ trade_guard check (if fails, return None)
    ├─→ Spread watchdog
    ├─→ Size validation
    └─→ Submit order to Alpaca
```

---

## B. All Scoring Functions and Their Inputs

### Primary Scoring Function
**`compute_composite_score_v3()`** (`uw_composite_v2.py:514`)
- **Inputs:**
  - `symbol: str`
  - `enriched_data: Dict` (from `enrich_signal()`)
  - `regime: str` (default: "NEUTRAL")
  - `expanded_intel: Dict` (optional, loaded from cache)
  - `use_adaptive_weights: bool` (default: True)
- **Output:** Dict with `"score"` field (0.0-8.0)

### Component Calculation Functions

1. **Flow Component** (`uw_composite_v2.py:590-598`)
   - Input: `flow_conv` (0.0-1.0), `flow_weight` (2.4 default)
   - Formula: `flow_weight * flow_conv_adjusted`
   - **Stealth flow boost:** +0.2 if `flow_conv < 0.3`
   - **Can be zero if:** `flow_conv == 0.0`

2. **Dark Pool Component** (`uw_composite_v2.py:604-613`)
   - Input: `dp_sent`, `dp_prem`, `dp_weight` (1.3 default)
   - Formula: `dp_weight * dp_strength`
   - **Can be zero if:** `dp_sent == "NEUTRAL"` or `dp_prem == 0`

3. **Insider Component** (`uw_composite_v2.py:615-624`)
   - Input: `ins_sent`, `ins_mod`, `insider_weight` (0.5 default)
   - Formula: `insider_weight * (0.25-0.75)` based on sentiment
   - **Can be zero if:** `ins_sent == "NEUTRAL"` (contributes 0.125 minimum)

4. **IV Term Skew Component** (`uw_composite_v2.py:626-629`)
   - Input: `iv_skew`, `iv_weight` (0.6 default), `flow_sign`
   - Formula: `iv_weight * abs(iv_skew) * (1.3 if aligned else 0.7)`
   - **Can be zero if:** `iv_skew == 0.0` or missing

5. **Smile Slope Component** (`uw_composite_v2.py:631-633`)
   - Input: `smile_slope`, `smile_weight` (0.35 default)
   - Formula: `smile_weight * abs(smile_slope)`
   - **Can be zero if:** `smile_slope == 0.0` or missing

6. **Whale Persistence Component** (`uw_composite_v2.py:635-641`)
   - Input: `motif_whale`, `whale_weight` (0.7 default)
   - Formula: `whale_weight * avg_conv` (if detected)
   - **Can be zero if:** `whale_detected == False`

7. **Event Alignment Component** (`uw_composite_v2.py:643-645`)
   - Input: `event_align`, `event_weight` (0.4 default)
   - Formula: `event_weight * event_align`
   - **Can be zero if:** `event_align == 0.0` or missing

8. **Temporal Motif Bonus** (`uw_composite_v2.py:647-656`)
   - Input: `motif_staircase`, `motif_burst`, `motif_weight` (0.6 default)
   - Formula: `motif_weight * motif_strength`
   - **Can be zero if:** No motifs detected

9. **Toxicity Penalty** (`uw_composite_v2.py:658-669`)
   - Input: `toxicity`, `tox_weight` (-0.9 default, must be negative)
   - Formula: `tox_weight * (toxicity - 0.5) * 1.5` (if toxicity > 0.5)
   - **Can be zero if:** `toxicity <= 0.5`

10. **Regime Modifier Component** (`uw_composite_v2.py:671-684`)
    - Input: `regime`, `flow_sign`, `regime_weight` (0.3 default)
    - Formula: `regime_weight * (regime_factor - 1.0) * 2.0`
    - **Can be zero if:** `regime == "mixed"` or `regime == "NEUTRAL"` (contributes ~0.012)

11-21. **V3 Expanded Components** (congress, shorts, institutional, tide, calendar, greeks, ftd, iv_rank, oi_change, etf_flow, squeeze_score)
    - **All can return 0.0 if:** Data not available or conditions not met
    - **Many have early returns:** `return 0.0, ""` if data missing

### Freshness Decay (CRITICAL)
**`compute_freshness()`** (`uw_enrichment_v2.py:234`)
- **Formula:** `freshness = exp(-age_min / 45)`
- **Minimum:** `max(0.1, min(1.0, freshness))`
- **Applied to final score:** `composite_score = composite_raw * freshness`
- **⚠️ CRITICAL ISSUE:** If data is 45+ minutes old, freshness < 0.5, which can cut scores in half
- **⚠️ FIX IN MAIN.PY:** Lines 7375-7384 adjust freshness to 0.9 if < 0.5, but this may not be sufficient

---

## C. All Fallback/Default Behaviors That Can Zero Out Scores

### 1. Missing Data → Component Returns 0.0

**Location:** `uw_composite_v2.py` component functions
- `compute_congress_component()`: Returns `0.0, ""` if `not congress_data` (line 254)
- `compute_shorts_component()`: Returns `0.0, ""` if `not shorts_data` (line 304)
- `compute_institutional_component()`: Returns `0.0, ""` if `not insider_data` (line 365)
- `compute_market_tide_component()`: Returns `0.0, ""` if `not tide_data` (line 427)
- `compute_calendar_component()`: Returns `0.0, ""` if `not calendar_data` (line 484)

**Impact:** If expanded intel data is missing, 5 components contribute 0.0

### 2. Missing Signal Features → Component = 0.0

**Location:** `uw_composite_v2.py:565-569`
- `iv_skew = _to_num(enriched_data.get("iv_term_skew", 0.0))` → Defaults to 0.0
- `smile_slope = _to_num(enriched_data.get("smile_slope", 0.0))` → Defaults to 0.0
- `event_align = _to_num(enriched_data.get("event_alignment", 0.0))` → Defaults to 0.0

**Impact:** If enrichment fails or cache doesn't have these, components = 0.0

### 3. Freshness Decay → Score Multiplied by < 1.0

**Location:** `uw_composite_v2.py:869`
- `composite_score = composite_raw * freshness`
- If `freshness = 0.1` (very stale), score is reduced by 90%

**Impact:** Even if all components sum to 3.0, if freshness=0.1, final score = 0.3

### 4. Missing Flow Conviction → Flow Component = 0.0

**Location:** `uw_composite_v2.py:552`
- `flow_conv = _to_num(enriched_data.get("conviction", 0.0))` → Defaults to 0.0
- `flow_component = flow_weight * flow_conv` → If flow_conv=0, component=0

**Impact:** Primary component (weight 2.4) contributes 0.0 if conviction missing

### 5. Missing Dark Pool Sentiment → DP Component = 0.2 (minimum)

**Location:** `uw_composite_v2.py:605-611`
- If `dp_sent not in ("BULLISH", "BEARISH")`, `dp_strength = 0.2`
- `dp_component = dp_weight * 0.2 = 1.3 * 0.2 = 0.26` (not zero, but low)

### 6. Missing Insider Sentiment → Insider Component = 0.125 (minimum)

**Location:** `uw_composite_v2.py:624`
- If `ins_sent == "NEUTRAL"`, `insider_component = insider_weight * 0.25 = 0.5 * 0.25 = 0.125`

### 7. Missing Motif Data → Motif Bonus = 0.0

**Location:** `uw_composite_v2.py:648-656`
- If no motifs detected, `motif_bonus = 0.0`

### 8. Missing Expanded Intel → All V3 Components = 0.0

**Location:** `uw_composite_v2.py:545-548`
- If `expanded_intel` is None or empty, all V3 components (congress, shorts, etc.) = 0.0

### 9. Missing Greeks/FTD/OI/ETF Data → Components = 0.0

**Location:** `uw_composite_v2.py:715-837`
- If `enriched_data.get("greeks", {})` is empty → `greeks_gamma_component = 0.0`
- If `enriched_data.get("ftd", {})` is empty → `ftd_pressure_component = 0.0`
- If `enriched_data.get("iv", {})` is empty → `iv_rank_component = 0.0` (or defaults to 50, which gives 0.15)
- If `enriched_data.get("oi_change", {})` is empty → `oi_change_component = 0.0`
- If `enriched_data.get("etf_flow", {})` is empty → `etf_flow_component = 0.0`
- If `enriched_data.get("squeeze_score", {})` is empty → `squeeze_score_component = 0.0`

### 10. Composite Score Clamping → Can't Go Negative

**Location:** `uw_composite_v2.py:881`
- `composite_score = max(0.0, min(8.0, composite_score))`
- **Impact:** Negative scores (from toxicity penalty) are clamped to 0.0

### 11. Structural Intelligence Multipliers → Can Reduce Score

**Location:** `main.py:5477`
- `score = base_score * regime_mult * macro_mult`
- If `regime_mult < 1.0` or `macro_mult < 1.0`, score is reduced
- **Can reduce score but not zero it** (unless both multipliers are 0.0, which shouldn't happen)

---

## D. All Exceptions That Can Cause Silent Score Failures

### 1. Import Errors → Adaptive Weights = None

**Location:** `uw_composite_v2.py:37-40`
```python
try:
    from adaptive_signal_optimizer import get_optimizer
    optimizer = get_optimizer()
except ImportError:
    optimizer = None
```
**Impact:** Falls back to default weights (acceptable, but may reduce scores if adaptive weights were higher)

### 2. Expanded Intel Load Failure → Empty Dict

**Location:** `uw_composite_v2.py:229-237`
```python
def _load_expanded_intel() -> Dict:
    try:
        if EXPANDED_INTEL_CACHE.exists():
            with EXPANDED_INTEL_CACHE.open("r") as f:
                return json.load(f)
    except:
        pass
    return {}
```
**Impact:** All V3 expanded components = 0.0 (silent failure)

### 3. Enrichment Failure → Missing Features

**Location:** `uw_enrichment_v2.py:248-275`
- If enrichment fails, features may be missing
- `enriched_data.get("iv_term_skew", 0.0)` → Returns 0.0 if missing
- **Impact:** Components that depend on these features = 0.0

### 4. Composite Scoring Returns None → Cluster Skipped

**Location:** `uw_composite_v2.py:103-127` (legacy function)
- If `sdata` is invalid (string, not dict), returns `None`
- **Location:** `main.py:7434`
- If `composite is None`, cluster is skipped (no score assigned)

### 5. Exception in Component Calculation → Component = 0.0

**Location:** Various component functions
- If exception occurs, component defaults to 0.0 or function returns `0.0, ""`
- **Impact:** Silent failure, component doesn't contribute

### 6. Exception in Structural Intelligence → Score Not Adjusted

**Location:** `main.py:5487-5490`
```python
except Exception as e:
    score = base_score
    final_score = score
    log_event("structural_intelligence", "error", symbol=symbol, error=str(e))
```
**Impact:** Score not adjusted (acceptable fallback, but may be lower than intended)

### 7. Exception in Score Validation → Validation Skipped

**Location:** `main.py:5503-5506`
```python
except ImportError:
    pass
except Exception as e:
    log_event("scoring", "score_validation_error", symbol=symbol, error=str(e))
```
**Impact:** Invalid scores may not be caught (but doesn't zero the score)

---

## E. All Mismatches Between Displayed Scores and Used Scores

### 1. Dashboard Shows `composite_score` from Cluster

**Location:** `dashboard.py` (likely reads from clusters or attribution logs)
- **Displayed:** `cluster.get("composite_score", 0.0)`
- **Used in decision:** Same value, but may be adjusted by structural intelligence multipliers

### 2. Structural Intelligence Multipliers Applied After Display

**Location:** `main.py:5477`
- **Displayed in logs:** `base_score` (before multipliers)
- **Used in decision:** `score = base_score * regime_mult * macro_mult`
- **Mismatch:** If multipliers < 1.0, actual score used is lower than displayed

### 3. Whale Conviction Boost Applied After Initial Score

**Location:** `uw_composite_v2.py:874-878`
- **Initial score:** `composite_raw * freshness`
- **Final score:** `composite_score = composite_raw * freshness + whale_conviction_boost`
- **Displayed:** Final score (includes boost)
- **Used:** Same (no mismatch)

### 4. Persistence Boost Applied After Composite Calculation

**Location:** `main.py:7496-7497`
- **Composite score:** Calculated in `compute_composite_score_v3()`
- **Persistence boost:** Applied later: `composite["score"] = original_score + persistence_boost`
- **Displayed:** Score after persistence boost
- **Used:** Same (no mismatch)

### 5. Sector Tide Boost Applied After Composite Calculation

**Location:** `main.py:7469`
- **Composite score:** Calculated first
- **Sector tide boost:** Applied: `composite["score"] = original_score + sector_tide_boost`
- **Displayed:** Score after boost
- **Used:** Same (no mismatch)

### 6. Alpha Signature Boosters Applied After Composite Calculation

**Location:** `main.py:7556`
- **Composite score:** Calculated first
- **Alpha boost:** Applied: `composite["score"] = original_score + alpha_boost_total`
- **Displayed:** Score after boost
- **Used:** Same (no mismatch)

### 7. Cross-Asset Adjustment Applied After Composite Calculation

**Location:** `main.py:7446`
- **Composite score:** Calculated first
- **Cross-asset adjustment:** Applied: `composite["score"] = original_score + cross_asset_adjustment`
- **Displayed:** Score after adjustment
- **Used:** Same (no mismatch)

**⚠️ POTENTIAL MISMATCH:** If dashboard shows score before structural intelligence multipliers, but decision uses score after multipliers, there's a mismatch.

---

## F. All Normalization/Scaling Issues

### 1. Freshness Exponential Decay Too Aggressive

**Location:** `uw_enrichment_v2.py:245`
- **Formula:** `freshness = exp(-age_min / 45)`
- **Issue:** After 45 minutes, freshness = 0.5 (50% reduction)
- **After 90 minutes:** freshness ≈ 0.25 (75% reduction)
- **After 135 minutes:** freshness ≈ 0.125 (87.5% reduction)
- **Minimum:** 0.1 (90% reduction maximum)

**Impact:** Scores are heavily penalized for stale data, even if data is still valid

### 2. Flow Conviction Clipped to 0.0-1.0

**Location:** `uw_composite_v2.py:552`
- `flow_conv = _to_num(enriched_data.get("conviction", 0.0))`
- **Issue:** If conviction is missing, defaults to 0.0 (not 0.5 or neutral)

**Impact:** Missing conviction → flow component = 0.0 (primary component lost)

### 3. IV Skew and Smile Slope Use abs() → Loses Direction

**Location:** `uw_composite_v2.py:629, 633`
- `iv_component = iv_weight * abs(iv_skew) * alignment_factor`
- `smile_component = smile_weight * abs(smile_slope)`
- **Issue:** Using `abs()` means negative values contribute the same as positive (may be intentional for alignment)

### 4. Component Values Clamped to 0.0-1.0 Range

**Location:** Various component calculations
- Many components use `min(1.0, ...)` to cap strength
- **Issue:** If actual value exceeds 1.0, it's capped (may be intentional)

### 5. Final Score Clamped to 0.0-8.0

**Location:** `uw_composite_v2.py:881`
- `composite_score = max(0.0, min(8.0, composite_score))`
- **Issue:** If raw score > 8.0, it's capped (may be intentional)

### 6. Toxicity Penalty Can Make Score Negative

**Location:** `uw_composite_v2.py:663-669`
- `toxicity_component = tox_weight * (toxicity - 0.5) * 1.5`
- `tox_weight = -0.9` (negative)
- **Issue:** High toxicity can make `composite_raw` negative, then clamped to 0.0

**Impact:** High toxicity → score = 0.0 (may be intentional, but harsh)

### 7. Regime Modifier Calculation

**Location:** `uw_composite_v2.py:684`
- `regime_component = regime_weight * (regime_factor - 1.0) * 2.0`
- **Issue:** For "mixed" regime, `regime_factor = 1.02`, so component = 0.3 * 0.02 * 2.0 = 0.012 (very small)

**Impact:** Mixed regime contributes almost nothing

---

## G. All Threshold Mismatches

### 1. Entry Threshold vs Score Distribution

**Location:** `uw_composite_v2.py:204-208`
- **Thresholds:**
  - `base: 2.7`
  - `canary: 2.9`
  - `champion: 3.2`
- **Issue:** If scores are typically 0.5-2.0, thresholds are too high

**Evidence from code comments:**
- Line 201: "ROOT CAUSE FIX: Thresholds were raised to 3.5/3.8/4.2 which blocked ALL trading"
- Line 205: "RESTORED to quality level - orders show scores 2.26-3.00 (avg 2.89)"

### 2. Freshness Threshold in Gate

**Location:** `uw_composite_v2.py:1229` (should_enter_v2)
- **Threshold:** `freshness >= 0.30`
- **Issue:** If freshness < 0.30, signal is rejected even if score is high

**Impact:** Stale data (90+ minutes old) is rejected regardless of score

### 3. Toxicity Threshold in Gate

**Location:** `uw_composite_v2.py:1233` (should_enter_v2)
- **Threshold:** `toxicity < 0.90`
- **Issue:** If toxicity >= 0.90, signal is rejected

**Impact:** High toxicity signals are rejected (may be intentional)

### 4. Score Validation Threshold

**Location:** `score_validation.py:51`
- **Threshold:** `score <= 0.0` triggers critical exception
- **Issue:** Scores of 0.0 are flagged as invalid

**Impact:** Zero scores trigger reinitialization attempts

---

## H. All Missing or Empty Feature Inputs

### 1. Flow Conviction Missing → Defaults to 0.0

**Location:** `uw_composite_v2.py:552`
- `flow_conv = _to_num(enriched_data.get("conviction", 0.0))`
- **Impact:** Primary component (weight 2.4) = 0.0

### 2. IV Term Skew Missing → Defaults to 0.0

**Location:** `uw_composite_v2.py:565`
- `iv_skew = _to_num(enriched_data.get("iv_term_skew", 0.0))`
- **Impact:** Component (weight 0.6) = 0.0

### 3. Smile Slope Missing → Defaults to 0.0

**Location:** `uw_composite_v2.py:566`
- `smile_slope = _to_num(enriched_data.get("smile_slope", 0.0))`
- **Impact:** Component (weight 0.35) = 0.0

### 4. Event Alignment Missing → Defaults to 0.0

**Location:** `uw_composite_v2.py:568`
- `event_align = _to_num(enriched_data.get("event_alignment", 0.0))`
- **Impact:** Component (weight 0.4) = 0.0

### 5. Toxicity Missing → Defaults to 0.0

**Location:** `uw_composite_v2.py:567`
- `toxicity = _to_num(enriched_data.get("toxicity", 0.0))`
- **Impact:** No penalty applied (acceptable, but may miss toxic signals)

### 6. Freshness Missing → Defaults to 1.0

**Location:** `uw_composite_v2.py:569`
- `freshness = _to_num(enriched_data.get("freshness", 1.0))`
- **Impact:** No decay applied (acceptable fallback)

### 7. Expanded Intel Missing → All V3 Components = 0.0

**Location:** `uw_composite_v2.py:545-548`
- If `expanded_intel` is None or empty, all V3 components = 0.0
- **Impact:** 11 components contribute 0.0 (congress, shorts, institutional, tide, calendar, greeks, ftd, iv_rank, oi_change, etf_flow, squeeze_score)

### 8. Dark Pool Data Missing → Component = 0.26 (minimum)

**Location:** `uw_composite_v2.py:556-559, 605-611`
- If `dark_pool` is missing or empty, `dp_strength = 0.2`
- **Impact:** Component = 1.3 * 0.2 = 0.26 (not zero, but low)

### 9. Insider Data Missing → Component = 0.125 (minimum)

**Location:** `uw_composite_v2.py:562, 616-624`
- If `insider` is missing or empty, `ins_sent = "NEUTRAL"`
- **Impact:** Component = 0.5 * 0.25 = 0.125 (not zero, but low)

### 10. Motif Data Missing → Motif Bonus = 0.0

**Location:** `uw_composite_v2.py:579-582, 648-656`
- If motif data is missing, `motif_bonus = 0.0`
- **Impact:** Component (weight 0.6) = 0.0

---

## I. All Places Where Scores Are Overwritten, Clipped, or Dropped

### 1. Freshness Decay Multiplies Score

**Location:** `uw_composite_v2.py:869`
- `composite_score = composite_raw * freshness`
- **Impact:** Reduces score proportionally to freshness (can reduce by 90%)

### 2. Final Score Clamped to 0.0-8.0

**Location:** `uw_composite_v2.py:881`
- `composite_score = max(0.0, min(8.0, composite_score))`
- **Impact:** Negative scores → 0.0, scores > 8.0 → 8.0

### 3. Structural Intelligence Multipliers

**Location:** `main.py:5477`
- `score = base_score * regime_mult * macro_mult`
- **Impact:** Can reduce or increase score (typically 0.9-1.15x range)

### 4. Whale Conviction Boost Added

**Location:** `uw_composite_v2.py:877`
- `composite_score += whale_conviction_boost` (typically +0.5)
- **Impact:** Increases score (positive)

### 5. Persistence Boost Added

**Location:** `main.py:7497`
- `composite["score"] = original_score + persistence_boost`
- **Impact:** Increases score (positive)

### 6. Sector Tide Boost Added

**Location:** `main.py:7469`
- `composite["score"] = original_score + sector_tide_boost`
- **Impact:** Increases score (positive)

### 7. Alpha Signature Boosters Added

**Location:** `main.py:7556`
- `composite["score"] = original_score + alpha_boost_total`
- **Impact:** Increases score (positive)

### 8. Cross-Asset Adjustment Added

**Location:** `main.py:7446`
- `composite["score"] = original_score + cross_asset_adjustment`
- **Impact:** Can increase or decrease score

### 9. Score Validation Can Trigger Reinitialization

**Location:** `score_validation.py:59-66`
- If score <= 0.0, attempts to reinitialize scoring weights
- **Impact:** May change weights, affecting future scores

### 10. Cluster Score Overwritten in Fallback Path

**Location:** `main.py:5602`
- If `cluster_source == "unknown"` or `composite_score <= 0.0`, recalculates score
- **Impact:** Original composite_score is replaced with fallback calculation

---

## J. Final Diagnosis: Why Scores Are Low

### Root Cause #1: Freshness Decay Too Aggressive (CRITICAL)

**Evidence:**
- `freshness = exp(-age_min / 45)` decays to 0.5 after 45 minutes
- Final score: `composite_raw * freshness`
- If data is 90+ minutes old, freshness ≈ 0.25, cutting score by 75%

**Impact:** Even if all components sum to 3.0, if freshness=0.25, final score = 0.75

**Fix Applied (Partial):** `main.py:7375-7384` adjusts freshness to 0.9 if < 0.5, but this may not be sufficient if freshness is already applied in composite calculation.

### Root Cause #2: Missing Expanded Intel Data (CRITICAL)

**Evidence:**
- V3 components (congress, shorts, institutional, tide, calendar, greeks, ftd, iv_rank, oi_change, etf_flow, squeeze_score) all return 0.0 if data missing
- Total potential contribution: ~4.0 points
- If all missing: 11 components = 0.0

**Impact:** Scores are 2.0-4.0 points lower than they could be

### Root Cause #3: Missing Core Signal Features (HIGH)

**Evidence:**
- `iv_term_skew`, `smile_slope`, `event_alignment` default to 0.0 if missing
- Total potential contribution: ~1.35 points (0.6 + 0.35 + 0.4)
- If all missing: 3 components = 0.0

**Impact:** Scores are 1.0-1.5 points lower than they could be

### Root Cause #4: Flow Conviction Missing or Low (HIGH)

**Evidence:**
- Primary component: `flow_component = 2.4 * flow_conv`
- If `flow_conv = 0.0` (missing), component = 0.0
- If `flow_conv = 0.3` (low), component = 0.72

**Impact:** Missing conviction → primary component lost (2.4 points)

### Root Cause #5: Dark Pool Sentiment Neutral (MEDIUM)

**Evidence:**
- If `dp_sent == "NEUTRAL"`, `dp_strength = 0.2`
- Component = 1.3 * 0.2 = 0.26 (vs potential 0.65-1.3)

**Impact:** Neutral sentiment → component reduced by ~75%

### Root Cause #6: Insider Sentiment Neutral (MEDIUM)

**Evidence:**
- If `ins_sent == "NEUTRAL"`, component = 0.5 * 0.25 = 0.125
- If `ins_sent == "BULLISH"`, component = 0.5 * (0.50 + modifier) ≈ 0.25-0.375

**Impact:** Neutral sentiment → component reduced by ~50%

### Root Cause #7: Missing Motif Detection (MEDIUM)

**Evidence:**
- If no motifs detected, `motif_bonus = 0.0`
- Potential contribution: 0.6-1.8 points

**Impact:** No motifs → component lost (0.6-1.8 points)

### Root Cause #8: Structural Intelligence Multipliers < 1.0 (LOW)

**Evidence:**
- `score = base_score * regime_mult * macro_mult`
- If both multipliers = 0.9, score reduced by 19%

**Impact:** Can reduce scores but typically not the primary cause

### Root Cause #9: Toxicity Penalty (LOW)

**Evidence:**
- If `toxicity > 0.5`, penalty applied: `-0.9 * (toxicity - 0.5) * 1.5`
- High toxicity can make score negative, then clamped to 0.0

**Impact:** High toxicity → score = 0.0 (may be intentional)

### Root Cause #10: Threshold Too High Relative to Score Distribution (MEDIUM)

**Evidence:**
- Threshold: 2.7 (base)
- If scores are typically 0.5-2.0, most signals are rejected
- Code comments indicate scores are 2.26-3.00 (avg 2.89), so threshold may be appropriate

**Impact:** If scores are low due to other issues, threshold appears too high

---

## K. Patch Plan to Fix Root Causes

### Priority 1: Fix Freshness Decay (CRITICAL)

**Issue:** Freshness decay is too aggressive and applied after component calculation

**Fix:**
1. **Option A:** Increase decay_min from 45 to 180 minutes (4x slower decay)
   - Location: `uw_enrichment_v2.py:234`
   - Change: `decay_min: int = 180`
   - Impact: After 180 minutes, freshness = 0.5 (vs 45 minutes currently)

2. **Option B:** Apply freshness decay only to stale components, not entire score
   - Location: `uw_composite_v2.py:869`
   - Change: Apply freshness only to components that depend on time-sensitive data
   - Impact: Core components (flow, dark pool) not affected by freshness

3. **Option C:** Remove freshness decay entirely (if data age is handled by gate)
   - Location: `uw_composite_v2.py:869`
   - Change: `composite_score = composite_raw` (remove `* freshness`)
   - Impact: Scores not reduced by freshness (gate still checks freshness >= 0.30)

**Recommended:** Option A (increase decay_min to 180) - preserves freshness concept but less aggressive

### Priority 2: Ensure Core Signal Features Are Computed (CRITICAL)

**Issue:** `iv_term_skew`, `smile_slope`, `event_alignment` default to 0.0 if missing

**Fix:**
1. **Ensure enrichment always computes these features:**
   - Location: `main.py:7395-7407`
   - Already has fallback computation, but may not be triggered
   - **Enhancement:** Always compute if missing, even if cache has data

2. **Add validation to ensure features exist before scoring:**
   - Location: `uw_composite_v2.py:565-569`
   - Add check: If feature missing, compute on-the-fly using `UWEnricher`

**Recommended:** Enhance existing fallback computation to be more aggressive

### Priority 3: Handle Missing Expanded Intel Gracefully (HIGH)

**Issue:** All V3 expanded components return 0.0 if data missing

**Fix:**
1. **Provide default values for missing expanded intel:**
   - Location: `uw_composite_v2.py:545-548`
   - Instead of empty dict, provide defaults with neutral values
   - Impact: Components contribute small amounts instead of 0.0

2. **Reduce weights for components that are often missing:**
   - Location: `uw_composite_v2.py:155-184`
   - If component is frequently missing, reduce its weight to avoid score deflation

**Recommended:** Provide default values for missing data (neutral contributions)

### Priority 4: Ensure Flow Conviction Is Never 0.0 (HIGH)

**Issue:** Missing conviction → flow component = 0.0 (primary component lost)

**Fix:**
1. **Default conviction to 0.5 (neutral) instead of 0.0:**
   - Location: `uw_composite_v2.py:552`
   - Change: `flow_conv = _to_num(enriched_data.get("conviction", 0.5))`
   - Impact: Missing conviction → component = 1.2 (vs 0.0)

2. **Validate conviction exists before scoring:**
   - Location: `uw_composite_v2.py:590`
   - Add check: If conviction missing, log warning and use 0.5

**Recommended:** Default to 0.5 (neutral) instead of 0.0

### Priority 5: Improve Missing Data Handling (MEDIUM)

**Issue:** Many components return 0.0 if data missing

**Fix:**
1. **Provide neutral defaults for all components:**
   - Location: Various component functions
   - Instead of `return 0.0, ""`, return small neutral contribution
   - Impact: Missing data doesn't zero out components

2. **Log missing data for monitoring:**
   - Location: Component functions
   - Add logging when data is missing
   - Impact: Visibility into why components are 0.0

**Recommended:** Provide neutral defaults (small positive contributions)

### Priority 6: Verify Freshness Fix in main.py Is Applied Correctly (MEDIUM)

**Issue:** `main.py:7375-7384` adjusts freshness, but may be too late (already applied in composite)

**Fix:**
1. **Check if freshness adjustment happens before or after composite calculation:**
   - Location: `main.py:7367-7384`
   - Freshness is adjusted in `enriched` dict before `compute_composite_score_v3()`
   - **This should work**, but verify it's not being overwritten

2. **Add logging to verify freshness value:**
   - Location: `main.py:7377`
   - Log actual freshness value used in composite calculation

**Recommended:** Verify freshness adjustment is working (add logging)

### Priority 7: Review Thresholds vs Actual Score Distribution (LOW)

**Issue:** Thresholds may be too high if scores are consistently low

**Fix:**
1. **Analyze actual score distribution from logs:**
   - Check `logs/attribution.jsonl` for score values
   - Calculate mean, median, percentiles

2. **Adjust thresholds if needed:**
   - Location: `uw_composite_v2.py:204-208`
   - If scores are typically 0.5-2.0, lower thresholds to 1.5/1.7/2.0
   - If scores are 2.0-3.0, current thresholds (2.7/2.9/3.2) may be appropriate

**Recommended:** Analyze score distribution first, then adjust if needed

---

## Summary of Critical Issues

1. **Freshness decay too aggressive** - Cuts scores by 50-90% for stale data
2. **Missing expanded intel** - 11 components contribute 0.0 (potential 4.0 points lost)
3. **Missing core features** - 3 components contribute 0.0 (potential 1.35 points lost)
4. **Missing flow conviction** - Primary component = 0.0 (potential 2.4 points lost)
5. **Neutral sentiment defaults** - Dark pool and insider contribute minimally

**Estimated Score Impact:**
- **Maximum potential score:** ~8.0 (if all components contribute)
- **Typical score with missing data:** 0.5-2.0 (if many components missing)
- **After freshness decay (0.25):** 0.125-0.5 (if data is 90+ minutes old)

**Most Likely Root Cause:** Combination of:
1. Freshness decay reducing scores by 50-90%
2. Missing expanded intel data (11 components = 0.0)
3. Missing core features (3 components = 0.0)
4. Missing or low flow conviction (primary component reduced)

**Recommended Immediate Fixes:**
1. Increase `decay_min` from 45 to 180 minutes
2. Default `flow_conv` to 0.5 instead of 0.0
3. Provide neutral defaults for missing expanded intel
4. Ensure core features (iv_skew, smile_slope, event_align) are always computed
5. Add logging to track which components are contributing 0.0

---

## Next Steps

1. **Run diagnostic script** to capture actual score distributions
2. **Check logs** for missing data warnings
3. **Verify freshness values** in composite results
4. **Implement Priority 1-4 fixes**
5. **Re-test** and measure score improvement
