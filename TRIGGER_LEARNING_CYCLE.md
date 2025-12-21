# Trigger Learning Cycle Now

## Quick Start

Run this command on the droplet to process ALL historical data through the learning system immediately:

```bash
cd ~/stock-bot
git pull origin main
python3 trigger_learning_cycle_now.py
```

## What It Does

This script processes **ALL historical data** through the learning system, including:

1. **Actual Trades** (`logs/attribution.jsonl`)
   - All completed trades
   - P&L outcomes
   - Component attribution

2. **Exit Events** (`logs/exit.jsonl`)
   - Exit reasons
   - Exit timing
   - Exit signal learning

3. **Blocked Trades** (`state/blocked_trades.jsonl`)
   - Counterfactual learning
   - Missed opportunities

4. **Gate Events** (`logs/gate.jsonl`) ← **NEW**
   - Gate pattern learning
   - Gate effectiveness analysis
   - Optimal threshold learning

5. **UW Blocked Entries** (`data/uw_attribution.jsonl`) ← **NEW**
   - Blocked UW entries (decision="rejected")
   - Signal combination analysis
   - Sentiment pattern tracking

6. **Signal Patterns** (`logs/signals.jsonl`) ← **NEW**
   - All signal generation events
   - Signal-to-trade correlation
   - Best component combinations

7. **Order Execution** (`logs/orders.jsonl`)
   - Execution quality tracking

## Expected Output

```
================================================================================
TRIGGER LEARNING CYCLE NOW
================================================================================

Started at: 2025-12-21 17:30:00 UTC

================================================================================
DATA FILES CHECK
================================================================================

✓ attribution        : logs/attribution.jsonl (207 records)
✓ exits              : logs/exit.jsonl (97 records)
✓ signals            : logs/signals.jsonl (2,000 records)
✓ orders             : logs/orders.jsonl (4,627 records)
✓ blocked_trades     : state/blocked_trades.jsonl (3,619 records)
✓ gate               : logs/gate.jsonl (12,195 records)
✓ uw_attribution     : data/uw_attribution.jsonl (2,000 records)

Total records available: 24,745

================================================================================
RUNNING LEARNING CYCLE
================================================================================

Processing ALL historical data through learning system...
[Progress...]

================================================================================
LEARNING CYCLE COMPLETE
================================================================================

Processing Results:
  Trades processed:        207
  Exits processed:         97
  Signals processed:       2,000
  Orders processed:        4,627
  Blocked trades:          3,619
  Gate events:             12,195
  UW blocked entries:      1,124
  Weights updated:         0

Processing time: 45.2 seconds

================================================================================
LEARNING ENHANCEMENTS STATUS
================================================================================

✓ Gate Pattern Learning: 15 gates tracked, 12,195 blocks analyzed
✓ UW Blocked Learning: 876 symbols tracked, 1,124 blocked entries analyzed
✓ Signal Pattern Learning: 200 symbols tracked, 2,000 signals, 75 trades correlated
```

## After Running

### Check Enhancement Status
```bash
python3 check_learning_enhancements.py
```

### Check Comprehensive Learning Status
```bash
python3 check_comprehensive_learning_status.py
```

### View State Files
```bash
# Gate patterns
cat state/gate_pattern_learning.json | python3 -m json.tool | head -50

# UW blocked patterns
cat state/uw_blocked_learning.json | python3 -m json.tool | head -50

# Signal patterns
cat state/signal_pattern_learning.json | python3 -m json.tool | head -50
```

## Notes

- **First Run**: Processes ALL historical data (may take a few minutes)
- **Subsequent Runs**: Only processes new data since last run
- **Weight Updates**: Only updates if enough new samples (MIN_SAMPLES guard)
- **State Files**: Created automatically in `state/` directory
- **No Impact on Trading**: This is read-only processing, doesn't affect live trading

## Troubleshooting

### No Data Files Found
If you see "No data files found":
- Check that log files exist: `ls -lh logs/*.jsonl`
- Check that data files exist: `ls -lh data/*.jsonl`
- Verify bot has been running and generating logs

### Processing Takes Too Long
- Normal for first run with lots of historical data
- Subsequent runs are much faster (only new data)
- Can interrupt with Ctrl+C (safe, won't corrupt state)

### Enhancement State Not Created
- Enhancement state files are only created if there's data to process
- If gate.jsonl is empty, gate_pattern_learning.json won't be created
- This is expected behavior

## Summary

This script gives you **immediate learning** from all historical data instead of waiting for the daily cycle. Perfect for:
- Initial setup
- After adding new learning enhancements
- When you want to reprocess all data
- Testing the learning system
