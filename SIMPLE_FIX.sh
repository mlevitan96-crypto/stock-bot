#!/bin/bash
# Simple fix - handles git conflicts and gets everything running

cd ~/stock-bot

echo "=========================================="
echo "SIMPLE FIX - Step by Step"
echo "=========================================="
echo ""

# 1. Handle git conflicts
echo "Step 1: Resolving git conflicts..."
git stash
git checkout main 2>/dev/null || git checkout -b main origin/main
git pull origin main
echo "✅ Git fixed"
echo ""

# 2. Install flask (ignore blinker conflict)
echo "Step 2: Installing Flask..."
pip3 install --break-system-packages --ignore-installed blinker flask 2>&1 | tail -3
echo "✅ Flask installed"
echo ""

# 3. Install alpaca (already done, but verify)
echo "Step 3: Verifying alpaca-trade-api..."
python3 -c "import alpaca_trade_api; print('✅ alpaca-trade-api OK')" 2>&1 || {
    pip3 install --break-system-packages --ignore-installed urllib3 alpaca-trade-api 2>&1 | tail -3
}
echo ""

# 4. Stop everything
echo "Step 4: Stopping existing processes..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*dashboard.py" 2>/dev/null
sleep 2
echo "✅ Processes stopped"
echo ""

# 5. Start bot
echo "Step 5: Starting bot..."
screen -dmS trading python3 main.py
sleep 3
if ps aux | grep "python.*main.py" | grep -v grep > /dev/null; then
    echo "✅ Bot started"
else
    echo "❌ Bot failed - check: screen -r trading"
fi
echo ""

# 6. Start dashboard
echo "Step 6: Starting dashboard..."
screen -dmS dashboard python3 dashboard.py
sleep 5
if ps aux | grep "python.*dashboard.py" | grep -v grep > /dev/null; then
    echo "✅ Dashboard started"
    DASHBOARD_IP=$(hostname -I | awk '{print $1}')
    echo "   Access at: http://$DASHBOARD_IP:5000"
else
    echo "❌ Dashboard failed - check: screen -r dashboard"
fi
echo ""

# 7. Test SRE endpoint
echo "Step 7: Testing SRE endpoint..."
sleep 3
curl -s http://localhost:5000/api/sre/health 2>/dev/null | python3 -m json.tool 2>/dev/null | head -15 || {
    echo "⚠️  SRE endpoint not ready yet (wait 10 seconds and try again)"
    echo "   Or check dashboard logs: screen -r dashboard"
}
echo ""

echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "To check status:"
echo "  ps aux | grep python | grep -v grep"
echo ""
echo "To view logs:"
echo "  screen -r trading    # Bot"
echo "  screen -r dashboard  # Dashboard"
echo ""
