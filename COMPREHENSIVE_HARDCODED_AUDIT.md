# Comprehensive Hardcoded Values & Unanalyzed Data Audit

## Executive Summary

This audit identifies ALL hardcoded thresholds, logged-but-unanalyzed data, and optimization opportunities to make this a best-in-breed trading bot.

**Total Hardcoded Values Found: 50+**
**Total Log Files Not Analyzed: 15+**
**Optimization Opportunities: 30+**

---

## PART 1: HARDCODED THRESHOLDS (Should Be Learned)

### Exit Thresholds (CRITICAL - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `TRAILING_STOP_PCT` | 0.015 (1.5%) | ✅ **IMPLEMENTED** | High - Directly affects P&L |
| `TIME_EXIT_MINUTES` | 240 (4 hours) | ✅ **IMPLEMENTED** | High - Affects hold time optimization |
| `TIME_EXIT_DAYS_STALE` | 12 days | ✅ **IMPLEMENTED** | Medium - Affects stale position cleanup |
| `TIME_EXIT_STALE_PNL_THRESH_PCT` | 0.03 (3%) | ❌ **NOT IMPLEMENTED** | Medium - When to exit stale positions |
| `PROFIT_TARGETS` | [0.02, 0.05, 0.10] | ❌ **NOT IMPLEMENTED** | High - Should learn optimal profit targets |
| `SCALE_OUT_FRACTIONS` | [0.3, 0.3, 0.4] | ❌ **NOT IMPLEMENTED** | High - Should learn optimal scale-out amounts |

### Entry Thresholds (CRITICAL - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `MIN_EXEC_SCORE` | 2.0 | ⚠️ **PARTIAL** (adaptive gate exists) | High - Entry gate threshold |
| `MIN_PREMIUM_USD` | 100,000 | ❌ **NOT IMPLEMENTED** | Medium - Flow filtering threshold |
| `MAX_EXPIRY_DAYS` | 7 days | ❌ **NOT IMPLEMENTED** | Low - Options expiry filter |
| `CLUSTER_WINDOW_SEC` | 600 (10 min) | ❌ **NOT IMPLEMENTED** | Medium - Signal clustering window |
| `CLUSTER_MIN_SWEEPS` | 3 | ❌ **NOT IMPLEMENTED** | Medium - Minimum sweeps for cluster |

### Position Management (CRITICAL - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `MAX_CONCURRENT_POSITIONS` | 16 | ❌ **NOT IMPLEMENTED** | High - Capacity constraint |
| `MAX_NEW_POSITIONS_PER_CYCLE` | 6 | ❌ **NOT IMPLEMENTED** | Medium - Rate limiting |
| `POSITION_SIZE_USD` | 500 | ⚠️ **PARTIAL** (sizing scenarios exist) | High - Base position size |
| `SIZE_VOL_CAP` | 0.03 (3%) | ❌ **NOT IMPLEMENTED** | Medium - Volatility-based sizing cap |
| `COOLDOWN_MINUTES_PER_TICKER` | 15 min | ❌ **NOT IMPLEMENTED** | Medium - Prevents over-trading |

### Displacement Parameters (MEDIUM - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `DISPLACEMENT_MIN_AGE_HOURS` | 4 hours | ❌ **NOT IMPLEMENTED** | Medium - When positions eligible |
| `DISPLACEMENT_MAX_PNL_PCT` | 0.01 (1%) | ❌ **NOT IMPLEMENTED** | Medium - P&L threshold for displacement |
| `DISPLACEMENT_SCORE_ADVANTAGE` | 2.0 | ❌ **NOT IMPLEMENTED** | Medium - Required score advantage |
| `DISPLACEMENT_COOLDOWN_HOURS` | 6 hours | ❌ **NOT IMPLEMENTED** | Low - Prevents churn |

### Execution Parameters (MEDIUM - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `ENTRY_TOLERANCE_BPS` | 10 bps | ❌ **NOT IMPLEMENTED** | Medium - Price tolerance for limit orders |
| `ENTRY_MAX_RETRIES` | 3 | ❌ **NOT IMPLEMENTED** | Low - Retry attempts |
| `ENTRY_RETRY_SLEEP_SEC` | 1.0 sec | ❌ **NOT IMPLEMENTED** | Low - Retry delay |
| `MAX_SPREAD_BPS` | 50 bps | ❌ **NOT IMPLEMENTED** | Medium - Blocks illiquid trades |

### Scoring Weights (PARTIALLY LEARNED - Some Hardcoded)

