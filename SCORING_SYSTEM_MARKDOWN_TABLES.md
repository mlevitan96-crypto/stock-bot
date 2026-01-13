# STOCK-BOT SCORING SYSTEM - MARKDOWN TABLES

**Date:** 2026-01-12  
**Version:** V3.1  
**Purpose:** Markdown table exports for documentation and dashboard integration

---

## BUY-SIDE SCORING COMPONENTS

| Component | Category | Weight | Raw Range | Multiplier Range | Final Contribution Formula | Max Contribution | Notes |
|-----------|----------|--------|-----------|------------------|---------------------------|------------------|-------|
| **options_flow** | Core Flow | 2.4 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * min(1.0, conviction + stealth_boost)` | 6.0 | Primary anchor. Stealth boost +0.2 if LOW magnitude. Default 0.5 if missing. |
| **dark_pool** | Core Flow | 1.3 | 0.2 - 1.3 | 0.25x - 2.5x | `weight * (0.5 + log10(premium)/7.5)` if BULLISH/BEARISH else `weight * 0.2` | 4.225 | Log-scaled by notional. Neutral 0.2 if no sentiment. |
| **insider** | Core Flow | 0.5 | 0.125 - 0.55 | 0.25x - 2.5x | `weight * (0.50 ± modifier)` | 0.6875 | BULLISH: 0.50+mod, BEARISH: 0.50-abs(mod), NEUTRAL: 0.25. Modifier: -0.05 to +0.05 |
| **iv_term_skew** | V2 Features | 0.6 | -0.15 to +0.15 | 0.25x - 2.5x | `weight * abs(skew) * (1.3 if aligned else 0.7)` | 0.117 | Alignment bonus/penalty based on flow direction |
| **smile_slope** | V2 Features | 0.35 | -0.10 to +0.10 | 0.25x - 2.5x | `weight * abs(slope)` | 0.0875 | OTM call/put skew indicator |
| **whale_persistence** | V2 Features | 0.7 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * avg_conviction` | 1.75 | Sustained high conviction detection (whale motif) |
| **event_alignment** | V2 Features | 0.4 | 0.0 - 1.0 | 0.25x - 2.5x | `weight * event_align` | 1.0 | Earnings/FDA/economic event alignment |
| **temporal_motif** | V2 Features | 0.6 | 0.0 - variable | 0.25x - 2.5x | `weight * (staircase_slope*3.0 + burst_intensity/2.0)` | variable | Pattern detection (staircase, burst, sweep) |
| **toxicity_penalty** | V2 Features | **-0.9** | -1.35 to 0.0 | 0.25x - 2.5x | `weight * (toxicity - 0.5) * 1.5` if >0.5 | **-3.375** | **NEGATIVE weight** - penalizes signal disagreement |
| **regime_modifier** | V2 Features | 0.3 | variable | 0.25x - 2.5x | `weight * (regime_factor - 1.0) * 2.0` | 0.09 | RISK_ON: +1.15/+0.95, RISK_OFF: +1.10/+0.90, Mixed: +1.02 |
| **congress** | V3 Expanded | 0.9 | -0.36 to +0.9 | 0.25x - 2.5x | `weight * (0.6 + activity*0.4) * (1+boost)` if aligned | 2.25 | Politician trading. Neutral default 0.2x if missing |
| **shorts_squeeze** | V3 Expanded | 0.7 | -0.14 to +0.7 | 0.25x - 2.5x | `weight * (SI*0.5 + DTC*0.3 + squeeze*0.3)` if bullish | 1.75 | Short interest + days to cover + FTD. Neutral default 0.2x |
| **institutional** | V3 Expanded | 0.5 | -0.15 to +0.5 | 0.25x - 2.5x | `weight * (0.5 + activity*0.5 + usd_bonus)` if aligned | 1.25 | 13F filings & institutional activity. Neutral default 0.2x |
| **market_tide** | V3 Expanded | 0.4 | 0.08 to +0.4 | 0.25x - 2.5x | `weight * call_ratio * (1.0 if aligned else 0.5)` | 1.0 | Options market sentiment. Neutral default 0.2x |
| **calendar_catalyst** | V3 Expanded | 0.45 | 0.0 to +0.45 | 0.25x - 2.5x | `weight * (earnings*0.4 + FDA*0.5 + econ*0.2)` | 1.125 | Earnings/FDA/Economic events. Neutral default 0.2x |
| **etf_flow** | V3 Expanded | 0.3 | -0.09 to +0.3 | 0.25x - 2.5x | `weight * (1.0 if BULLISH+risk_on else 0.5 if BULLISH else -0.3 if BEARISH)` | 0.75 | ETF in/outflows. Neutral default 0.2x |
| **greeks_gamma** | V2 Full Intel | 0.4 | 0.04 to +0.4 | 0.25x - 2.5x | `weight * (1.0 if squeeze, 0.5/0.25/0.1/0.2 by exposure)` | 1.0 | Gamma exposure for squeeze detection. Neutral default 0.2x |
| **ftd_pressure** | V2 Full Intel | 0.3 | 0.06 to +0.3 | 0.25x - 2.5x | `weight * (1.0 if squeeze/200k+, 0.67/0.33/0.1/0.2 by count)` | 0.75 | Fails-to-deliver pressure. Neutral default 0.2x |
| **iv_rank** | V2 Full Intel | 0.2 | **-0.2 to +0.2** | 0.25x - 2.5x | `weight * (1.0 if <20, 0.5 if <30, **-1.0** if >80, **-0.5** if >70, 0.15 if 30-70)` | 0.5 | **CAN BE NEGATIVE** - high IV = caution, low IV = opportunity |
| **oi_change** | V2 Full Intel | 0.35 | 0.035 to +0.35 | 0.25x - 2.5x | `weight * (1.0 if >50k aligned, 0.57/0.29/0.1/0.2 by net_oi)` | 0.875 | Open interest changes. Neutral default 0.2x |
| **squeeze_score** | V2 Full Intel | 0.2 | 0.04 to +0.2 | 0.25x - 2.5x | `weight * (1.0 if high, 0.5 if signals>=1, 0.2 if neutral)` | 0.5 | Combined squeeze indicator. Neutral default 0.2x |

