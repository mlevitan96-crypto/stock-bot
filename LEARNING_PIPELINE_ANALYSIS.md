# Learning Pipeline Analysis & Verification

## Critical Finding: Learning Pipeline May Not Be Active

Based on code analysis, there are several potential gaps in the learning pipeline that could prevent the bot from learning from collected data.

## Data Flow Analysis

### 1. Trade Logging ✅
**Status**: Working
- `log_exit_attribution()` is called when positions close (line 3360, 3813)
- Logs to `logs/attribution.jsonl` with:
  - P&L (USD and %)
  - Entry/exit prices
  - Components (signal values at entry)
  - Market regime
  - Close reason

### 2. Learning System Initialization ⚠️
**Status**: Conditional
- Adaptive optimizer is lazy-loaded via `get_optimizer()` (line 62-66)
- Only initialized when first accessed
- State loaded from `state/signal_weights.json` if exists
- **Issue**: If optimizer never accessed, learning never starts

### 3. Trade Recording ⚠️
**Status**: Has Issues

**Entry Learning**:
- `record_trade_for_learning()` is called from `learn_from_outcomes()` (line 1973)
- **CRITICAL ISSUE**: Uses `reward` (pnl_usd) instead of `pnl_pct` for learning
  ```python
  record_trade_for_learning(comps, reward, regime, sector)
  # reward is pnl_usd (could be $100 or $1000), not percentage
  # Learning system expects pnl as percentage (0.025 for 2.5%)
  ```

**Exit Learning**:
- `log_exit_attribution()` attempts to feed exit signals (line 1053-1102)
- Parses close reason to extract exit components
- **Issue**: Only processes if `pnl_pct != 0`, may miss breakeven trades

### 4. Log Processing ⚠️
**Status**: Limited Scope

**`learn_from_outcomes()` Function** (line 1927):
- **CRITICAL LIMITATION**: Only processes TODAY's trades
  ```python
  if not rec.get("ts", "").startswith(today):
      continue  # Skips all historical trades
  ```
- Only runs if `ENABLE_PER_TICKER_LEARNING=true`
- Only called daily after market close (line 5357)
- **Issue**: Historical trades are never processed

**Weight Updates**:
- `update_weights()` only called if `trades_processed >= 5` (line 1979)
- Requires minimum 30 samples per component to adjust weights
- **Issue**: If <5 trades today, no weight update happens

### 5. Weight Application ⚠️
**Status**: Conditional

**Composite Scoring**:
- `uw_composite_v2.py` uses `get_adaptive_weights()` (line 44-49)
- Falls back to static `WEIGHTS_V3` if adaptive not available
- **Issue**: If optimizer not initialized, static weights always used

**Weight Export**:
- `get_weights_for_composite()` exports effective weights
- Merges base weights with adaptive multipliers
- **Issue**: If multipliers never updated, same as static weights

## Identified Issues

### Issue 1: Historical Trades Not Processed
**Problem**: `learn_from_outcomes()` only processes today's trades
**Impact**: Historical data is ignored, learning starts from scratch daily
**Fix Needed**: Process all unprocessed trades, not just today's

### Issue 2: P&L Format Mismatch
**Problem**: `record_trade_for_learning()` receives `pnl_usd` but learning expects `pnl_pct`
**Impact**: Learning system receives wrong scale (dollars vs percentages)
**Fix Needed**: Pass `pnl_pct / 100.0` instead of `pnl_usd`

### Issue 3: Learning Only Runs Daily
**Problem**: `learn_from_outcomes()` only called after market close
**Impact**: Trades closed during day aren't learned from until EOD
**Fix Needed**: Call after each trade close, or batch process more frequently

### Issue 4: Minimum Sample Threshold
**Problem**: Requires 30+ samples per component before adjusting weights
**Impact**: New components or low-frequency signals never learn
**Fix Needed**: Lower threshold or use different learning approach for low-sample components

### Issue 5: No Verification of Learning
**Problem**: No health checks to verify learning is working
**Impact**: Silent failures go undetected
**Fix Needed**: Add learning health checks to monitoring

## Verification Checklist

Run `VERIFY_LEARNING_PIPELINE.py` to check:

- [ ] Log files exist and have recent data
- [ ] Learning state file exists (`state/signal_weights.json`)
- [ ] Components have sample counts > 0
- [ ] Multipliers have changed from default (1.0)
- [ ] Learning log has update records
- [ ] Adaptive optimizer is initialized
- [ ] Composite scoring uses adaptive weights
- [ ] No optimizer errors in `data/optimizer_errors.jsonl`

## Recommended Fixes

### Fix 1: Process Historical Trades
```python
def learn_from_outcomes(process_all=False):
    # If process_all=True, process all unprocessed trades
    # Track last processed trade ID to avoid duplicates
```

### Fix 2: Fix P&L Format
```python
# In learn_from_outcomes(), line 1973:
pnl_pct = float(rec.get("pnl_pct", 0)) / 100.0  # Convert % to decimal
record_trade_for_learning(comps, pnl_pct, regime, sector)
```

### Fix 3: Continuous Learning
```python
# Call after each trade close:
def log_exit_attribution(...):
    # ... existing logging ...
    
    # Immediately feed to learning (don't wait for EOD)
    try:
        pnl_pct = context.get("pnl_pct", 0) / 100.0
        record_trade_for_learning(comps, pnl_pct, regime, sector)
        
        # Trigger weight update if enough samples
        optimizer = _get_adaptive_optimizer()
        if optimizer and optimizer.learner.learning_history >= 30:
            optimizer.update_weights()
    except:
        pass
```

### Fix 4: Lower Sample Threshold
```python
# In adaptive_signal_optimizer.py, LearningOrchestrator:
MIN_SAMPLES = 10  # Lower from 30 to allow faster learning
# Or use Bayesian prior for low-sample components
```

### Fix 5: Add Learning Health Check
```python
def check_learning_health():
    """Verify learning system is active and processing data"""
    optimizer = _get_adaptive_optimizer()
    if not optimizer:
        return {"status": "error", "message": "Optimizer not initialized"}
    
    report = optimizer.get_report()
    if report["learning_samples"] == 0:
        return {"status": "warning", "message": "No learning samples"}
    
    if not optimizer.has_learned_weights():
        return {"status": "warning", "message": "Weights not updated yet"}
    
    return {"status": "ok", "samples": report["learning_samples"]}
```

## Immediate Actions

1. **Run Verification Script**:
   ```bash
   python VERIFY_LEARNING_PIPELINE.py
   ```

2. **Check Log Files**:
   ```bash
   ls -lh logs/attribution.jsonl
   ls -lh data/uw_attribution.jsonl
   ls -lh state/signal_weights.json
   ```

3. **Check Learning Logs**:
   ```bash
   tail -20 data/weight_learning.jsonl
   tail -20 data/optimizer_errors.jsonl
   ```

4. **Verify Optimizer State**:
   ```python
   from adaptive_signal_optimizer import get_optimizer
   opt = get_optimizer()
   print(opt.get_report())
   ```

5. **Test Learning Flow**:
   - Manually trigger `learn_from_outcomes()`
   - Check if weights update
   - Verify weights are applied to scoring

## Monitoring Recommendations

Add to daily health checks:
- Learning samples count
- Last weight update timestamp
- Components with sufficient samples
- Weight update frequency
- Learning errors

Add alerts for:
- No learning samples in 7 days
- Weights not updated in 14 days
- Learning errors accumulating
- Components stuck at default multipliers
