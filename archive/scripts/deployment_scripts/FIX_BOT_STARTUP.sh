#!/bin/bash
# Fix bot startup issues - check logs and restart properly

echo "=================================================================================="
echo "FIXING BOT STARTUP - CHECKING LOGS AND ERRORS"
echo "=================================================================================="

cd ~/stock-bot

# 1. Check supervisor logs for errors
echo ""
echo "1. Checking supervisor logs for errors..."
if [ -f "logs/supervisor.jsonl" ]; then
    echo "  Recent supervisor events:"
    tail -20 logs/supervisor.jsonl | grep -E "ERROR|FAILED|DIED|exited" || echo "    No errors found"
else
    echo "  No supervisor log found"
fi

# 2. Try to get screen output
echo ""
echo "2. Checking screen session output..."
screen -S supervisor -X hardcopy /tmp/supervisor_output.txt 2>/dev/null
if [ -f "/tmp/supervisor_output.txt" ]; then
    echo "  Last 30 lines from supervisor:"
    tail -30 /tmp/supervisor_output.txt | grep -E "ERROR|FAILED|trading-bot|main.py" || echo "    (no relevant errors)"
    rm /tmp/supervisor_output.txt
else
    echo "  Could not capture screen output"
fi

# 3. Check if main.py can even run
echo ""
echo "3. Testing if main.py can run..."
source venv/bin/activate
timeout 5 python main.py --help 2>&1 | head -5 || {
    echo "  ⚠️  main.py failed to start or has syntax errors"
    echo "  Checking for syntax errors..."
    python -m py_compile main.py 2>&1 | head -10
}

# 4. Check for import errors
echo ""
echo "4. Checking for import errors..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    import main
    print('  ✓ main.py imports successfully')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1 | head -20

# 5. Check if secrets are actually loaded
echo ""
echo "5. Testing if secrets are loaded by Python..."
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
alpaca_key = os.getenv('ALPACA_KEY') or os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_SECRET') or os.getenv('ALPACA_API_SECRET')
uw_key = os.getenv('UW_API_KEY')
print(f'  ALPACA_KEY: {\"SET\" if alpaca_key else \"NOT SET\"}')
print(f'  ALPACA_SECRET: {\"SET\" if alpaca_secret else \"NOT SET\"}')
print(f'  UW_API_KEY: {\"SET\" if uw_key else \"NOT SET\"}')
if not alpaca_key or not alpaca_secret:
    print('  ❌ CRITICAL: Alpaca credentials not loaded!')
    print('     Check .env file format and ensure load_dotenv() works')
"

# 6. Stop everything and restart with verbose logging
echo ""
echo "6. Stopping all processes..."
pkill -f deploy_supervisor
pkill -f "python.*main.py"
pkill -f "python.*dashboard.py"
pkill -f "python.*uw_flow_daemon"
sleep 3

# 7. Start supervisor and capture output
echo ""
echo "7. Starting supervisor with output capture..."
source venv/bin/activate
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py 2>&1 | tee -a logs/supervisor_startup.log"

# 8. Wait and check
echo ""
echo "8. Waiting 10 seconds for services to start..."
sleep 10

# 9. Final check
echo ""
echo "9. Final status check..."
BOT_RUNNING=$(pgrep -f "python.*main.py" > /dev/null && echo "YES" || echo "NO")
DASHBOARD_RUNNING=$(pgrep -f "python.*dashboard.py" > /dev/null && echo "YES" || echo "NO")
SUPERVISOR_RUNNING=$(pgrep -f "deploy_supervisor" > /dev/null && echo "YES" || echo "NO")

echo "  Bot (main.py): $BOT_RUNNING"
echo "  Dashboard: $DASHBOARD_RUNNING"
echo "  Supervisor: $SUPERVISOR_RUNNING"

if [ "$BOT_RUNNING" = "NO" ]; then
    echo ""
    echo "  ❌ Bot still not running!"
    echo "  Check startup log: tail -50 logs/supervisor_startup.log"
    echo "  Check supervisor screen: screen -r supervisor"
    echo "  Look for errors in the output above"
else
    echo ""
    echo "  ✓ Bot is running!"
fi

echo ""
echo "=================================================================================="
echo "DIAGNOSIS COMPLETE"
echo "=================================================================================="