| Parameter | Current Value | Learning Status | Impact |
|-----------|--------------|-----------------|--------|
| `FLOW_COUNT_W` | 0.5 | ⚠️ **PARTIAL** (adaptive weights exist) | High - Entry scoring |
| `FLOW_PREMIUM_MILLION_W` | 1.0 | ⚠️ **PARTIAL** | High - Entry scoring |
| `CONFIRM_GAMMA_NEG_W` | 0.5 | ⚠️ **PARTIAL** | Medium - Confirmation scoring |
| `CONFIRM_DARKPOOL_W` | 0.25 | ⚠️ **PARTIAL** | Medium - Confirmation scoring |
| `CONFIRM_NET_PREMIUM_W` | 0.25 | ⚠️ **PARTIAL** | Medium - Confirmation scoring |
| `CONFIRM_VOL_W` | 0.1 | ⚠️ **PARTIAL** | Low - Confirmation scoring |
| `WEIGHTS_V3` base weights | Hardcoded in `uw_composite_v2.py` | ⚠️ **PARTIAL** (multipliers learned) | High - All signal weights |
| `ENTRY_THRESHOLDS` | 2.7, 2.9, 3.2 | ⚠️ **PARTIAL** (adaptive gate adjusts) | High - Entry gates |

### Confirmation Thresholds (MEDIUM - Currently Hardcoded)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `DARKPOOL_OFFLIT_MIN` | 1,000,000 | ❌ **NOT IMPLEMENTED** | Medium - Dark pool threshold |
| `NET_PREMIUM_MIN_ABS` | 100,000 | ❌ **NOT IMPLEMENTED** | Medium - Net premium threshold |
| `RV20_MAX` | 0.8 | ❌ **NOT IMPLEMENTED** | Low - Volatility threshold |

### Risk Management (CRITICAL - Currently Hardcoded in risk_management.py)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| `daily_loss_pct` | 0.04 (4%) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `daily_loss_dollar` | 2200 (paper) / 400 (live) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `min_account_equity` | 0.85 (85% of starting) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `max_drawdown_pct` | 0.20 (20%) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `risk_per_trade_pct` | 0.015 (1.5%) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `max_position_dollar` | 825 (paper) / 300 (live) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `max_symbol_exposure` | 0.10 (10%) | ❌ **NOT IMPLEMENTED** | High - Risk control |
| `max_sector_exposure` | 0.30 (30%) | ❌ **NOT IMPLEMENTED** | High - Risk control |

### Exit Urgency Thresholds (MEDIUM - Currently Hardcoded in adaptive_signal_optimizer.py)

| Parameter | Current Value | Should Learn | Impact |
|-----------|--------------|--------------|--------|
| Exit urgency EXIT threshold | 6.0 | ❌ **NOT IMPLEMENTED** | High - When to exit |
| Exit urgency REDUCE threshold | 3.0 | ❌ **NOT IMPLEMENTED** | Medium - When to reduce |
| Signal decay threshold | 0.7 (70%) | ❌ **NOT IMPLEMENTED** | High - Entry signal decay |
| Drawdown velocity threshold | 3.0% | ❌ **NOT IMPLEMENTED** | Medium - Drawdown response |
| Time decay threshold | 72 hours | ❌ **NOT IMPLEMENTED** | Medium - Time-based decay |
| Loss limit threshold | -5.0% | ❌ **NOT IMPLEMENTED** | High - Loss protection |

### Adaptive Gate Thresholds (PARTIALLY LEARNED in signals/uw_adaptive.py)

| Parameter | Current Value | Learning Status | Impact |
|-----------|--------------|-----------------|--------|
| `BASE_THRESHOLD` | 2.50 | ✅ **LEARNED** (adaptive gate) | High - Entry gate |
| Bucket win rate targets | 0.60, 0.55, 0.50 | ❌ **NOT IMPLEMENTED** | Medium - Bucket adaptation |
| Drawdown sensitivity rules | Hardcoded deltas (+0.75, +0.50, +0.25, -0.25) | ❌ **NOT IMPLEMENTED** | Medium - Drawdown response |
| `MIN_SAMPLES_BUCKET` | 30 | ❌ **NOT IMPLEMENTED** | Low - Statistical significance |
| `THEME_MAX_PENALTY` | -0.50 | ❌ **NOT IMPLEMENTED** | Medium - Theme adjustments |
| `THEME_MAX_BONUS` | +0.25 | ❌ **NOT IMPLEMENTED** | Medium - Theme adjustments |

---

