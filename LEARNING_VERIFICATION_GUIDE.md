# Learning Pipeline Verification & Fix Guide

## Quick Status Check

Run this command to verify learning pipeline health:
```bash
python VERIFY_LEARNING_PIPELINE.py
```

## Critical Bug Fixed

**Issue**: Learning system was receiving P&L in dollars instead of percentage  
**Location**: `main.py` line 1973  
**Status**: ✅ FIXED

The learning system expects P&L as a decimal percentage (0.025 for 2.5%), but was receiving dollars ($100, $1000). This would cause all learning to be invalid.

## How to Verify Learning is Working

### 1. Check Log Files Exist
```bash
# Attribution logs (closed trades)
ls -lh logs/attribution.jsonl

# UW attribution logs (signal evaluations)
ls -lh data/uw_attribution.jsonl
```

### 2. Check Learning State
```bash
# Learning weights state
cat state/signal_weights.json | jq '.learner.learning_history_count'

# Learning updates log
tail -20 data/weight_learning.jsonl
```

### 3. Verify Components Have Samples
```python
from adaptive_signal_optimizer import get_optimizer
opt = get_optimizer()
report = opt.get_report()

# Check component performance
for comp, perf in report['component_performance'].items():
    samples = perf.get('samples', 0)
    if samples > 0:
        print(f"{comp}: {samples} samples, multiplier={perf.get('multiplier', 1.0):.2f}")
```

### 4. Check if Weights Are Applied
```python
from uw_composite_v2 import get_adaptive_weights
weights = get_adaptive_weights()
if weights:
    print("✅ Adaptive weights are being used")
    # Check if any multipliers are non-default
    from adaptive_signal_optimizer import get_optimizer
    opt = get_optimizer()
    mults = opt.get_multipliers_only()
    non_default = {k: v for k, v in mults.items() if v != 1.0}
    if non_default:
        print(f"✅ {len(non_default)} components have learned multipliers")
    else:
        print("⚠️ All multipliers at default (1.0) - learning hasn't adjusted yet")
else:
    print("❌ Adaptive weights not available")
```

## Data Flow Verification

### Step 1: Trade Closes
- `log_exit_attribution()` is called
- Logs to `logs/attribution.jsonl` with:
  - `pnl_usd`: Dollar P&L
  - `pnl_pct`: Percentage P&L
  - `components`: Signal values at entry

### Step 2: Learning Processes Trade
- `learn_from_outcomes()` reads attribution log
- Extracts `pnl_pct` and converts to decimal
- Calls `record_trade_for_learning(components, pnl_pct, regime, sector)`

### Step 3: Learning System Records
- `LearningOrchestrator.record_trade_outcome()` receives data
- Updates component performance:
  - Wins/losses per component
  - EWMA win rate
  - EWMA P&L
  - Sector/regime performance

### Step 4: Weight Updates
- After 30+ samples, `update_weights()` is called
- Adjusts multipliers based on performance
- Saves to `state/signal_weights.json`

### Step 5: Weights Applied
- `uw_composite_v2` calls `get_adaptive_weights()`
- Merges base weights with learned multipliers
- Uses in composite scoring

## Common Issues & Solutions

### Issue: No Attribution Logs
**Symptom**: `logs/attribution.jsonl` doesn't exist or is empty  
**Cause**: No trades have closed, or `log_exit_attribution()` not being called  
**Fix**: Check if trades are closing, verify exit evaluation is running

### Issue: Components Missing
**Symptom**: Trades logged but `components` field is empty  
**Cause**: Components not stored in position metadata  
**Fix**: Verify `components` are saved when position opens (line 3412)

### Issue: Learning Not Processing
**Symptom**: Logs exist but learning history is empty  
**Cause**: `learn_from_outcomes()` not being called, or only processing today's trades  
**Fix**: 
1. Verify `learn_from_outcomes()` is called daily (line 5357)
2. Check if `ENABLE_PER_TICKER_LEARNING=true`
3. Process historical trades manually

### Issue: Weights Not Updating
**Symptom**: Components have samples but multipliers stay at 1.0  
**Cause**: Not enough samples (needs 30+), or update logic not running  
**Fix**:
1. Check sample counts: need 30+ per component
2. Verify `update_weights()` is called (line 1983)
3. Check for errors in `data/optimizer_errors.jsonl`

### Issue: Weights Not Applied
**Symptom**: Multipliers updated but composite scoring uses static weights  
**Cause**: `uw_composite_v2` not calling `get_adaptive_weights()`  
**Fix**: Verify `uw_composite_v2.py` uses adaptive weights (line 44-49)

## Monitoring Recommendations

Add to daily monitoring:
1. Learning samples count
2. Last weight update timestamp
3. Components with sufficient samples (30+)
4. Non-default multipliers count
5. Learning errors

Set alerts for:
- No learning samples in 7 days
- Weights not updated in 14 days
- Learning errors accumulating
- All multipliers at default after 50+ trades

## Testing the Fix

After applying the P&L format fix:

1. **Close a test trade** (or wait for next close)
2. **Check attribution log**:
   ```bash
   tail -1 logs/attribution.jsonl | jq '.pnl_pct'
   ```
3. **Verify learning received it**:
   ```python
   from adaptive_signal_optimizer import get_optimizer
   opt = get_optimizer()
   print(f"Learning history: {len(opt.learner.learning_history)}")
   ```
4. **Check if sample counts increased**:
   ```python
   report = opt.get_report()
   for comp, perf in report['component_performance'].items():
       if perf.get('samples', 0) > 0:
           print(f"{comp}: {perf['samples']} samples")
   ```

## Expected Timeline

- **Immediate**: Each closed trade feeds to learning
- **After 5 trades**: Weight update triggered (if >=5 today)
- **After 30 samples**: Components start adjusting multipliers
- **Weekly**: Full weight optimization cycle
- **Continuous**: Weights applied to all scoring decisions

## Files Reference

- **VERIFY_LEARNING_PIPELINE.py**: Diagnostic script
- **LEARNING_PIPELINE_ANALYSIS.md**: Detailed issue analysis
- **LEARNING_PIPELINE_FIXES.md**: Code fixes with examples
- **LEARNING_PIPELINE_SUMMARY.md**: Executive summary
- **LEARNING_VERIFICATION_GUIDE.md**: This guide
