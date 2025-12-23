#!/bin/bash
# Restart bot and verify it's working

echo "=================================================================================="
echo "RESTARTING BOT AND VERIFYING"
echo "=================================================================================="

cd ~/stock-bot

# 1. Stop everything
echo ""
echo "1. Stopping all processes..."
pkill -f deploy_supervisor
pkill -f "python.*main.py"
pkill -f "python.*dashboard.py"
pkill -f "python.*uw_flow_daemon"
sleep 3

# 2. Verify stopped
echo ""
echo "2. Verifying processes stopped..."
ps aux | grep -E "main.py|dashboard.py|uw_flow_daemon|deploy_supervisor" | grep -v grep || echo "  ✓ All processes stopped"

# 3. Check .env file exists
echo ""
echo "3. Checking .env file..."
if [ -f ".env" ]; then
    echo "  ✓ .env file exists"
    # Check if it has required variables (without showing values)
    if grep -q "ALPACA_KEY" .env && grep -q "ALPACA_SECRET" .env; then
        echo "  ✓ ALPACA_KEY and ALPACA_SECRET found in .env"
    else
        echo "  ⚠️  ALPACA_KEY or ALPACA_SECRET missing from .env"
    fi
    if grep -q "UW_API_KEY" .env; then
        echo "  ✓ UW_API_KEY found in .env"
    else
        echo "  ⚠️  UW_API_KEY missing from .env"
    fi
else
    echo "  ❌ .env file NOT FOUND"
    echo "     Create .env file with ALPACA_KEY, ALPACA_SECRET, UW_API_KEY"
fi

# 4. Restart supervisor
echo ""
echo "4. Restarting supervisor..."
source venv/bin/activate
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
sleep 5

# 5. Verify processes started
echo ""
echo "5. Verifying processes started..."
sleep 3
ps aux | grep -E "deploy_supervisor|main.py|dashboard.py|uw_flow_daemon" | grep -v grep

# 6. Check supervisor logs
echo ""
echo "6. Checking supervisor status..."
echo "  To view logs: screen -r supervisor"
echo "  (Press Ctrl+A then D to detach)"

# 7. Wait and check again
echo ""
echo "7. Waiting 10 seconds for services to initialize..."
sleep 10

# 8. Final check
echo ""
echo "8. Final process check..."
# More robust process detection - check multiple patterns
BOT_RUNNING="NO"
if pgrep -f "python.*main.py" > /dev/null 2>&1; then
    BOT_RUNNING="YES"
elif pgrep -f "main.py" > /dev/null 2>&1; then
    BOT_RUNNING="YES"
elif ps aux | grep -E "[p]ython.*main\.py|[p]ython main" > /dev/null 2>&1; then
    BOT_RUNNING="YES"
fi

DASHBOARD_RUNNING=$(pgrep -f "python.*dashboard.py" > /dev/null 2>&1 && echo "YES" || echo "NO")
SUPERVISOR_RUNNING=$(pgrep -f "deploy_supervisor" > /dev/null 2>&1 && echo "YES" || echo "NO")
UW_DAEMON_RUNNING=$(pgrep -f "uw_flow_daemon" > /dev/null 2>&1 && echo "YES" || echo "NO")

echo "  Bot (main.py): $BOT_RUNNING"
echo "  Dashboard: $DASHBOARD_RUNNING"
echo "  Supervisor: $SUPERVISOR_RUNNING"
echo "  UW Daemon: $UW_DAEMON_RUNNING"

# Also check if bot is actually responding via health endpoint
BOT_RESPONDING="NO"
if command -v curl > /dev/null 2>&1; then
    if curl -s -m 2 http://localhost:8081/health > /dev/null 2>&1; then
        BOT_RESPONDING="YES"
    fi
fi

if [ "$BOT_RESPONDING" = "YES" ]; then
    echo "  Bot Health Endpoint: RESPONDING"
elif [ "$BOT_RUNNING" = "YES" ]; then
    echo "  Bot Health Endpoint: NOT RESPONDING (may still be starting)"
else
    echo "  Bot Health Endpoint: NOT RESPONDING"
fi

if [ "$BOT_RUNNING" = "YES" ] || [ "$BOT_RESPONDING" = "YES" ]; then
    echo ""
    echo "  ✓ Bot is running!"
    echo "  Run diagnostic again in 1 minute: python3 diagnose_alpaca_orders.py"
else
    echo ""
    echo "  ❌ Bot is NOT running"
    echo "  Check supervisor logs: screen -r supervisor"
    echo "  Look for errors in the logs"
fi

echo ""
echo "=================================================================================="
echo "RESTART COMPLETE"
echo "=================================================================================="
echo ""
echo "Next steps:"
echo "1. Wait 1-2 minutes for bot to initialize"
echo "2. Run diagnostic: python3 diagnose_alpaca_orders.py"
echo "3. Check supervisor logs: screen -r supervisor"
echo "4. Check if signals are being generated"
echo ""
