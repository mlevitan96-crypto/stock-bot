# Learning Pipeline - Next Steps

## ✅ What's Already Done

1. **Critical Bug Fixed**: P&L format mismatch fixed in `main.py` line 1972-1973
2. **Verification Script Created**: `VERIFY_LEARNING_PIPELINE.py`
3. **Analysis Documents Created**: Full analysis of issues and fixes

## Where to Run Scripts

**IMPORTANT**: All scripts must be run from the **project root directory** (where `main.py` is located).

**Project Root**: `c:\Users\markl\OneDrive\Documents\Cursor\stock-bot\`

---

## Step 1: Verify the Fix is Applied ✅

The critical P&L format bug has been fixed. Verify it's in your code:

**Check**: Open `main.py` and verify line 1972-1973 shows:
```python
pnl_pct = float(rec.get("pnl_pct", 0)) / 100.0  # Convert % to decimal (0.025 for 2.5%)
record_trade_for_learning(comps, pnl_pct, regime, sector)
```

If it still shows `reward` instead of `pnl_pct`, the fix needs to be applied.

---

## Step 2: Run Verification Script (Copy-Paste Ready)

**Windows PowerShell** (run from project root):

```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python VERIFY_LEARNING_PIPELINE.py
```

**Windows Command Prompt**:

```cmd
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python VERIFY_LEARNING_PIPELINE.py
```

**What it shows**:
- Whether logs exist
- If learning system is initialized
- Component sample counts
- Whether weights have been updated
- Any errors

**Output saved to**: `learning_pipeline_report.json`

---

## Step 3: Check Learning System Status (Copy-Paste Ready)

**Create and run this Python script** (`check_learning_status.py`):

```python
#!/usr/bin/env python3
"""Quick learning status check - copy/paste ready"""
import json
from pathlib import Path

print("=" * 60)
print("LEARNING SYSTEM STATUS CHECK")
print("=" * 60)
print()

# Check if optimizer is available
try:
    from adaptive_signal_optimizer import get_optimizer
    opt = get_optimizer()
    if opt:
        print("[OK] Adaptive optimizer initialized")
        
        report = opt.get_report()
        print(f"Learning samples: {report['learning_samples']}")
        print(f"Has learned weights: {opt.has_learned_weights()}")
        
        # Check component performance
        comp_perf = report.get('component_performance', {})
        components_with_samples = sum(1 for c in comp_perf.values() if c.get('samples', 0) > 0)
        print(f"Components with samples: {components_with_samples}")
        
        # Show top components
        if components_with_samples > 0:
            print("\nTop components by samples:")
            sorted_comps = sorted(comp_perf.items(), key=lambda x: x[1].get('samples', 0), reverse=True)
            for comp, perf in sorted_comps[:5]:
                samples = perf.get('samples', 0)
                if samples > 0:
                    mult = perf.get('multiplier', 1.0)
                    print(f"  {comp}: {samples} samples, multiplier={mult:.2f}")
    else:
        print("[ERROR] Optimizer not initialized")
except ImportError as e:
    print(f"[ERROR] Cannot import optimizer: {e}")
except Exception as e:
    print(f"[ERROR] Error checking optimizer: {e}")

print()

# Check logs
print("=" * 60)
print("LOG FILES CHECK")
print("=" * 60)
print()

attr_log = Path("logs/attribution.jsonl")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Attribution log exists: {len(lines)} trades")
        if lines:
            try:
                last = json.loads(lines[-1])
                print(f"  Last trade: {last.get('symbol')} P&L: {last.get('pnl_pct', 0)}%")
            except:
                pass
else:
    print("[WARNING] No attribution log found (logs/attribution.jsonl)")

uw_attr_log = Path("data/uw_attribution.jsonl")
if uw_attr_log.exists():
    with open(uw_attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] UW attribution log exists: {len(lines)} records")
else:
    print("[INFO] No UW attribution log (data/uw_attribution.jsonl)")

print()

# Check learning state
print("=" * 60)
print("LEARNING STATE CHECK")
print("=" * 60)
print()

