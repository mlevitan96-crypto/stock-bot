#!/bin/bash
# Complete fix for bot and dashboard - handles all issues

set -e  # Exit on error

echo "=========================================="
echo "COMPLETE SYSTEM FIX"
echo "=========================================="
echo ""

cd ~/stock-bot

# 1. Switch to main branch
echo "1. Switching to main branch..."
echo "----------------------------------------"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Currently on branch: $CURRENT_BRANCH"
    echo "   Switching to main..."
    git checkout main 2>&1 || {
        echo "   Stashing changes and switching..."
        git stash
        git checkout main
    }
fi
git pull origin main
echo "✅ On main branch"
echo ""

# 2. Install dependencies (handle urllib3 conflict)
echo "2. Installing Python dependencies..."
echo "----------------------------------------"
# Install flask first (needed for dashboard)
pip3 install --break-system-packages flask 2>&1 | tail -3

# Install alpaca-trade-api (skip urllib3 if it conflicts)
pip3 install --break-system-packages --ignore-installed urllib3 alpaca-trade-api 2>&1 | tail -5 || {
    echo "⚠️  urllib3 conflict - trying alternative..."
    pip3 install --break-system-packages --no-deps alpaca-trade-api 2>&1 | tail -3
}
echo ""

# 3. Stop all existing processes
echo "3. Stopping existing processes..."
echo "----------------------------------------"
pkill -f "python.*main.py" 2>/dev/null && echo "   Stopped main.py processes" || echo "   No main.py processes found"
pkill -f "python.*dashboard.py" 2>/dev/null && echo "   Stopped dashboard.py processes" || echo "   No dashboard.py processes found"
sleep 2
echo ""

# 4. Test imports
echo "4. Testing critical imports..."
echo "----------------------------------------"
python3 -c "
import sys
errors = []
try:
    import flask
    print('✅ flask')
except ImportError as e:
    errors.append(f'flask: {e}')
    print('❌ flask')

try:
    import alpaca_trade_api
    print('✅ alpaca_trade_api')
except ImportError as e:
    errors.append(f'alpaca_trade_api: {e}')
    print('❌ alpaca_trade_api')

try:
    from sre_monitoring import get_sre_health
    print('✅ sre_monitoring')
except ImportError as e:
    errors.append(f'sre_monitoring: {e}')
    print('❌ sre_monitoring')

if errors:
    print(f'\n⚠️  {len(errors)} import errors found')
    sys.exit(1)
else:
    print('\n✅ All imports successful')
"
IMPORT_STATUS=$?
echo ""

# 5. Start bot
if [ $IMPORT_STATUS -eq 0 ]; then
    echo "5. Starting bot..."
    echo "----------------------------------------"
    screen -dmS trading python3 main.py
    sleep 3
    if ps aux | grep "python.*main.py" | grep -v grep > /dev/null; then
        echo "✅ Bot started"
    else
        echo "❌ Bot failed to start - check logs: screen -r trading"
    fi
    echo ""
    
    # 6. Start dashboard
    echo "6. Starting dashboard..."
    echo "----------------------------------------"
    screen -dmS dashboard python3 dashboard.py
    sleep 3
    if ps aux | grep "python.*dashboard.py" | grep -v grep > /dev/null; then
        echo "✅ Dashboard started"
    else
        echo "❌ Dashboard failed to start - check logs: screen -r dashboard"
    fi
    echo ""
else
    echo "5. Skipping bot/dashboard start (import errors)"
    echo "   Fix imports first, then run:"
    echo "   screen -dmS trading python3 main.py"
    echo "   screen -dmS dashboard python3 dashboard.py"
    echo ""
fi

# 7. Status check
echo "7. Final status check..."
echo "----------------------------------------"
BOT_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | head -1)
DASHBOARD_PID=$(ps aux | grep "python.*dashboard.py" | grep -v grep | awk '{print $2}' | head -1)

if [ ! -z "$BOT_PID" ]; then
    echo "✅ Bot running (PID: $BOT_PID)"
else
    echo "❌ Bot not running"
fi

if [ ! -z "$DASHBOARD_PID" ]; then
    echo "✅ Dashboard running (PID: $DASHBOARD_PID)"
    echo "   Access at: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "❌ Dashboard not running"
fi
echo ""

# 8. Test SRE endpoint
echo "8. Testing SRE endpoint..."
echo "----------------------------------------"
sleep 2
curl -s http://localhost:5000/api/sre/health | python3 -m json.tool 2>/dev/null | head -10 || {
    echo "⚠️  SRE endpoint not responding yet (may need a few seconds)"
}
echo ""

echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
echo ""
echo "To check logs:"
echo "  screen -r trading    # Bot logs"
echo "  screen -r dashboard  # Dashboard logs"
echo ""
echo "To access dashboard:"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo ""
