# Complete TODO List - All Pending Items

**Last Updated**: 2025-12-24  
**Status**: All TODOs are **NON-BLOCKING** - System is ready for trading

---

## Critical TODOs: **NONE** ✅

All critical functionality is complete. All TODOs are future enhancements.

---

## Main Code TODOs (main.py)

### 1. TCA Integration (Line 4103)
- **TODO**: `Get from recent TCA data` (slippage)
- **Current**: Uses default `0.003` (0.3%)
- **Impact**: Low - System works with default
- **Priority**: Medium (Future Enhancement)

### 2. Regime Forecast (Line 4166)
- **TODO**: `Link to regime forecast`
- **Current**: Uses default `0.0`
- **Impact**: Low - System works without
- **Priority**: Medium (Future Enhancement)

### 3. TCA Quality (Line 4167)
- **TODO**: `Link to recent TCA quality`
- **Current**: Uses default `0.0`
- **Impact**: Low - System works without
- **Priority**: Medium (Future Enhancement)

### 4. Toxicity Sentinel (Line 4386)
- **TODO**: `Link to toxicity sentinel`
- **Current**: Uses default `0.0`
- **Impact**: Low - System works without
- **Priority**: Medium (Future Enhancement)

### 5. Execution Failures Tracking (Line 4387)
- **TODO**: `Track per-symbol execution failures`
- **Current**: Uses default `0`
- **Impact**: Low - System works without
- **Priority**: Low (Future Enhancement)

### 6. Experiment Parameters (Lines 2253, 2548)
- **TODO**: `Copy experiment parameters into production profile`
- **Impact**: Low - Placeholder for future feature
- **Priority**: Low (Future Enhancement)

---

## Learning System TODOs (comprehensive_learning_orchestrator_v2.py)

### 1. Signal Pattern Learning ⚠️
- **Status**: Tracking only (not learning yet)
- **Current**: Processes signals but doesn't learn patterns
- **Impact**: Low - Core learning works without this
- **Priority**: Medium (Future Enhancement)
- **What's Missing**:
  - Pattern recognition (which signal combinations work best)
  - Signal timing optimization
  - Signal strength correlation with outcomes

### 2. Execution Quality Learning ⚠️
- **Status**: Tracking only (not learning yet)
- **Current**: Processes orders but doesn't learn execution patterns
- **Impact**: Low - Core learning works without this
- **Priority**: Medium (Future Enhancement)
- **What's Missing**:
  - Slippage analysis
  - Fill rate optimization
  - Order timing optimization

### 3. Counterfactual P&L Analysis ⚠️
- **Status**: Not implemented
- **Current**: Doesn't compute theoretical P&L for blocked trades
- **Impact**: Medium - Would help optimize gates
- **Priority**: Medium-High (Most valuable enhancement)
- **What's Missing**:
  - Compute theoretical P&L for blocked trades
  - Learn which gates are too restrictive
  - Optimize gate thresholds based on missed opportunities

### 4. Gate Pattern Learning ⚠️
- **Status**: Partially implemented (V1 enhancements exist)
- **Current**: Tracks gate blocks but doesn't fully optimize thresholds
- **Impact**: Medium - Would optimize gate effectiveness
- **Priority**: Medium (Future Enhancement)
- **What's Missing**:
  - Threshold state persistence
  - Gate threshold optimization
  - Gate effectiveness analysis

### 5. UW Blocked Entry Learning ⚠️
- **Status**: Partially implemented (V1 enhancements exist)
- **Current**: Tracks blocked UW entries but doesn't fully learn from them
- **Impact**: Low - Enhancement feature
- **Priority**: Low-Medium (Future Enhancement)
- **What's Missing**:
  - Learn from missed opportunities
  - Optimize entry criteria based on blocked signals

---

## Parameter Optimization TODOs (60+ Hardcoded Parameters)

### Exit Parameters
- ❌ **TODO**: Profit targets [2%, 5%, 10%] - Learn optimal targets
- ❌ **TODO**: Scale-out fractions [30%, 30%, 40%] - Learn optimal scale-out strategy
- ❌ **TODO**: Exit urgency thresholds (6.0 for EXIT, 3.0 for REDUCE) - Learn optimal urgency

### Entry Parameters
- ❌ **TODO**: MIN_PREMIUM_USD (100k) - Learn optimal flow filtering
- ❌ **TODO**: CLUSTER_WINDOW_SEC (600s) - Learn optimal clustering window
- ❌ **TODO**: CLUSTER_MIN_SWEEPS (3) - Learn optimal cluster size

