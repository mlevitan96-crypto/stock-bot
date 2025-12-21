# Learning Pipeline Fixes & Verification Guide

## Executive Summary

The learning system is **initialized and available**, but **NOT processing trades** because:

1. **No trade logs exist** - Either no trades have closed, or logging isn't working
2. **Historical trades not processed** - `learn_from_outcomes()` only processes today's trades
3. **P&L format mismatch** - Learning receives dollars instead of percentages
4. **Learning only runs daily** - Trades closed during day aren't learned from until EOD
5. **High sample threshold** - Requires 30+ samples before adjusting weights

## Critical Issues Found

### Issue 1: P&L Format Mismatch (CRITICAL)

**Location**: `main.py` line 1973

**Problem**:
```python
reward = float(rec.get("pnl_usd", 0))  # This is in DOLLARS ($100, $1000, etc.)
record_trade_for_learning(comps, reward, regime, sector)
```

**Expected**: Learning system expects P&L as **percentage** (0.025 for 2.5%)

**Impact**: Learning system receives wrong scale, making all learning invalid

**Fix**:
```python
# Change line 1973 from:
record_trade_for_learning(comps, reward, regime, sector)

# To:
pnl_pct = float(rec.get("pnl_pct", 0)) / 100.0  # Convert % to decimal
record_trade_for_learning(comps, pnl_pct, regime, sector)
```

### Issue 2: Only Processes Today's Trades

**Location**: `main.py` line 1942

**Problem**:
```python
if not rec.get("ts", "").startswith(today):
    continue  # Skips ALL historical trades
```

**Impact**: Historical trades are never learned from. If bot restarts, all previous learning is lost.

**Fix**: Track last processed trade ID and process all unprocessed trades:
```python
def learn_from_outcomes(process_all=False):
    # ... existing code ...
    
    # Track last processed trade
    last_processed_file = Path("state/last_processed_trade.json")
    last_processed_id = None
    if last_processed_file.exists() and not process_all:
        last_processed_id = json.loads(last_processed_file.read_text()).get("trade_id")
    
    trades_processed = 0
    new_last_id = None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("type") != "attribution":
                continue
            
            trade_id = rec.get("trade_id", "")
            
            # Skip if already processed (unless process_all)
            if not process_all and last_processed_id and trade_id <= last_processed_id:
                continue
            
            # ... process trade ...
            trades_processed += 1
            new_last_id = trade_id
    
    # Save last processed ID
    if new_last_id:
        last_processed_file.write_text(json.dumps({"trade_id": new_last_id}))
```

### Issue 3: Learning Only Runs Daily

**Location**: `main.py` line 5357

**Problem**: `learn_from_outcomes()` only called after market close

**Impact**: Trades closed during day aren't learned from until EOD

**Fix**: Call after each trade close:
```python
def log_exit_attribution(...):
    # ... existing logging code ...
    
    # Immediately feed to learning (don't wait for EOD)
    try:
        pnl_pct = context.get("pnl_pct", 0) / 100.0
        components = context.get("components", {})
        regime = context.get("market_regime", "unknown")
        
        # Record trade for learning
        record_trade_for_learning(components, pnl_pct, regime, "unknown")
        
        # Trigger weight update if enough samples accumulated
        optimizer = _get_adaptive_optimizer()
        if optimizer:
            history_size = len(optimizer.learner.learning_history)
            if history_size >= 30:  # Enough samples for update
                optimizer.update_weights()
                log_event("learning", "weights_updated_immediate", 
                         samples=history_size)
    except Exception as e:
        log_event("learning", "immediate_learning_failed", error=str(e))
```

### Issue 4: High Sample Threshold

**Location**: `adaptive_signal_optimizer.py` line 450

**Problem**: `MIN_SAMPLES = 30` means components need 30+ trades before adjusting

**Impact**: Low-frequency signals (congress, shorts_squeeze) may never learn

**Fix**: Use Bayesian prior for low-sample components:
```python
# In LearningOrchestrator.update_weights():
if total < self.MIN_SAMPLES:
    # Use Bayesian prior for low-sample components
    # Start with weak prior, strengthen as samples accumulate
    prior_strength = total / self.MIN_SAMPLES  # 0.0 to 1.0
    if prior_strength > 0.1:  # At least 10% of required samples
        # Apply small adjustment based on current performance
        current_mult = self.entry_model.weight_bands[component].current
        if wins > losses and total >= 5:
            new_mult = min(2.5, current_mult + self.UPDATE_STEP * prior_strength)
        elif losses > wins and total >= 5:
            new_mult = max(0.25, current_mult - self.UPDATE_STEP * prior_strength)
        else:
            new_mult = current_mult
        
        if new_mult != current_mult:
            self.entry_model.update_multiplier(component, new_mult)
            # ... log adjustment ...
```