**Total Components:** 21  
**Score Range:** 0.0 - 8.0 (clamped, but can exceed 5.0 due to multipliers)  
**Primary Anchor:** options_flow (weight 2.4)  
**Negative Components:** toxicity_penalty (-0.9), iv_rank (can be negative)

---

## EXIT-SIDE SCORING COMPONENTS

| Component | Base Weight | Raw Range | Multiplier Range | Final Contribution Formula | Trigger Condition | Max Contribution | Notes |
|-----------|-------------|-----------|------------------|---------------------------|-------------------|------------------|-------|
| **entry_decay** | 1.0 | 0.0 - 1.0 | 0.25x - 2.5x | `(1 - decay_ratio) * weight` | current_score/entry_score < 0.7 (30%+ decay) | 2.5 | Signal decay detection |
| **adverse_flow** | 1.2 | 0.0 - 2.4 | 0.25x - 2.5x | `2.0 * weight` | Flow reversal (LONG+BEARISH or SHORT+BULLISH) | 6.0 | Major exit signal |
| **drawdown_velocity** | 1.5 | 0.0 - 4.5 | 0.25x - 2.5x | `min(3.0, drawdown/age_days) * 0.5 * weight` | drawdown > 3.0% | 11.25 | Velocity-based drawdown |
| **time_decay** | 0.8 | 0.0 - 1.6 | 0.25x - 2.5x | `min(2.0, (age_hours-72)/48) * weight` | age_hours > 72 (3 days) | 4.0 | Time-based decay |
| **momentum_reversal** | 1.3 | 0.0 - variable | 0.25x - 2.5x | `abs(momentum) * weight` | (LONG AND momentum<-0.5) OR (SHORT AND momentum>0.5) | variable | Momentum reversal |
| **volume_exhaustion** | 0.9 | 0.0 - variable | 0.25x - 2.5x | RESERVED | RESERVED | N/A | Not actively used |
| **support_break** | 1.4 | 0.0 - variable | 0.25x - 2.5x | RESERVED | RESERVED | N/A | Not actively used |
| **loss_limit** | 2.0 (fixed) | 0.0 - 2.0 | N/A | `2.0` (fixed) | current_pnl < -5.0% | 2.0 | Hard-coded override |

**Total Components:** 8 (5 active, 2 reserved, 1 fixed)  
**Urgency Range:** 0.0 - 10.0 (clamped)  
**Exit Thresholds:** EXIT ≥ 6.0, REDUCE ≥ 3.0, HOLD < 3.0

---

## THRESHOLDS SUMMARY

### Buy-Side Thresholds

| Threshold | Value | Source |
|-----------|-------|--------|
| MIN_EXEC_SCORE | 3.0 | config/registry.py |
| MIN_NOTIONAL_USD | $100 | Config.MIN_NOTIONAL_USD |
| MAX_SPREAD_BPS | 50 | Config.MAX_SPREAD_BPS |
| Score Max | 8.0 | Clamped in code |

### Exit-Side Thresholds

| Threshold | Value | Recommendation | Source |
|-----------|-------|----------------|--------|
| EXIT | ≥ 6.0 | Immediate close | adaptive_signal_optimizer.py |
| REDUCE | ≥ 3.0 | Partial close | adaptive_signal_optimizer.py |
| HOLD | < 3.0 | Continue monitoring | adaptive_signal_optimizer.py |
| TRAILING_STOP_PCT | 1.5% | Trailing stop | config/registry.py |
| TIME_EXIT_MINUTES | 240 | Time-based exit | config/registry.py |
| TIME_EXIT_DAYS_STALE | 12 | Stale position exit | config/registry.py |
| STOP_LOSS_PCT | -1.0% | Hard stop | main.py evaluate_exits |
| PROFIT_TARGET_PCT | 0.75% | Profit target | main.py evaluate_exits |

---

## KEY OBSERVATIONS

1. **Adaptive Multipliers:** All components support 0.25x - 2.5x multipliers (regime-aware)
2. **Missing Data:** Most components use neutral default (0.2x weight) instead of 0.0
3. **Negative Components:** toxicity_penalty (always negative), iv_rank (can be negative)
4. **Score Exceedance:** Scores can exceed 5.0 due to multipliers and bonuses (expected)
5. **Unused Components:** volume_exhaustion and support_break are reserved for future use

---

**Last Updated:** 2026-01-12  
**Source Files:** uw_composite_v2.py, adaptive_signal_optimizer.py, config/registry.py