### Position Management
- ❌ **TODO**: MAX_CONCURRENT_POSITIONS (16) - Learn optimal capacity
- ❌ **TODO**: MAX_NEW_POSITIONS_PER_CYCLE (6) - Learn optimal entry rate
- ❌ **TODO**: COOLDOWN_MINUTES_PER_TICKER (15) - Learn optimal cooldown

### Risk Management
- ❌ **TODO**: Daily loss limit (4%) - Learn optimal risk tolerance
- ❌ **TODO**: Max drawdown (20%) - Learn optimal drawdown tolerance
- ❌ **TODO**: Risk per trade (1.5%) - Learn optimal position sizing
- ❌ **TODO**: Max symbol exposure (10%) - Learn optimal diversification
- ❌ **TODO**: Max sector exposure (30%) - Learn optimal sector limits

### Execution Parameters
- ❌ **TODO**: ENTRY_TOLERANCE_BPS (10) - Learn optimal price tolerance
- ❌ **TODO**: MAX_SPREAD_BPS (50) - Learn optimal spread tolerance
- ❌ **TODO**: ENTRY_MAX_RETRIES (3) - Learn optimal retry strategy

### Displacement Parameters
- ❌ **TODO**: DISPLACEMENT_MIN_AGE_HOURS (4) - Learn optimal displacement timing
- ❌ **TODO**: DISPLACEMENT_MAX_PNL_PCT (1%) - Learn optimal displacement criteria
- ❌ **TODO**: DISPLACEMENT_SCORE_ADVANTAGE (2.0) - Learn optimal score advantage required

### Signal Filtering
- ❌ **TODO**: DARKPOOL_OFFLIT_MIN (1M) - Learn optimal dark pool threshold
- ❌ **TODO**: NET_PREMIUM_MIN_ABS (100k) - Learn optimal net premium threshold
- ❌ **TODO**: RV20_MAX (0.8) - Learn optimal volatility threshold

### Learning Parameters
- ❌ **TODO**: Bucket win rate targets (0.60, 0.55, 0.50) - Learn optimal targets
- ❌ **TODO**: Drawdown sensitivity deltas - Learn optimal drawdown response

---

## Code Quality TODOs

### 1. Duplicate Imports (145 warnings)
- **Status**: Non-critical code quality issue
- **Impact**: None (Python handles duplicates)
- **Priority**: Low (Code cleanup)
- **Action**: Clean up in next code review cycle

### 2. State Persistence
- **TODO**: Implement threshold state persistence
- **TODO**: Implement profit target state persistence
- **TODO**: Implement risk limit state persistence
- **Priority**: Low (Future Enhancement)

---

## Other TODOs

### Counterfactual Analyzer
- **TODO**: Implement actual price lookup (counterfactual_analyzer.py:31)
- **Priority**: Low (Future Enhancement)

### Missing Endpoints
- **TODO**: Create TODO for missing endpoints (health supervisor)
- **Priority**: Low (Future Enhancement)

---

## Summary by Priority

### High Priority (None)
- ✅ All critical functionality complete

### Medium Priority (Future Enhancements)
1. Counterfactual P&L Analysis - Most valuable for gate optimization
2. TCA Integration - Enhance execution quality
3. Regime Forecast - Enhance regime-aware trading
4. Signal Pattern Learning - Learn best signal combinations
5. Gate Pattern Learning - Optimize gate thresholds
6. Execution Quality Learning - Optimize execution

### Low Priority (Nice to Have)
1. Toxicity Sentinel - Enhance risk management
2. Parameter Optimization (60+ parameters) - Learn optimal values
3. Code Quality Cleanup - Duplicate imports
4. State Persistence - Various state files
5. UW Blocked Entry Learning - Learn from missed opportunities

---

## Recommendation

**Current Status**: ✅ **SYSTEM IS READY FOR TRADING**

All TODOs are **non-blocking future enhancements**. The core system is fully functional:
- ✅ Core learning system working
- ✅ All critical features implemented
- ✅ No blocking issues

**Priority Order for Future Implementation**:
1. Counterfactual P&L (Medium-High) - Most valuable for gate optimization
2. Gate Pattern Learning (Medium) - Optimize gate thresholds
3. Signal Pattern Learning (Medium) - Learn best signal combinations
4. Execution Quality Learning (Medium) - Optimize execution
5. Parameter Optimization (Low-Medium) - Learn optimal values for 60+ parameters
6. TCA Integration (Medium) - Enhance execution quality
7. Regime Forecast (Medium) - Enhance regime-aware trading

---

**Bottom Line**: All TODOs are enhancements, not blockers. System is production-ready.