### Issue 5: No Verification

**Problem**: No health checks to verify learning is working

**Fix**: Add to daily health checks:
```python
def check_learning_health():
    """Verify learning system is active and processing data"""
    optimizer = _get_adaptive_optimizer()
    if not optimizer:
        return {"status": "error", "message": "Optimizer not initialized"}
    
    report = optimizer.get_report()
    issues = []
    
    if report["learning_samples"] == 0:
        issues.append("No learning samples - trades not being recorded")
    
    if not optimizer.has_learned_weights():
        issues.append("Weights not updated - may need more samples")
    
    # Check component health
    component_report = report.get("component_performance", {})
    components_with_samples = sum(1 for c in component_report.values() 
                                   if c.get("samples", 0) > 0)
    
    if components_with_samples == 0:
        issues.append("No components have samples")
    elif components_with_samples < 5:
        issues.append(f"Only {components_with_samples} components have samples")
    
    return {
        "status": "ok" if not issues else "warning",
        "samples": report["learning_samples"],
        "components_with_samples": components_with_samples,
        "has_learned_weights": optimizer.has_learned_weights(),
        "issues": issues
    }
```

## Implementation Steps

### Step 1: Fix P&L Format (IMMEDIATE)
1. Edit `main.py` line 1973
2. Change to use `pnl_pct` instead of `pnl_usd`
3. Test with a single trade

### Step 2: Process Historical Trades
1. Add last processed trade tracking
2. Modify `learn_from_outcomes()` to process all unprocessed trades
3. Run once to backfill historical data

### Step 3: Continuous Learning
1. Add learning call to `log_exit_attribution()`
2. Trigger weight updates when enough samples accumulate
3. Monitor learning activity

### Step 4: Lower Thresholds
1. Reduce `MIN_SAMPLES` or add Bayesian prior
2. Allow faster learning for high-frequency components
3. Keep conservative approach for low-frequency components

### Step 5: Add Monitoring
1. Add learning health check to daily monitoring
2. Alert if learning not active
3. Track learning metrics in dashboard

## Verification Commands

### Check if Learning is Active
```python
from adaptive_signal_optimizer import get_optimizer
opt = get_optimizer()
report = opt.get_report()
print(f"Samples: {report['learning_samples']}")
print(f"Has learned: {opt.has_learned_weights()}")
print(f"Components: {len(report['component_performance'])}")
```

### Check Log Files
```bash
# Count attribution logs
wc -l logs/attribution.jsonl

# Check recent trades
tail -20 logs/attribution.jsonl | jq '.context.components'

# Check learning state
cat state/signal_weights.json | jq '.learner.learning_history_count'
```

### Manually Trigger Learning
```python
# Process all historical trades
from main import learn_from_outcomes
learn_from_outcomes(process_all=True)

# Check if weights updated
from adaptive_signal_optimizer import get_optimizer
opt = get_optimizer()
print(opt.get_report())
```

### Monitor Learning Activity
```python
# Watch learning log
tail -f data/weight_learning.jsonl

# Check for errors
tail -f data/optimizer_errors.jsonl
```

## Expected Behavior After Fixes

1. **Immediate**: Each closed trade feeds to learning system
2. **After 5 trades**: Weight update triggered (if >=5 trades today)
3. **After 30 samples**: Components start adjusting multipliers
4. **Weekly**: Full weight optimization cycle
5. **Continuous**: Weights applied to all scoring decisions

## Success Metrics

- ✅ Attribution logs contain trades with components
- ✅ Learning history grows with each trade
- ✅ Component sample counts increase
- ✅ Multipliers change from default (1.0)
- ✅ Weight updates logged in `data/weight_learning.jsonl`
- ✅ Composite scoring uses adaptive weights
- ✅ No errors in `data/optimizer_errors.jsonl`

## Next Steps

1. **Run verification script**: `python VERIFY_LEARNING_PIPELINE.py`
2. **Review findings**: Check `learning_pipeline_report.json`
3. **Apply fixes**: Start with P&L format fix (Issue 1)
4. **Test**: Close a trade and verify it's learned from
5. **Monitor**: Watch learning metrics daily
6. **Iterate**: Adjust thresholds based on results