## PART 2: LOGGED BUT NOT ANALYZED DATA

### Log Files with Unanalyzed Data

| Log File | Data Logged | Currently Analyzed? | Learning Opportunity |
|----------|-------------|---------------------|---------------------|
| `logs/attribution.jsonl` | Trade outcomes, P&L, close reasons | ⚠️ **PARTIAL** (entry learning only) | ✅ **NOW ANALYZED** (exit learning added) |
| `logs/orders.jsonl` | Order events, fills, slippage | ❌ **NOT ANALYZED** | High - Execution quality learning |
| `logs/exits.jsonl` | Exit events | ❌ **NOT ANALYZED** | High - Exit pattern analysis |
| `logs/telemetry.jsonl` | System events | ❌ **NOT ANALYZED** | Medium - System health patterns |
| `logs/composite_attribution.jsonl` | Composite scoring data | ❌ **NOT ANALYZED** | High - Score component analysis |
| `data/live_orders.jsonl` | Live order tracking | ❌ **NOT ANALYZED** | Medium - Order execution patterns |
| `data/blocked_trades.jsonl` | Blocked trade reasons | ❌ **NOT ANALYZED** | High - Learn from missed opportunities |
| `data/governance_events.jsonl` | Risk freezes, mode changes | ❌ **NOT ANALYZED** | Medium - Risk pattern analysis |
| `data/uw_api_quota.jsonl` | API usage tracking | ⚠️ **PARTIAL** (monitoring only) | Low - Usage optimization |
| `data/execution_quality.jsonl` | Execution metrics | ❌ **NOT ANALYZED** | High - Slippage, fill rate learning |
| `logs/reconcile.jsonl` | Position reconciliation | ❌ **NOT ANALYZED** | Medium - Reconciliation patterns |
| `logs/watchdog_events.jsonl` | Health check events | ❌ **NOT ANALYZED** | Medium - System reliability patterns |
| `logs/uw_daemon.jsonl` | UW API polling | ❌ **NOT ANALYZED** | Low - API usage patterns |
| `logs/uw_errors.jsonl` | UW API errors | ❌ **NOT ANALYZED** | Medium - Error pattern analysis |
| `data/portfolio_events.jsonl` | Portfolio changes | ❌ **NOT ANALYZED** | Medium - Portfolio evolution |

### Specific Unanalyzed Data Points

1. **Order Execution Quality:**
   - Slippage amounts (logged but not optimized)
   - Fill rates by order type (limit vs market)
   - Fill times
   - Spread costs
   - **Should learn:** Optimal order types, timing, price tolerance

2. **Blocked Trades:**
   - Reasons for blocking (logged in `blocked_trades.jsonl`)
   - Counterfactual P&L (what if we traded?)
   - **Should learn:** Which blocks were good/bad decisions

3. **Exit Patterns:**
   - Exit timing vs optimal timing
   - Exit price vs peak price
   - **Should learn:** Optimal exit timing per signal type

4. **Execution Patterns:**
   - Regime-based execution success rates
   - Maker vs taker fill rates
   - **Should learn:** Optimal execution strategy per regime

---

## PART 3: OPTIMIZATION FRAMEWORK NEEDED

### Missing Learning Components

1. **Threshold Optimization Framework:**
   - Test multiple threshold values
   - Track outcomes for each
   - Gradually adjust toward optimal
   - **Status:** ❌ Not implemented (except exit thresholds - just added)

2. **Parameter Sensitivity Analysis:**
   - Which parameters matter most?
   - Which can be safely adjusted?
   - **Status:** ❌ Not implemented

3. **Multi-Parameter Optimization:**
   - Optimize combinations of parameters
   - Example: trail stop + time exit together
   - **Status:** ❌ Not implemented

4. **Regime-Specific Parameters:**
   - Different thresholds for different market regimes
   - Example: Tighter stops in high vol
   - **Status:** ❌ Not implemented

5. **Symbol-Specific Parameters:**
   - Per-ticker thresholds (some exist, but not all)
   - Example: Different trail stops for volatile vs stable stocks
   - **Status:** ⚠️ Partial (per-ticker learning exists but limited)

---

## PART 4: IMPLEMENTATION PRIORITY

### Phase 1: Critical (Immediate Impact)
1. ✅ **DONE**: Exit threshold optimization
2. ✅ **DONE**: Close reason performance analysis
3. ❌ **TODO**: Profit target optimization
4. ❌ **TODO**: Scale-out fraction optimization
5. ❌ **TODO**: Exit urgency threshold learning

