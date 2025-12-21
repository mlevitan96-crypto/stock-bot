# Droplet Commands - Learning Pipeline Check

## ⚠️ IMPORTANT: Run from Project Root on Droplet

**Project Root on Droplet**: `~/stock-bot`

All commands below assume you're SSH'd into the droplet and in this directory.

---

## Step 1: Pull Latest Changes

**Copy and paste this entire block**:

```bash
cd ~/stock-bot
git pull origin main
```

---

## Step 2: Full Verification (Run This First)

**Copy and paste this entire block**:

```bash
cd ~/stock-bot
python3 VERIFY_LEARNING_PIPELINE.py
```

This will show you:
- Whether logs exist
- If learning system is initialized  
- Component sample counts
- Whether weights have been updated
- Any errors

**Output saved to**: `learning_pipeline_report.json`

---

## Step 3: Quick Status Check

**Copy and paste this entire block**:

```bash
cd ~/stock-bot
python3 check_learning_status.py
```

This shows:
- Learning system status
- Log files status
- Component samples
- Learning state

---

## Step 4: Check if Trades Are Closing

**Copy and paste this entire block**:

```bash
cd ~/stock-bot
python3 check_trades_closing.py
```

This shows:
- Exit events
- Closed trades
- Whether logging is working

---

## Step 5: Detailed Learning Report

**Copy and paste this entire block**:

```bash
cd ~/stock-bot
python3 manual_learning_check.py
```

This shows:
- All component performance
- Multipliers (which have changed from default)
- Win rates per component

---

## Quick One-Liner: Pull and Run Full Check

**Copy and paste this entire block**:

```bash
cd ~/stock-bot && git pull origin main && python3 VERIFY_LEARNING_PIPELINE.py
```

---

## If Using Virtual Environment

If your droplet uses a virtual environment:

```bash
cd ~/stock-bot
source venv/bin/activate
git pull origin main
python3 VERIFY_LEARNING_PIPELINE.py
python3 check_learning_status.py
python3 check_trades_closing.py
python3 manual_learning_check.py
```

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

## View Results

**View the full report**:
```bash
cd ~/stock-bot
cat learning_pipeline_report.json | python3 -m json.tool
```

**View recent attribution logs**:
```bash
cd ~/stock-bot
tail -20 logs/attribution.jsonl | python3 -m json.tool
```

**View learning state**:
```bash
cd ~/stock-bot
cat state/signal_weights.json | python3 -m json.tool | head -50
```

---

## Troubleshooting

**If scripts don't work**:

1. **Check you're in the right directory**:
   ```bash
   cd ~/stock-bot
   ls main.py
   ```

2. **Check Python version**:
   ```bash
   python3 --version
   ```

3. **Check if modules are available**:
   ```bash
   python3 -c "from adaptive_signal_optimizer import get_optimizer; print('OK')"
   ```

4. **If module not found, activate venv**:
   ```bash
   source venv/bin/activate
   python3 VERIFY_LEARNING_PIPELINE.py
   ```

---

## All Commands in One Place

**Complete check sequence** (copy/paste ready):

```bash
cd ~/stock-bot
git pull origin main
echo "=== Full Verification ==="
python3 VERIFY_LEARNING_PIPELINE.py
echo ""
echo "=== Quick Status ==="
python3 check_learning_status.py
echo ""
echo "=== Check Trades Closing ==="
python3 check_trades_closing.py
echo ""
echo "=== Detailed Report ==="
python3 manual_learning_check.py
```

---

## Files Created

All these scripts are in the project root (`~/stock-bot`):
- `VERIFY_LEARNING_PIPELINE.py` - Full diagnostic
- `check_learning_status.py` - Quick status
- `check_trades_closing.py` - Check trades
- `manual_learning_check.py` - Detailed report

Run them all from the same directory (project root).
