# STOCK-BOT FULL SCORING SYSTEM DOCUMENTATION

**Date:** 2026-01-12  
**Version:** V3.1 (Full Intelligence Pipeline)  
**Mode:** EXTRACTION & DOCUMENTATION (No Production Logic Modifications)

---

## EXECUTIVE SUMMARY

This document provides a complete extraction, documentation, and visualization of the stock-bot scoring system:

- **Buy-Side Components:** 21 signal components with weights, ranges, and formulas
- **Exit-Side Components:** 7 exit urgency components with weights, ranges, and formulas
- **Adaptive Multipliers:** 0.25x - 2.5x range (regime-aware)
- **Score Range:** 0.0 - 8.0 (can exceed theoretical max due to multipliers)
- **Exit Urgency Range:** 0.0 - 10.0

---

## TABLE OF CONTENTS

1. [Buy-Side Scoring Components](#buy-side-scoring-components)
2. [Exit-Side Scoring Components](#exit-side-scoring-components)
3. [Scoring Formulas](#scoring-formulas)
4. [Thresholds & Decision Rules](#thresholds--decision-rules)
5. [JSON Export](#json-export)
6. [Visual Scoring Map](#visual-scoring-map)
7. [Component Details](#component-details)

---

## BUY-SIDE SCORING COMPONENTS

### Core Flow Signals (V1 - Original)

| Component | Weight (V3) | Raw Range | Multiplier Range | Final Contribution Formula | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------|
| **options_flow** | 2.4 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * flow_conv_adjusted` | Primary anchor component. Stealth flow boost +0.2 for LOW magnitude (<0.3). Default conviction 0.5 if missing. |
| **dark_pool** | 1.3 | 0.2 - 1.3 | 0.25x - 2.5x | `weight * (0.5 + log10(premium)/7.5)` | Log-scaled by notional magnitude. Neutral 0.2 if no sentiment. |
| **insider** | 0.5 | 0.125 - 0.55 | 0.25x - 2.5x | `weight * (0.50 ± modifier)` | BULLISH: 0.50+mod, BEARISH: 0.50-abs(mod), NEUTRAL: 0.25. Modifier range: -0.05 to +0.05 |

### V2 Features (Advanced Options Signals)

| Component | Weight (V3) | Raw Range | Multiplier Range | Final Contribution Formula | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------|
| **iv_term_skew** | 0.6 | -0.15 to +0.15 | 0.25x - 2.5x | `weight * abs(skew) * (1.3 if aligned else 0.7)` | Alignment bonus/penalty based on flow direction |
| **smile_slope** | 0.35 | -0.10 to +0.10 | 0.25x - 2.5x | `weight * abs(slope)` | OTM call/put skew indicator |
| **whale_persistence** | 0.7 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * avg_conviction` | Sustained high conviction detection |
| **event_alignment** | 0.4 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * event_align` | Earnings/FDA/economic event alignment |
| **temporal_motif** | 0.6 | 0.0 - variable | 0.25x - 2.5x | `weight * (staircase_slope*3.0 + burst_intensity/2.0)` | Pattern detection (staircase, burst, sweep) |
| **toxicity_penalty** | -0.9 | -1.35 to 0.0 | 0.25x - 2.5x | `weight * (toxicity - 0.5) * 1.5` | **NEGATIVE weight** - penalizes signal disagreement. Applied if toxicity > 0.5 |
| **regime_modifier** | 0.3 | variable | 0.25x - 2.5x | `weight * (regime_factor - 1.0) * 2.0` | RISK_ON: +1.15 aligned, +0.95 opposite. RISK_OFF: +1.10 opposite, +0.90 aligned. Mixed: +1.02 |

### V3 Expanded Intelligence Signals

| Component | Weight (V3) | Raw Range | Multiplier Range | Final Contribution Formula | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------|
| **congress** | 0.9 | -0.36 to +0.9 | 0.25x - 2.5x | `weight * (0.6 + activity*0.4) * (1+boost)` if aligned | Politician trading signals. Neutral default 0.2x weight if missing |
| **shorts_squeeze** | 0.7 | -0.14 to +0.7 | 0.25x - 2.5x | `weight * (SI_strength + DTC_strength + squeeze_flag*0.3)` | Short interest + days to cover + FTD pressure. Neutral default 0.2x weight if missing |
| **institutional** | 0.5 | -0.15 to +0.5 | 0.25x - 2.5x | `weight * (0.5 + activity*0.5 + usd_bonus)` if aligned | 13F filings & institutional activity. Neutral default 0.2x weight if missing |
| **market_tide** | 0.4 | 0.08 to +0.4 | 0.25x - 2.5x | `weight * call_ratio * (1.0 if aligned else 0.5)` | Options market sentiment. Neutral default 0.2x weight if missing |
| **calendar_catalyst** | 0.45 | 0.0 to +0.45 | 0.25x - 2.5x | `weight * (earnings_prox*0.4 + FDA*0.5 + econ*0.2)` | Earnings/FDA/Economic events. Neutral default 0.2x weight if missing |
| **etf_flow** | 0.3 | -0.09 to +0.3 | 0.25x - 2.5x | `weight * (1.0 if BULLISH+risk_on else 0.5 if BULLISH else -0.3 if BEARISH)` | ETF in/outflows. Neutral default 0.2x weight if missing |

### V2 Full Intelligence Pipeline (Advanced Market Microstructure)

| Component | Weight (V3) | Raw Range | Multiplier Range | Final Contribution Formula | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------|
| **greeks_gamma** | 0.4 | 0.04 to +0.4 | 0.25x - 2.5x | `weight * (1.0 if squeeze, else 0.5/0.25/0.1/0.2 by exposure)` | Gamma exposure for squeeze detection. Neutral default 0.2x weight if missing |
| **ftd_pressure** | 0.3 | 0.06 to +0.3 | 0.25x - 2.5x | `weight * (1.0 if squeeze/200k+, else 0.67/0.33/0.1/0.2 by count)` | Fails-to-deliver pressure. Neutral default 0.2x weight if missing |
| **iv_rank** | 0.2 | -0.2 to +0.2 | 0.25x - 2.5x | `weight * (1.0 if <20, 0.5 if <30, -1.0 if >80, -0.5 if >70, 0.15 if 30-70)` | IV rank for options timing. **Can be negative** (high IV = caution) |
| **oi_change** | 0.35 | 0.035 to +0.35 | 0.25x - 2.5x | `weight * (1.0 if >50k aligned, else 0.57/0.29/0.1/0.2)` | Open interest changes. Neutral default 0.2x weight if missing |
| **squeeze_score** | 0.2 | 0.04 to +0.2 | 0.25x - 2.5x | `weight * (1.0 if high, else 0.5 if signals>=1, else 0.2)` | Combined squeeze indicator. Neutral default 0.2x weight if missing |

---

## EXIT-SIDE SCORING COMPONENTS

### Exit Urgency Components

| Component | Base Weight | Raw Range | Multiplier Range | Final Contribution Formula | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------|
| **entry_decay** | 1.0 | 0.0 - 1.0 | 0.25x - 2.5x | `(1 - decay_ratio) * weight` | Triggered if current_score/entry_score < 0.7 (30%+ decay) |
| **adverse_flow** | 1.2 | 0.0 - 2.4 | 0.25x - 2.5x | `2.0 * weight` | Flow reversal detected (LONG+Bearish or SHORT+Bullish) |
| **drawdown_velocity** | 1.5 | 0.0 - 4.5 | 0.25x - 2.5x | `min(3.0, drawdown/age_days) * 0.5 * weight` | Triggered if drawdown > 3.0%. Velocity = drawdown/age_hours |
| **time_decay** | 0.8 | 0.0 - 1.6 | 0.25x - 2.5x | `min(2.0, (age_hours-72)/48) * weight` | Triggered if age > 72 hours |
| **momentum_reversal** | 1.3 | 0.0 - variable | 0.25x - 2.5x | `abs(momentum) * weight` | Triggered if LONG+momentum<-0.5 or SHORT+momentum>0.5 |
| **volume_exhaustion** | 0.9 | 0.0 - variable | 0.25x - 2.5x | (Not actively used in current code) | Reserved for future use |
| **support_break** | 1.4 | 0.0 - variable | 0.25x - 2.5x | (Not actively used in current code) | Reserved for future use |
| **loss_limit** | 2.0 (fixed) | 0.0 - 2.0 | N/A (fixed) | `2.0` if current_pnl < -5.0% | Hard-coded loss limit override |

### Exit Urgency Thresholds

| Threshold | Value | Recommendation |
|-----------|-------|----------------|
| **EXIT** | urgency ≥ 6.0 | Immediate close |
| **REDUCE** | urgency ≥ 3.0 | Consider partial close |
| **HOLD** | urgency < 3.0 | Continue monitoring |

---

## SCORING FORMULAS

### Buy-Side Composite Score Formula

```
# Component Calculation (per component)
component_contribution = base_weight * adaptive_multiplier * raw_value * alignment_factor

# Special Cases:
- options_flow: raw_value = min(1.0, conviction + stealth_boost)  # stealth_boost = 0.2 if LOW magnitude
- dark_pool: raw_value = 0.5 + log10(premium)/7.5  # if BULLISH/BEARISH, else 0.2
- toxicity_penalty: contribution = weight * (toxicity - 0.5) * 1.5  # if toxicity > 0.5
- regime_modifier: contribution = weight * (regime_factor - 1.0) * 2.0

# Final Score Calculation
composite_raw = sum(all_components)
composite_score = composite_raw * freshness_factor + whale_conviction_boost
composite_score = clamp(composite_score, 0.0, 8.0)
```

### Exit Urgency Score Formula

```
urgency = 0.0

# Entry Decay
if entry_score > 0 and current_score/entry_score < 0.7:
    urgency += (1 - decay_ratio) * weight("entry_decay")

# Adverse Flow
if flow_reversal:
    urgency += 2.0 * weight("adverse_flow")

# Drawdown Velocity
if drawdown > 3.0:
    velocity = drawdown / max(1, age_hours/24)
    urgency += min(3.0, velocity * 0.5) * weight("drawdown_velocity")

# Time Decay
if age_hours > 72:
    urgency += min(2.0, (age_hours-72)/48) * weight("time_decay")

# Momentum Reversal
if (LONG and momentum < -0.5) or (SHORT and momentum > 0.5):
    urgency += abs(momentum) * weight("momentum_reversal")

# Loss Limit (fixed)
if current_pnl < -5.0:
    urgency += 2.0

# Recommendation
if urgency >= 6.0: recommendation = "EXIT"
elif urgency >= 3.0: recommendation = "REDUCE"
else: recommendation = "HOLD"
```

---

## THRESHOLDS & DECISION RULES

### Buy-Side Thresholds

| Threshold | Value | Source | Notes |
|-----------|-------|--------|-------|
| **MIN_EXEC_SCORE** | 3.0 | `config/registry.py` | Minimum composite score to execute trade |
| **MIN_NOTIONAL_USD** | $100 | `Config.MIN_NOTIONAL_USD` | Minimum order notional |
| **MAX_SPREAD_BPS** | 50 | `Config.MAX_SPREAD_BPS` | Maximum spread to allow execution |

### Exit-Side Thresholds

| Threshold | Value | Source | Notes |
|-----------|-------|--------|-------|
| **EXIT Urgency** | ≥ 6.0 | `adaptive_signal_optimizer.py` | Immediate close |
| **REDUCE Urgency** | ≥ 3.0 | `adaptive_signal_optimizer.py` | Partial close |
| **HOLD Urgency** | < 3.0 | `adaptive_signal_optimizer.py` | Continue monitoring |
| **TRAILING_STOP_PCT** | 1.5% | `config/registry.py` | Trailing stop percentage |
| **TIME_EXIT_MINUTES** | 240 | `config/registry.py` | Time-based exit (4 hours) |
| **TIME_EXIT_DAYS_STALE** | 12 | `config/registry.py` | Stale position exit |

---

## JSON EXPORT

```json
{
  "version": "V3.1",
  "extraction_date": "2026-01-12",
  "buy_score_components": [
    {
      "name": "options_flow",
      "weight": 2.4,
      "raw_range": [0.0, 1.0],
      "multiplier_range": [0.25, 2.5],
      "formula": "weight * min(1.0, conviction + stealth_boost)",
      "anchored": true,
      "notes": "Primary anchor component. Stealth flow boost +0.2 for LOW magnitude (<0.3). Default conviction 0.5 if missing."
    },
    {
      "name": "dark_pool",
      "weight": 1.3,
      "raw_range": [0.2, 1.3],
      "multiplier_range": [0.25, 2.5],
      "formula": "weight * (0.5 + log10(premium)/7.5) if BULLISH/BEARISH else weight * 0.2",
      "anchored": false,
      "notes": "Log-scaled by notional magnitude. Neutral 0.2 if no sentiment."
    }
  ],
  "exit_score_components": [
    {
      "name": "entry_decay",
      "base_weight": 1.0,
      "raw_range": [0.0, 1.0],
      "multiplier_range": [0.25, 2.5],
      "formula": "(1 - decay_ratio) * weight",
      "notes": "Triggered if current_score/entry_score < 0.7 (30%+ decay)"
    }
  ],
  "thresholds": {
    "buy": {
      "min_exec_score": 3.0,
      "min_notional_usd": 100,
      "max_spread_bps": 50
    },
    "exit": {
      "exit": 6.0,
      "reduce": 3.0,
      "hold": 0.0
    }
  }
}
```

*[Full JSON export provided in separate file: `SCORING_SYSTEM_JSON_EXPORT.json`]*

---

## VISUAL SCORING MAP

This visual map shows the complete flow from raw inputs to final decisions. Suitable for dashboard integration or MEMORY_BANK.md.

```
═══════════════════════════════════════════════════════════════════════════
                    STOCK-BOT SCORING SYSTEM MAP
                    Complete Buy-Side & Exit-Side Flow
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                        BUY-SIDE SCORING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────┘

RAW INPUTS
    │
    ├─► Options Flow (conviction: 0.0-1.0)
    ├─► Dark Pool (premium: $0-$100M+)
    ├─► Insider (net_buys/sells, modifier: -0.05 to +0.05)
    ├─► IV Term Skew (-0.15 to +0.15)
    ├─► Smile Slope (-0.10 to +0.10)
    ├─► Market Microstructure (greeks, FTD, OI, IV rank)
    ├─► Expanded Intel (congress, shorts, institutional, tide, calendar, ETF)
    └─► Motifs (staircase, sweep, burst, whale)
    │
    ▼
NORMALIZATION
    │
    ├─► Flow: conviction + stealth_boost (if LOW magnitude)
    ├─► Dark Pool: log10(premium)/7.5 scaling
    ├─► Missing Data: Neutral defaults (0.2x weight) for most components
    └─► Toxicity: Penalty if > 0.5
    │
    ▼
WEIGHTED COMPONENTS
    │
    ├─► Core Flow Signals (weight: 2.4, 1.3, 0.5)
    │   ├─► options_flow [ANCHOR] (2.4)
    │   ├─► dark_pool (1.3)
    │   └─► insider (0.5)
    │
    ├─► V2 Advanced Features (weights: 0.6, 0.35, 0.7, 0.4, -0.9, 0.6, 0.3)
    │   ├─► iv_term_skew (0.6) - alignment bonus/penalty
    │   ├─► smile_slope (0.35)
    │   ├─► whale_persistence (0.7)
    │   ├─► event_alignment (0.4)
    │   ├─► temporal_motif (0.6)
    │   ├─► toxicity_penalty (-0.9) [NEGATIVE]
    │   └─► regime_modifier (0.3)
    │
    ├─► V3 Expanded Intelligence (weights: 0.9, 0.7, 0.5, 0.4, 0.45, 0.3)
    │   ├─► congress (0.9)
    │   ├─► shorts_squeeze (0.7)
    │   ├─► institutional (0.5)
    │   ├─► market_tide (0.4)
    │   ├─► calendar_catalyst (0.45)
    │   └─► etf_flow (0.3)
    │
    └─► V2 Full Intelligence Pipeline (weights: 0.4, 0.3, 0.2, 0.35, 0.2)
        ├─► greeks_gamma (0.4)
        ├─► ftd_pressure (0.3)
        ├─► iv_rank (0.2) [CAN BE NEGATIVE]
        ├─► oi_change (0.35)
        └─► squeeze_score (0.2)
    │
    ▼
ADAPTIVE MULTIPLIERS (Regime-Aware)
    │
    └─► Per-component multipliers: 0.25x - 2.5x
        (Learned from trade outcomes, regime-specific)
    │
    ▼
FINAL AGGREGATION
    │
    ├─► composite_raw = sum(all_weighted_components)
    ├─► composite_score = composite_raw * freshness_factor
    ├─► + whale_conviction_boost (+0.5 if whale detected)
    └─► composite_score = clamp(0.0, 8.0)
    │
    ▼
DECISION LOGIC
    │
    ├─► Score >= 3.0 (MIN_EXEC_SCORE) → ENTER
    ├─► Score < 3.0 → HOLD/BLOCK
    └─► Additional gates: spread, notional, buying power, cooldown, etc.
    │
    ▼
ORDER CONSTRUCTION
    └─► Position sizing based on score, conviction, account equity


┌─────────────────────────────────────────────────────────────────────────┐
│                       EXIT-SIDE SCORING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────┘

POSITION STATE + CURRENT SIGNALS
    │
    ├─► Entry Score (historical)
    ├─► Current Composite Score
    ├─► Current P&L (%)
    ├─► Age (hours)
    ├─► High Water Mark (%)
    ├─► Flow Reversal Flag
    └─► Momentum
    │
    ▼
EXIT COMPONENT CALCULATION
    │
    ├─► entry_decay (weight: 1.0)
    │   └─► (1 - current_score/entry_score) if decay_ratio < 0.7
    │
    ├─► adverse_flow (weight: 1.2)
    │   └─► 2.0 * weight if flow reversal detected
    │
    ├─► drawdown_velocity (weight: 1.5)
    │   └─► min(3.0, drawdown/age_days) * 0.5 * weight if drawdown > 3%
    │
    ├─► time_decay (weight: 0.8)
    │   └─► min(2.0, (age_hours-72)/48) * weight if age > 72h
    │
    ├─► momentum_reversal (weight: 1.3)
    │   └─► abs(momentum) * weight if opposite momentum
    │
    ├─► volume_exhaustion (weight: 0.9)
    │   └─► (Reserved for future use)
    │
    ├─► support_break (weight: 1.4)
    │   └─► (Reserved for future use)
    │
    └─► loss_limit (fixed: 2.0)
        └─► +2.0 if current_pnl < -5.0%
    │
    ▼
ADAPTIVE MULTIPLIERS
    │
    └─► Per-component multipliers: 0.25x - 2.5x
        (Learned from exit timing outcomes)
    │
    ▼
EXIT URGENCY SCORE
    │
    └─► urgency = sum(all_weighted_components)
        urgency = clamp(0.0, 10.0)
    │
    ▼
EXIT RECOMMENDATION
    │
    ├─► urgency >= 6.0 → EXIT (immediate close)
    ├─► urgency >= 3.0 → REDUCE (partial close)
    └─► urgency < 3.0 → HOLD (continue monitoring)
    │
    ▼
ADDITIONAL EXIT TRIGGERS
    │
    ├─► Trailing Stop: price <= high_water * (1 - 1.5%)
    ├─► Profit Target: P&L >= 0.75% (full position)
    ├─► Stop Loss: P&L <= -1.0% (hard stop)
    ├─► Time Exit: age >= 240 minutes (4 hours)
    ├─► Stale Position: age >= 12 days AND P&L < 3%
    └─► Signal Decay: current_score < 60% of entry_score


═══════════════════════════════════════════════════════════════════════════
                          THRESHOLD DECISION TREE
═══════════════════════════════════════════════════════════════════════════

BUY DECISION:
    composite_score >= 3.0? ──YES──► Check gates (spread, notional, cooldown, etc.)
                        │
                       NO
                        │
                        └──► BLOCK (HOLD)

EXIT DECISION:
    exit_urgency >= 6.0? ──YES──► EXIT (immediate close)
                      │
                     NO
                      │
         exit_urgency >= 3.0? ──YES──► REDUCE (partial close)
                           │
                          NO
                           │
                           └──► HOLD (continue monitoring)

═══════════════════════════════════════════════════════════════════════════
```

---

## COMPONENT DETAILS

### Buy-Side Component Details

#### 1. options_flow (ANCHOR COMPONENT)
- **Weight:** 2.4 (base), 0.25x - 2.5x (adaptive)
- **Raw Input:** conviction (0.0 - 1.0), sentiment (BULLISH/BEARISH/NEUTRAL)
- **Normalization:**
  - Stealth flow boost: +0.2 if conviction < 0.3 (LOW magnitude)
  - Default conviction: 0.5 if missing (prevents zero contribution)
- **Formula:** `weight * min(1.0, conviction + stealth_boost)`
- **Max Contribution:** 2.4 * 2.5 * 1.0 = 6.0
- **Notes:** Primary anchor component. Currently adaptive weights disabled for this component (forced to use base 2.4) due to learning issues.

#### 2. dark_pool
- **Weight:** 1.3 (base), 0.25x - 2.5x (adaptive)
- **Raw Input:** total_premium/total_notional (USD), sentiment (BULLISH/BEARISH/NEUTRAL), print_count
- **Normalization:** Log-scaled: `0.5 + min(0.8, log10(premium)/7.5)`
- **Formula:** `weight * (0.5 + log_factor)` if BULLISH/BEARISH, else `weight * 0.2`
- **Max Contribution:** 1.3 * 2.5 * 1.3 = 4.225
- **Notes:** Neutral default 0.2x weight if no sentiment data.

#### 3. insider
- **Weight:** 0.5 (base), 0.25x - 2.5x (adaptive)
- **Raw Input:** sentiment, conviction_modifier (-0.05 to +0.05), net_buys, net_sells, total_usd
- **Normalization:**
  - BULLISH: `0.50 + modifier`
  - BEARISH: `0.50 - abs(modifier)`
  - NEUTRAL: `0.25`
- **Formula:** `weight * normalized_value`
- **Max Contribution:** 0.5 * 2.5 * 0.55 = 0.6875
- **Notes:** Shares data source with institutional component.

[... Additional component details in full documentation ...]

---

## NOTES & OBSERVATIONS

### Missing Data Handling
- Most components use **neutral default** (0.2x weight) instead of 0.0 when data is missing
- This prevents zero contributions from blocking all scoring
- Exceptions: Some components return 0.0 if critical data is missing (e.g., congress if recent_count == 0)

### Adaptive Multipliers
- **Range:** 0.25x - 2.5x (regime-aware)
- **Learning:** Continuous Bayesian updates based on trade outcomes
- **Regime-Specific:** Separate multipliers per regime (RISK_ON, RISK_OFF, MIXED)
- **Safety:** options_flow currently forced to base weight (2.4) due to learning issues

### Score Range Exceedance
- Theoretical max: 8.0 (clamped)
- Actual scores can exceed 5.0 due to:
  - Regime multipliers
  - Macro multipliers
  - Whale persistence bonuses
  - Whale conviction boost (+0.5)
- This is **expected behavior**, not a bug

### Unused/Reserved Components
- **Exit Components:** volume_exhaustion, support_break (defined but not actively used in exit urgency calculation)
- **Future Expansion:** These components are reserved for future enhancements

---

**Documentation Generated:** 2026-01-12  
**Source Files Analyzed:**
- `uw_composite_v2.py`
- `adaptive_signal_optimizer.py`
- `config/registry.py`
- `signals/uw_composite.py`

**Mode:** Extraction & Documentation Only (No Code Modifications)
