# Pre-Market-Close Structural Health Check

## Purpose

This health check script verifies key system metrics before market close to ensure:
1. Panic regime activity is tracked
2. Current regime and thresholds are correct
3. Position capacity is available for MOC (Market-On-Close) moves

## Usage

### On Droplet (Recommended)

```bash
cd ~/stock-bot
bash pre_market_close_health_check.sh
```

### Manual Commands

If you prefer to run commands individually:

```bash
cd ~/stock-bot

# 1. Check if any 'Panic Boosts' were applied today
grep -i "panic" data/explainable_logs.jsonl | tail -n 5
# OR if file is in logs/ directory:
grep -i "panic" logs/explainable_logs.jsonl | tail -n 5

# 2. Verify current regime and threshold
python3 -c "
from structural_intelligence import get_regime_detector
from specialist_strategy_rotator import SpecialistStrategyRotator

regime_detector = get_regime_detector()
current_regime, confidence = regime_detector.detect_regime()
ssr = SpecialistStrategyRotator(current_regime, 2.0)
threshold = ssr.get_proactive_threshold()

print(f'Current Regime: {current_regime} (confidence: {confidence:.2f})')
print(f'Active Threshold: {threshold:.2f}')
"

# 3. Check Capacity
python3 -c "
import json
from pathlib import Path

meta = json.load(open('state/position_metadata.json'))
active_positions = len(meta)
max_positions = 16
free_capacity = max_positions - active_positions

print(f'Active Positions: {active_positions} / {max_positions}')
print(f'Free Capacity: {free_capacity}')
"
```

## What Each Check Does

### 1. Panic Regime Activity

**Purpose**: Verify if panic regime was detected today and if buy-the-dip strategy was applied.

**Location**: `data/explainable_logs.jsonl` or `logs/explainable_logs.jsonl`

**What to Look For**:
- Entries containing "panic" (case-insensitive)
- Should show if panic regime was detected
- Confirms the panic fix (1.2x multiplier) is working

**Expected Output**:
```
Found 3 panic-related entries
Recent entries:
- {"ts": "...", "type": "regime", "regime": "PANIC", ...}
```

### 2. Current Regime and Threshold

**Purpose**: Verify the current market regime and active entry threshold.

**Components**:
- **Regime Detection**: Uses structural intelligence HMM-based regime detector
- **Threshold**: Uses SpecialistStrategyRotator to get proactive threshold (may be adjusted for mid-day liquidity gaps)

**What to Look For**:
- Regime should be one of: RISK_ON, NEUTRAL, RISK_OFF, PANIC
- Threshold typically 2.0 (base) or 2.75 (during mid-day 11:30-13:30 EST)

**Expected Output**:
```
Detected Regime: PANIC (confidence: 0.75)
Active Threshold: 2.00
```

### 3. Position Capacity

**Purpose**: Check how many position slots are available for new entries (especially MOC moves).

**Location**: `state/position_metadata.json`

**What to Look For**:
- Active positions count (should be < 16)
- Free capacity (16 - active positions)
- If capacity is low (< 3 slots), consider exiting weak positions

**Expected Output**:
```
Active Positions: 8 / 16
Free Capacity: 8
Status: OK - 8 slot(s) available for new entries
```

## Interpreting Results

### Healthy State

- **Panic Activity**: Either no panic (normal) or panic detected with entries logged
- **Regime**: Valid regime detected with reasonable confidence (>0.5)
- **Threshold**: 2.0-2.75 (normal range)
- **Capacity**: 4+ free slots available

### Warning Signs

- **Panic Activity**: Many panic entries but no positions entered (may indicate threshold too high)
- **Regime**: Low confidence (<0.5) or "UNKNOWN"
- **Threshold**: Unexpectedly high (>3.0) outside mid-day window
- **Capacity**: < 3 free slots (may need to exit weak positions)

### Actions to Take

1. **If Panic Detected but No Entries**:
   - Check if signals were generated but blocked by gates
   - Review logs for blocked trades
   - Verify panic multiplier (1.2x) is being applied

2. **If Capacity Full**:
   - Review positions and consider exiting weakest performers
   - Check if displacement logic should trigger
   - Review exit signals for positions

3. **If Threshold Too High**:
   - Verify mid-day window (11:30-13:30 EST) if threshold is 2.75
   - Check if system stage changed unexpectedly
   - Review threshold configuration

## Integration with Monitoring

This health check complements:
- Dashboard monitoring (`/api/positions`, `/api/health`)
- Daily learning cycle
- Position reconciliation loop
- Regime detection updates

## Frequency

**Recommended**: Run before market close (3:30-4:00 PM EST) to:
- Verify capacity for MOC moves
- Check if panic regime affected trading today
- Ensure thresholds are correct for next trading day

## Troubleshooting

### Script Fails to Run

1. **Check file permissions**:
   ```bash
   chmod +x pre_market_close_health_check.sh
   ```

2. **Verify Python path**:
   ```bash
   which python3
   ```

3. **Check if files exist**:
   ```bash
   ls -la data/explainable_logs.jsonl
   ls -la state/position_metadata.json
   ls -la state/signal_weights.json
   ```

### Import Errors

If imports fail:
```bash
# Activate virtual environment if using one
source venv/bin/activate

# Or install dependencies
pip install -r requirements.txt
```

### File Not Found

- `explainable_logs.jsonl` might be in `logs/` instead of `data/`
- `position_metadata.json` is created when first position is opened
- Script handles missing files gracefully
