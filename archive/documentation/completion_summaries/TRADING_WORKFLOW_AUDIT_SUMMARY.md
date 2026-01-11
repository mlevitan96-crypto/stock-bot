# Trading Workflow Audit Summary

## Purpose
Comprehensive audit to verify:
1. Bot is seeing current open trades from Alpaca
2. Position reconciliation is working correctly
3. Complete trading workflow is functioning (signal → entry → exit)
4. Exit evaluation is running and processing positions

## Audit Script Created
**File:** `FULL_TRADING_WORKFLOW_AUDIT.py`

### What It Checks

#### 1. Alpaca Connection & Positions
- Connects to Alpaca API
- Fetches current positions from broker
- Displays position details (symbol, qty, entry price, current price, P&L)

#### 2. Executor State (`executor.opens`)
- Checks `state/executor_state.json` for in-memory position tracking
- Compares with Alpaca positions
- Identifies missing or orphaned positions

#### 3. Position Metadata
- Checks `state/position_metadata.json`
- Verifies entry_score, components, entry_ts are preserved
- Ensures metadata exists for all Alpaca positions

#### 4. Position Reconciliation
- Compares Alpaca positions vs executor.opens vs metadata
- Checks for:
  - Positions in Alpaca but not in executor (missing tracking)
  - Positions in executor but not in Alpaca (orphaned)
  - Quantity mismatches
  - Entry price mismatches
  - Missing entry_score

#### 5. Main Loop Activity
- Checks `logs/run.jsonl` for recent cycles
- Verifies bot is running (cycles in last hour/day)
- Determines if main loop is active (last cycle < 5 minutes ago)

#### 6. Exit Evaluation Activity
- Checks `logs/exits.jsonl` for recent exit events
- Verifies exit evaluation is running
- Shows last exit event timestamp

#### 7. Entry/Execution Activity
- Checks `logs/attribution.jsonl` for recent entries
- Verifies entry execution is working
- Shows last entry event details

#### 8. Reconciliation Logs
- Checks `data/audit_positions_autofix.jsonl`
- Reviews recent reconciliation events
- Identifies any position sync issues

## How Position Tracking Works

### Flow Overview
1. **Entry**: `decide_and_execute()` → `executor.submit_entry()` → `executor.mark_open()`
   - Position added to `executor.opens[symbol]`
   - Metadata written to `state/position_metadata.json`
   - Entry logged to `logs/attribution.jsonl`

2. **Reconciliation**: `executor.reconcile_positions()` (on startup) or `reload_positions_from_metadata()` (periodic)
   - Fetches positions from Alpaca API
   - Syncs `executor.opens` with Alpaca positions
   - Updates metadata from Alpaca if missing

3. **Exit Evaluation**: `executor.evaluate_exits()` (every cycle)
   - Iterates through `executor.opens`
   - Evaluates exit signals (trailing stop, time exit, signal decay, etc.)
   - Closes positions when triggers hit
   - Removes from `executor.opens` after close

### Key Files
- `executor.opens`: In-memory dict tracking open positions (key: symbol, value: position info)
- `state/position_metadata.json`: Persistent metadata (entry_score, components, entry_ts, etc.)
- `state/executor_state.json`: Snapshot of executor.opens (for debugging)
- `logs/exits.jsonl`: Exit events log
- `logs/attribution.jsonl`: Entry/exit attribution log
- `logs/run.jsonl`: Main loop cycle log

## Running the Audit

### On Droplet (Recommended)
The bot runs on the droplet, so audit should run there for accurate results:

```bash
# SSH to droplet
ssh alpaca

# Navigate to bot directory
cd ~/stock-bot

# Run audit
python3 FULL_TRADING_WORKFLOW_AUDIT.py
```

### Locally (Limited)
Can run locally but will only check local files (may be outdated):

```bash
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python FULL_TRADING_WORKFLOW_AUDIT.py
```

## Expected Results

### Healthy System
- ✅ All Alpaca positions are in executor.opens
- ✅ No orphaned positions in executor.opens
- ✅ All positions have metadata with entry_score > 0
- ✅ Main loop is active (cycles in last hour)
- ✅ Exit evaluation running (exits in last hour)
- ✅ Entry execution working (entries in logs)

### Issues to Watch For
- ❌ Positions in Alpaca but NOT in executor.opens → Reconciliation not working
- ❌ Positions in executor.opens but NOT in Alpaca → Orphaned tracking
- ❌ Missing entry_score (0.0) → Metadata not preserved
- ❌ No cycles in last hour → Main loop not running
- ❌ No exits in last hour → Exit evaluation not running
- ❌ Quantity/price mismatches → Sync issues

## Next Steps

1. **Deploy audit script to droplet** (if not already there)
2. **Run audit on droplet** to get current state
3. **Review results** and identify any issues
4. **Fix any reconciliation or tracking issues** found
5. **Re-run audit** to verify fixes

## Related Documentation
- `MEMORY_BANK.md`: Complete system documentation
- `ALPACA_TRADING_BOT_WORKFLOW.md`: Detailed workflow documentation
- `position_reconciliation_loop.py`: Reconciliation implementation
- `main.py`: Main trading loop and executor implementation
