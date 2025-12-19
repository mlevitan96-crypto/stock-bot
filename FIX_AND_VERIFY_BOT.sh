#!/bin/bash
# Complete fix and verification script

cd ~/stock-bot

echo "=========================================="
echo "STEP 1: Pull latest fixes"
echo "=========================================="
git pull origin main
echo ""

echo "=========================================="
echo "STEP 2: Check current bot status"
echo "=========================================="
python3 DIAGNOSE_BOT_EXECUTION.py
echo ""

echo "=========================================="
echo "STEP 3: Check worker thread status"
echo "=========================================="
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    # Try to check if worker is running by looking at logs
    from pathlib import Path
    import json
    import time
    
    worker_log = Path('logs/worker.jsonl')
    if worker_log.exists():
        lines = worker_log.read_text().splitlines()
        if lines:
            last_event = json.loads(lines[-1])
            ts = last_event.get('_ts', 0)
            age_min = (time.time() - ts) / 60
            msg = last_event.get('msg', 'unknown')
            print(f'Last worker event: {age_min:.1f} min ago - {msg}')
            if age_min > 5:
                print('  ⚠️  Worker appears stalled')
            else:
                print('  ✅ Worker active')
        else:
            print('  ⚠️  No worker events logged')
    else:
        print('  ⚠️  Worker log does not exist')
    
    # Check watchdog
    watchdog_log = Path('logs/watchdog.jsonl')
    if watchdog_log.exists():
        lines = watchdog_log.read_text().splitlines()
        if lines:
            last_event = json.loads(lines[-1])
            ts = last_event.get('_ts', 0)
            age_min = (time.time() - ts) / 60
            msg = last_event.get('msg', 'unknown')
            print(f'Last watchdog event: {age_min:.1f} min ago - {msg}')
except Exception as e:
    print(f'Error checking status: {e}')
"
echo ""

echo "=========================================="
echo "STEP 4: Check for exceptions"
echo "=========================================="
if [ -f "logs/worker_error.jsonl" ]; then
    echo "Recent worker errors:"
    tail -3 logs/worker_error.jsonl | python3 -c "
import sys, json, time
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('_ts', 0)
        age_min = (time.time() - ts) / 60 if ts > 0 else 0
        error = data.get('error', 'unknown')
        print(f'  {age_min:.1f} min ago: {error[:150]}')
    except:
        pass
"
else
    echo "No worker error log"
fi
echo ""

echo "=========================================="
echo "STEP 5: Check run_once logs"
echo "=========================================="
if [ -f "logs/run_once.jsonl" ]; then
    echo "Recent run_once events:"
    tail -5 logs/run_once.jsonl | python3 -c "
import sys, json, time
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('_ts', 0)
        age_min = (time.time() - ts) / 60 if ts > 0 else 0
        msg = data.get('msg', 'unknown')
        error = data.get('error', '')
        if error:
            print(f'  {age_min:.1f} min ago: ERROR - {error[:100]}')
        else:
            print(f'  {age_min:.1f} min ago: {msg}')
    except:
        pass
"
else
    echo "⚠️  run_once log does not exist - bot may not be executing"
fi
echo ""

echo "=========================================="
echo "STEP 6: Restart bot if needed"
echo "=========================================="
echo "If worker is stalled, restart the bot:"
echo "  PID=\$(pgrep -f 'main.py' | head -1)"
echo "  [ -n \"\$PID\" ] && kill \$PID && sleep 3"
echo "  screen -dmS trading python3 main.py"
echo ""

echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
