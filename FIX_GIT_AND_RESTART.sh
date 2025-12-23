#!/bin/bash
# Fix git conflicts and restart bot with latest fixes

echo "=================================================================================="
echo "FIXING GIT CONFLICTS AND RESTARTING BOT"
echo "=================================================================================="

cd ~/stock-bot

# 1. Stash any local changes
echo ""
echo "1. Stashing local changes..."
git stash

# 2. Pull latest fixes
echo ""
echo "2. Pulling latest fixes..."
git pull origin main

# 3. Stop all processes
echo ""
echo "3. Stopping all processes..."
pkill -f deploy_supervisor
pkill -f "python.*main.py"
pkill -f "python.*dashboard.py"
pkill -f "python.*uw_flow_daemon"
sleep 3

# 4. Verify .env exists
echo ""
echo "4. Checking .env file..."
if [ -f ".env" ]; then
    echo "  ✓ .env file exists"
    if grep -q "ALPACA_KEY" .env && grep -q "ALPACA_SECRET" .env; then
        echo "  ✓ ALPACA_KEY and ALPACA_SECRET found in .env"
    else
        echo "  ⚠️  ALPACA credentials not found in .env"
    fi
    if grep -q "UW_API_KEY" .env; then
        echo "  ✓ UW_API_KEY found in .env"
    else
        echo "  ⚠️  UW_API_KEY not found in .env"
    fi
else
    echo "  ❌ .env file not found"
fi

# 5. Activate venv and start supervisor
echo ""
echo "5. Starting supervisor..."
source venv/bin/activate
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"

# 6. Wait for services to start
echo ""
echo "6. Waiting 15 seconds for services to initialize..."
sleep 15

# 7. Check status
echo ""
echo "7. Checking service status..."
BOT_RUNNING=$(pgrep -f "python.*main.py" > /dev/null && echo "YES" || echo "NO")
DASHBOARD_RUNNING=$(pgrep -f "python.*dashboard.py" > /dev/null && echo "YES" || echo "NO")
SUPERVISOR_RUNNING=$(pgrep -f "deploy_supervisor" > /dev/null && echo "YES" || echo "NO")
UW_DAEMON_RUNNING=$(pgrep -f "uw_flow_daemon" > /dev/null && echo "YES" || echo "NO")

echo "  Bot (main.py): $BOT_RUNNING"
echo "  Dashboard: $DASHBOARD_RUNNING"
echo "  Supervisor: $SUPERVISOR_RUNNING"
echo "  UW Daemon: $UW_DAEMON_RUNNING"

if [ "$BOT_RUNNING" = "YES" ] && [ "$UW_DAEMON_RUNNING" = "YES" ]; then
    echo ""
    echo "  ✓ All services running!"
else
    echo ""
    echo "  ⚠️  Some services not running. Check logs:"
    echo "     screen -r supervisor"
fi

echo ""
echo "=================================================================================="
echo "RESTART COMPLETE"
echo "=================================================================================="
