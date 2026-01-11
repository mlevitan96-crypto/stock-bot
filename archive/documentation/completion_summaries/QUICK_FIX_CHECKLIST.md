# Quick Fix Checklist - When No Trades

**Use this checklist when bot isn't trading.**

## Step 1: Verify Bot is Running
```bash
ps aux | grep "python.*main.py"
# Should see process running
```
**If not running:**
```bash
systemctl restart trading-bot.service
```

## Step 2: Check Cycles
```bash
tail -1 logs/run.jsonl | jq '{ts, clusters, orders}'
# Check timestamp - should be within last 60 seconds
```
**If stale:**
- See Step 1 (restart)

## Step 3: Clear Freezes
```bash
cat state/governor_freezes.json | jq '.[] | select(.active == true)'
# Should be empty
```
**If freezes exist:**
```bash
python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timezone
freeze_file = Path('state/governor_freezes.json')
if freeze_file.exists():
    data = json.load(open(freeze_file))
    for k in list(data.keys()):
        if data[k].get('active', False):
            data[k]['active'] = False
            data[k]['cleared_at'] = datetime.now(timezone.utc).isoformat()
    json.dump(data, open(freeze_file, 'w'), indent=2)
EOF
```

## Step 4: Verify Fixes
```bash
python3 verify_weight_fix.py
# Should print: 2.4
```

## Step 5: Check Scores
```bash
tail -20 data/uw_attribution.jsonl | jq -r '.symbol + ": " + (.score | tostring) + " -> " + .decision'
# Should see scores >= 2.7 with decision="signal"
```

## Step 6: Check Gate Events
```bash
tail -20 logs/composite_gate.jsonl | jq -r 'select(.msg == "accepted") | .symbol'
# Should see accepted signals
```

## Step 7: Check Orders
```bash
tail -20 logs/orders.jsonl | jq -r '.symbol + ": " + .action'
# Should see order submissions
```

---

## Common Issues & Quick Fixes

### Issue: Cycles Not Running
**Fix:**
```bash
systemctl restart trading-bot.service
sleep 10
tail -f logs/run.jsonl  # Watch for new cycles
```

### Issue: Scores Too Low (0.0-0.6)
**Check:**
```bash
python3 verify_weight_fix.py  # Should be 2.4
```
**If not 2.4:** Code fix not loaded, restart bot

### Issue: All Signals Blocked
**Check:**
```bash
tail -20 logs/composite_gate.jsonl | jq -r '.threshold' | sort -u
# Should be 2.70, not 3.50
```
**If 3.50:**
```bash
rm state/uw_thresholds_hierarchical.json
systemctl restart trading-bot.service
```

### Issue: No Cache Data
**Check:**
```bash
cat data/uw_flow_cache.json | jq 'keys | length'
# Should be > 1
```
**If 0 or 1:**
```bash
ps aux | grep uw_flow_daemon
# Should see daemon running
```

---

## Full Diagnostic Script
```bash
python3 diagnose_complete.py
```
This checks everything and prints a summary.
