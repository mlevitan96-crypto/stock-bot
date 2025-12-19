#!/bin/bash
# Check bot status and diagnose execution issues

cd ~/stock-bot

echo "=========================================="
echo "BOT STATUS CHECK"
echo "=========================================="
echo ""

# 1. Check if process is running
echo "1. PROCESS STATUS"
echo "-" * 40
PID=$(pgrep -f "main.py" | head -1)
if [ -n "$PID" ]; then
    echo "✅ Bot running (PID: $PID)"
    ps aux | grep "$PID" | grep -v grep
else
    echo "❌ Bot NOT running"
    exit 1
fi
echo ""

# 2. Check recent run.jsonl entries
echo "2. EXECUTION CYCLES"
echo "-" * 40
if [ -f "logs/run.jsonl" ]; then
    TOTAL=$(wc -l < logs/run.jsonl)
    echo "Total cycles logged: $TOTAL"
    
    if [ "$TOTAL" -gt 0 ]; then
        echo ""
        echo "Last 3 cycles:"
        tail -3 logs/run.jsonl | while read line; do
            echo "$line" | python3 -c "
import sys, json, time
try:
    data = json.load(sys.stdin)
    ts = data.get('_ts', 0)
    age_min = (time.time() - ts) / 60 if ts > 0 else 0
    clusters = data.get('clusters', 0)
    orders = data.get('orders', 0)
    msg = data.get('msg', 'unknown')
    print(f'  {age_min:.1f} min ago: {msg}, {clusters} clusters, {orders} orders')
except:
    print('  (could not parse)')
"
        done
    else
        echo "⚠️  No cycles logged"
    fi
else
    echo "❌ Run log file does not exist"
fi
echo ""

# 3. Check for exceptions
echo "3. RECENT ERRORS"
echo "-" * 40
if [ -f "logs/worker_error.jsonl" ]; then
    ERRORS=$(tail -5 logs/worker_error.jsonl | wc -l)
    if [ "$ERRORS" -gt 0 ]; then
        echo "Last errors:"
        tail -3 logs/worker_error.jsonl | python3 -c "
import sys, json, time
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('_ts', 0)
        age_min = (time.time() - ts) / 60 if ts > 0 else 0
        error = data.get('error', 'unknown')
        print(f'  {age_min:.1f} min ago: {error[:100]}')
    except:
        pass
"
    else
        echo "✅ No recent errors"
    fi
else
    echo "⚠️  Error log does not exist"
fi
echo ""

# 4. Check worker logs
echo "4. WORKER LOGS"
echo "-" * 40
if [ -f "logs/worker.jsonl" ]; then
    echo "Last worker events:"
    tail -5 logs/worker.jsonl | python3 -c "
import sys, json, time
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('_ts', 0)
        age_min = (time.time() - ts) / 60 if ts > 0 else 0
        msg = data.get('msg', 'unknown')
        iter = data.get('iter', '?')
        print(f'  {age_min:.1f} min ago: {msg} (iter: {iter})')
    except:
        pass
"
else
    echo "⚠️  Worker log does not exist"
fi
echo ""

# 5. Check if watchdog is running
echo "5. WATCHDOG STATUS"
echo "-" * 40
if [ -f "logs/watchdog.jsonl" ]; then
    echo "Last watchdog events:"
    tail -3 logs/watchdog.jsonl | python3 -c "
import sys, json, time
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('_ts', 0)
        age_min = (time.time() - ts) / 60 if ts > 0 else 0
        msg = data.get('msg', 'unknown')
        print(f'  {age_min:.1f} min ago: {msg}')
    except:
        pass
"
else
    echo "⚠️  Watchdog log does not exist"
fi
echo ""

# 6. Check run_once logs
echo "6. RUN_ONCE LOGS"
echo "-" * 40
if [ -f "logs/run_once.jsonl" ]; then
    echo "Last run_once events:"
    tail -3 logs/run_once.jsonl | python3 -c "
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
    echo "⚠️  run_once log does not exist"
fi
echo ""

echo "=========================================="
echo "DIAGNOSIS COMPLETE"
echo "=========================================="