weights_file = Path("state/signal_weights.json")
if weights_file.exists():
    with open(weights_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        learner = state.get("learner", {})
        history_count = learner.get("learning_history_count", 0)
        print(f"[OK] Learning state file exists")
        print(f"  Learning history: {history_count} trades")
        
        # Check component samples
        entry_weights = state.get("entry_weights", {})
        bands = entry_weights.get("weight_bands", {})
        components_with_data = sum(1 for b in bands.values() if isinstance(b, dict) and b.get("sample_count", 0) > 0)
        print(f"  Components with data: {components_with_data}")
        
        if components_with_data > 0:
            print("\n  Components with samples:")
            for comp, band in bands.items():
                if isinstance(band, dict):
                    samples = band.get("sample_count", 0)
                    if samples > 0:
                        mult = band.get("current", 1.0)
                        wins = band.get("wins", 0)
                        losses = band.get("losses", 0)
                        print(f"    {comp}: {samples} samples ({wins}W/{losses}L), mult={mult:.2f}")
else:
    print("[WARNING] No learning state file (state/signal_weights.json)")
    print("  Learning system hasn't processed any trades yet")

print()

# Check learning log
learning_log = Path("data/weight_learning.jsonl")
if learning_log.exists():
    with open(learning_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Learning updates log: {len(lines)} updates")
        if lines:
            try:
                last_update = json.loads(lines[-1])
                adjustments = last_update.get("adjustments", [])
                print(f"  Last update: {len(adjustments)} components adjusted")
            except:
                pass
else:
    print("[INFO] No learning updates log yet (data/weight_learning.jsonl)")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
```

**Run it**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_learning_status.py
```

---

## Step 4: Check if Trades Are Closing

The verification showed **no logs found**, which means either:
1. No trades have closed yet, OR
2. Logging isn't working

**Quick Check Script** (`check_trades_closing.py`):

```python
#!/usr/bin/env python3
"""Check if trades are closing and being logged"""
import json
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("TRADE CLOSING CHECK")
print("=" * 60)
print()

# Check exit logs
exit_log = Path("logs/exit.jsonl")
if exit_log.exists():
    with open(exit_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Exit log exists: {len(lines)} exit events")
        if lines:
            # Show last 5 exits
            print("\nLast 5 exits:")
            for line in lines[-5:]:
                try:
                    rec = json.loads(line)
                    symbol = rec.get('symbol', 'UNKNOWN')
                    reason = rec.get('reason', 'unknown')
                    ts = rec.get('ts', '')
                    print(f"  {symbol}: {reason} ({ts})")
                except:
                    pass
else:
    print("[WARNING] No exit log found (logs/exit.jsonl)")

print()

# Check attribution logs
attr_log = Path("logs/attribution.jsonl")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Attribution log exists: {len(lines)} closed trades")
        if lines:
            # Show last 5 trades
            print("\nLast 5 closed trades:")
            for line in lines[-5:]:
                try:
                    rec = json.loads(line)
                    if rec.get('type') == 'attribution':
                        symbol = rec.get('symbol', 'UNKNOWN')
                        pnl_pct = rec.get('pnl_pct', 0)
                        pnl_usd = rec.get('pnl_usd', 0)
                        ts = rec.get('ts', '')
                        print(f"  {symbol}: P&L={pnl_pct:.2f}% (${pnl_usd:.2f}) - {ts}")
                except:
                    pass
else:
    print("[WARNING] No attribution log found (logs/attribution.jsonl)")
    print("  This means either:")
    print("    1. No trades have closed yet")
    print("    2. log_exit_attribution() is not being called")

print()
```

**Run it**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_trades_closing.py
```

---

## Step 5: Manual Learning Check (Copy-Paste Ready)

**If you want to manually check learning** (`manual_learning_check.py`):

```python
#!/usr/bin/env python3
"""Manual learning system check"""
from adaptive_signal_optimizer import get_optimizer

opt = get_optimizer()
if not opt:
    print("ERROR: Optimizer not available")
    exit(1)

print("Learning System Report:")
print("=" * 60)
report = opt.get_report()

print(f"Total learning samples: {report['learning_samples']}")
print(f"Has learned weights: {opt.has_learned_weights()}")
print()

print("Component Performance:")
print("-" * 60)
comp_perf = report.get('component_performance', {})
for comp, perf in sorted(comp_perf.items()):
    samples = perf.get('samples', 0)
    if samples > 0:
        mult = perf.get('multiplier', 1.0)
        wins = perf.get('wins', 0)
        losses = perf.get('losses', 0)
        wr = wins / (wins + losses) if (wins + losses) > 0 else 0
        print(f"{comp:25s} samples={samples:3d} wins={wins:2d} losses={losses:2d} wr={wr:.2f} mult={mult:.2f}")

print()
print("Multipliers (non-default):")
print("-" * 60)
mults = opt.get_multipliers_only()
non_default = {k: v for k, v in mults.items() if v != 1.0}
if non_default:
    for comp, mult in sorted(non_default.items(), key=lambda x: abs(x[1] - 1.0), reverse=True):
        print(f"{comp:25s} multiplier={mult:.2f}")
else:
    print("All multipliers at default (1.0) - learning hasn't adjusted yet")
```

**Run it**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python manual_learning_check.py
```

---

## Step 6: Process Historical Trades (If Needed)

**If you have historical trades that haven't been learned from**, create this script (`process_historical_trades.py`):

```python
#!/usr/bin/env python3
"""Process all historical trades for learning"""
import json
from pathlib import Path
from main import learn_from_outcomes

# This will process all trades in attribution.jsonl
# Note: learn_from_outcomes() currently only processes today's trades
# This is a workaround to process all trades

attr_log = Path("logs/attribution.jsonl")
if not attr_log.exists():
    print("No attribution log found")
    exit(1)

print("Processing historical trades...")
print("=" * 60)

# Load all trades
all_trades = []
with open(attr_log, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get('type') == 'attribution':
                all_trades.append(rec)
        except:
            continue

print(f"Found {len(all_trades)} historical trades")

# Manually feed each trade to learning system
from adaptive_signal_optimizer import get_optimizer
opt = get_optimizer()

if not opt:
    print("ERROR: Optimizer not available")
    exit(1)

processed = 0
for rec in all_trades:
    try:
        ctx = rec.get('context', {})
        comps = ctx.get('components', {})
        pnl_pct = float(rec.get('pnl_pct', 0)) / 100.0
        regime = ctx.get('market_regime', 'unknown')
        sector = 'unknown'
        
        if comps and pnl_pct != 0:
            opt.record_trade(comps, pnl_pct, regime, sector)
            processed += 1
    except Exception as e:
        print(f"Error processing trade: {e}")
        continue

print(f"Processed {processed} trades for learning")

# Trigger weight update if enough samples
if processed >= 5:
    print("\nTriggering weight update...")
    result = opt.update_weights()
    print(f"Weight update result: {result.get('total_adjusted', 0)} components adjusted")
    opt.save_state()
    print("Learning state saved")
else:
    print(f"\nOnly {processed} trades processed (need 5+ for weight update)")

print("\nDone!")
```

**Run it**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python process_historical_trades.py
```

---

## Daily Monitoring Commands (Copy-Paste Ready)

### Quick Status Check
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python VERIFY_LEARNING_PIPELINE.py
```

### Check Recent Trades
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_trades_closing.py
```

### Check Learning State
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_learning_status.py
```

### Full Learning Report
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python manual_learning_check.py
```

---

## Success Criteria

You'll know learning is working when:

1. ✅ **Logs Exist**: `logs/attribution.jsonl` has trade records
2. ✅ **Samples Growing**: Component sample counts increase after each trade
3. ✅ **Weights Updating**: Multipliers change from 1.0 after 30+ samples
4. ✅ **Updates Logged**: `data/weight_learning.jsonl` shows weight adjustments
5. ✅ **Weights Applied**: Composite scoring uses adaptive weights

---

## Troubleshooting

### If verification script fails:
1. Make sure you're in the project root directory
2. Check Python can import modules: `python -c "import adaptive_signal_optimizer"`
3. Check if virtual environment is activated (if using one)

### If no logs found:
1. Check if trades are actually closing (check Alpaca account)
2. Check `logs/exit.jsonl` for exit events
3. Verify `log_exit_attribution()` is being called

### If learning not processing:
1. Check `ENABLE_PER_TICKER_LEARNING=true` in config
2. Verify `learn_from_outcomes()` is called (line 5357)
3. Check for errors in `data/optimizer_errors.jsonl`

---

## Files Reference

1. **VERIFY_LEARNING_PIPELINE.py** - Full diagnostic (run this first)
2. **check_learning_status.py** - Quick status check (create from Step 3)
3. **check_trades_closing.py** - Check if trades are closing (create from Step 4)
4. **manual_learning_check.py** - Detailed learning report (create from Step 5)
5. **process_historical_trades.py** - Process old trades (create from Step 6)
6. **LEARNING_PIPELINE_ANALYSIS.md** - Understand the issues
7. **LEARNING_PIPELINE_FIXES.md** - See specific code fixes

---

## Next Actions

1. **Run verification**: `python VERIFY_LEARNING_PIPELINE.py`
2. **Check if trades closing**: Review dashboard or create `check_trades_closing.py`
3. **Monitor daily**: Run verification script daily to track learning progress
4. **Review fixes**: Read `LEARNING_PIPELINE_FIXES.md` for additional improvements