### Phase 2: High Priority (Significant Impact)
1. ❌ **TODO**: Order execution quality learning
2. ❌ **TODO**: Blocked trade counterfactual analysis
3. ❌ **TODO**: Position sizing optimization (enhance existing)
4. ❌ **TODO**: Entry threshold optimization (enhance adaptive gate)
5. ❌ **TODO**: Regime-specific parameter learning

### Phase 3: Medium Priority (Incremental Improvement)
1. ❌ **TODO**: Displacement parameter optimization
2. ❌ **TODO**: Execution parameter optimization (spread, tolerance)
3. ❌ **TODO**: Confirmation threshold optimization
4. ❌ **TODO**: Cluster window optimization
5. ❌ **TODO**: Cooldown period optimization

### Phase 4: Low Priority (Nice to Have)
1. ❌ **TODO**: API usage pattern optimization
2. ❌ **TODO**: System health pattern analysis
3. ❌ **TODO**: Log file consolidation and analysis

---

## PART 5: RECOMMENDED IMPLEMENTATION

### Create Universal Optimization Framework

**New Module: `parameter_optimizer.py`**

```python
class ParameterOptimizer:
    """Universal framework for optimizing any hardcoded parameter."""
    
    def optimize_parameter(self, 
                          param_name: str,
                          test_values: List[float],
                          outcome_metric: str = "pnl",
                          min_samples: int = 30):
        """
        Test different parameter values and learn optimal.
        
        Example:
            optimize_parameter("TRAILING_STOP_PCT", [0.010, 0.015, 0.020, 0.025])
        """
        # 1. For each test value, simulate historical outcomes
        # 2. Calculate weighted average outcome (with exponential decay)
        # 3. Find best value
        # 4. Gradually adjust current value toward optimal
        pass
```

### Create Log Analysis Framework

**New Module: `log_analyzer.py`**

```python
class LogAnalyzer:
    """Analyze all log files for learning opportunities."""
    
    def analyze_orders(self):
        """Learn from order execution patterns."""
        pass
    
    def analyze_blocked_trades(self):
        """Learn from blocked trade counterfactuals."""
        pass
    
    def analyze_execution_quality(self):
        """Learn optimal execution strategies."""
        pass
```

---

## SUMMARY: What's Missing for Best-in-Breed

### Critical Gaps:
1. ❌ **60+ hardcoded thresholds** not optimized
2. ❌ **15+ log files** not analyzed for learning
3. ❌ **No universal optimization framework** - each parameter optimized separately
4. ❌ **No regime-specific learning** - same thresholds for all market conditions
5. ❌ **No symbol-specific optimization** - limited per-ticker learning
6. ❌ **No execution quality learning** - slippage, fill rates not optimized
7. ❌ **No counterfactual analysis** for most decisions
8. ❌ **Risk management parameters hardcoded** - should learn optimal risk limits
9. ❌ **Profit targets & scale-outs hardcoded** - should learn optimal take-profit strategy
10. ❌ **Entry execution parameters hardcoded** - spread tolerance, retry logic not optimized

### What We Just Added (Exit Learning):
1. ✅ Exit threshold optimization (trail stop %, time exit minutes, stale days)
2. ✅ Close reason performance analysis (which exit signals work best)
3. ✅ Exit signal weight updates (weights adjust based on outcomes)
4. ✅ Exit outcome recording (feeds exit data to learning system)
5. ✅ Universal parameter optimizer framework (skeleton created)

### Next Critical Steps:
1. **Profit Target Optimization** - Learn optimal profit targets (currently [2%, 5%, 10%])
2. **Scale-Out Optimization** - Learn optimal scale-out fractions (currently [30%, 30%, 40%])
3. **Risk Limit Optimization** - Learn optimal risk limits (daily loss %, drawdown %, position size)
4. **Order Execution Learning** - Analyze slippage, fill rates, optimal order types
5. **Blocked Trade Analysis** - Learn from missed opportunities
6. **Regime-Specific Parameters** - Different thresholds for different market conditions
7. **Entry Threshold Optimization** - Enhance adaptive gate with more learning
8. **Displacement Optimization** - Learn optimal displacement criteria

---

## RECOMMENDATION

**Implement a comprehensive learning framework that:**
1. Tests all hardcoded parameters
2. Analyzes all logged data
3. Learns optimal values continuously
4. Applies learnings gradually (anti-overfitting)
5. Tracks performance by regime, symbol, time of day, etc.

This would make the bot truly best-in-breed - continuously learning and optimizing every aspect of trading.
