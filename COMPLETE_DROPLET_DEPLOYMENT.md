# Complete Droplet Deployment - Phase 2 Activation

## ALL Commands You Need (Copy/Paste Ready)

### Step 1: Pull Latest Code (Includes Phase 2)

```bash
# SSH into droplet (if not already there)
# ssh root@your_droplet_ip

# Navigate to project
cd ~/stock-bot

# Pull latest code (includes Phase 2)
git pull origin main
```

### Step 2: Verify Phase 2 Code is Present

```bash
# Check Phase 2 methods exist
grep -n "analyze_risk_limits\|analyze_execution_quality" comprehensive_learning_orchestrator.py

# Should show line numbers where these methods are defined
```

### Step 3: Test Phase 2 Methods Work

```bash
# Test that Phase 2 can be imported
python3 -c "
from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator
o = ComprehensiveLearningOrchestrator()
print('Phase 2 methods available:')
print('  - analyze_risk_limits:', hasattr(o, 'analyze_risk_limits'))
print('  - analyze_execution_quality:', hasattr(o, 'analyze_execution_quality'))
print('  - analyze_profit_targets:', hasattr(o, 'analyze_profit_targets'))
print('SUCCESS: All Phase 2 methods are available!')
"
```

### Step 4: Find and Stop Current Bot Process

```bash
# Find the running bot
ps aux | grep "main.py" | grep -v grep

# Note the PID (process ID) - example: 313598

# Kill the process (replace 313598 with your actual PID)
kill 313598

# Wait a moment
sleep 3

# Verify it's stopped
ps aux | grep "main.py" | grep -v grep
# Should show nothing
```

### Step 5: Restart Bot with New Code

```bash
# Option A: Start in screen session (recommended)
screen -dmS trading python3 main.py

# Option B: Start in background with nohup
nohup python3 main.py > logs/bot.log 2>&1 &

# Option C: Start in existing screen session
screen -S trading -X stuff "python3 main.py\n"
```

### Step 6: Verify Bot is Running with New Code

```bash
# Check process is running
ps aux | grep "main.py" | grep -v grep

# Check logs show startup
tail -20 logs/run.jsonl | tail -5

# Verify learning system is active
tail -f logs/comprehensive_learning.log
# Press Ctrl+C to stop watching
```

### Step 7: Verify Phase 2 Will Run

```bash
# Check that learning cycle includes Phase 2
python3 -c "
from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator
import inspect
o = ComprehensiveLearningOrchestrator()
source = inspect.getsource(o.run_learning_cycle)
if 'risk_limits' in source and 'execution_quality' in source:
    print('SUCCESS: Phase 2 is integrated into learning cycle!')
else:
    print('ERROR: Phase 2 not found in learning cycle')
"
```

### Step 8: Monitor After Restart

```bash
# Watch for any errors
tail -f logs/*.log | grep -i error

# Check bot is trading
tail -f logs/run.jsonl

# Verify learning cycle will run (after market close)
# The next learning cycle will include Phase 2 automatically
```

---

## Complete One-Liner (If You Want to Do It All at Once)

```bash
cd ~/stock-bot && \
git pull origin main && \
python3 -c "from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator; o = ComprehensiveLearningOrchestrator(); print('Phase 2 available:', hasattr(o, 'analyze_risk_limits'))" && \
PID=$(ps aux | grep "main.py" | grep -v grep | awk '{print $2}') && \
[ -n "$PID" ] && kill $PID && sleep 3 && \
screen -dmS trading python3 main.py && \
sleep 2 && \
ps aux | grep "main.py" | grep -v grep && \
echo "SUCCESS: Bot restarted with Phase 2!"
```

---

## Verification Checklist

After completing all steps:

- [ ] Code pulled: `git pull origin main` completed
- [ ] Phase 2 methods exist: Test command shows all methods available
- [ ] Old process stopped: `ps aux | grep main.py` shows nothing
- [ ] New process running: `ps aux | grep main.py` shows new PID
- [ ] No errors: `tail logs/*.log | grep error` shows no critical errors
- [ ] Learning active: `tail logs/comprehensive_learning.log` shows activity

---

## What Happens Next

1. **Bot runs normally** - Trading continues
2. **After market close** - Learning cycle runs automatically
3. **Phase 2 activates** - Risk limits and execution quality are analyzed
4. **Results appear** - Check `logs/comprehensive_learning.jsonl` tomorrow

---

## Check Results Tomorrow

```bash
# After market close, check learning results
tail -1 logs/comprehensive_learning.jsonl | python3 -m json.tool

# Look for Phase 2 results
tail -1 logs/comprehensive_learning.jsonl | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
print('Exit Thresholds:', d.get('exit_thresholds', {}).get('status'))
print('Profit Targets:', d.get('profit_targets', {}).get('status'))
print('Risk Limits:', d.get('risk_limits', {}).get('status'))
print('Execution Quality:', d.get('execution_quality', {}).get('status'))
"
```

---

## Troubleshooting

### If git pull fails:
```bash
# Check you're in the right directory
pwd
# Should show: /root/stock-bot

# Check git status
git status
```

### If python3 can't import:
```bash
# Install dependencies
pip3 install -r requirements.txt
```

### If process won't start:
```bash
# Check for errors
python3 main.py
# Look for error messages
```

### If screen session issues:
```bash
# List screen sessions
screen -ls

# Kill all screen sessions
screen -X -S trading quit

# Start fresh
screen -dmS trading python3 main.py
```

---

## Summary

**Phase 2 is already in the code** - you just need to:
1. Pull latest code
2. Restart the bot
3. Wait for next learning cycle

That's it! Phase 2 will activate automatically.
