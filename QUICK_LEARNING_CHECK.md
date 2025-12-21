# Quick Learning Pipeline Check - Copy/Paste Ready

## ⚠️ IMPORTANT: Run from Project Root

**Project Root**: `c:\Users\markl\OneDrive\Documents\Cursor\stock-bot\`

All commands below assume you're in this directory.

---

## Step 1: Full Verification (Run This First)

**Copy and paste this entire block**:

```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python VERIFY_LEARNING_PIPELINE.py
```

This will show you:
- Whether logs exist
- If learning system is initialized  
- Component sample counts
- Whether weights have been updated
- Any errors

**Output saved to**: `learning_pipeline_report.json`

---

## Step 2: Quick Status Check

**Copy and paste this entire block**:

```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_learning_status.py
```

This shows:
- Learning system status
- Log files status
- Component samples
- Learning state

---

## Step 3: Check if Trades Are Closing

**Copy and paste this entire block**:

```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python check_trades_closing.py
```

This shows:
- Exit events
- Closed trades
- Whether logging is working

---

## Step 4: Detailed Learning Report

**Copy and paste this entire block**:

```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
python manual_learning_check.py
```

This shows:
- All component performance
- Multipliers (which have changed from default)
- Win rates per component

---

## What to Look For

### ✅ Learning is Working When:
- Attribution logs exist with trades
- Component sample counts > 0
- Multipliers changed from 1.0 (after 30+ samples)
- Learning updates logged in `data/weight_learning.jsonl`

### ❌ Issues to Watch For:
- No logs found = No trades closing OR logging broken
- All multipliers at 1.0 = Learning hasn't adjusted yet (need 30+ samples)
- No learning state file = Learning system not initialized
- Components with 0 samples = Trades not being processed

---

## If Scripts Don't Work

**Check you're in the right directory**:
```powershell
cd c:\Users\markl\OneDrive\Documents\Cursor\stock-bot
dir main.py
```

**If main.py exists**, you're in the right place.  
**If not**, navigate to where `main.py` is located.

---

## Files Created

All these scripts are in the project root:
- `VERIFY_LEARNING_PIPELINE.py` - Full diagnostic
- `check_learning_status.py` - Quick status
- `check_trades_closing.py` - Check trades
- `manual_learning_check.py` - Detailed report

Run them all from the same directory (project root).
