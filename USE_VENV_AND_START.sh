#!/bin/bash
# Use virtual environment and start with deploy_supervisor (has graceful fallbacks)

cd ~/stock-bot

echo "=========================================="
echo "ENVIRONMENT SETUP WITH GRACEFUL FALLBACKS"
echo "=========================================="
echo ""

# 1. Handle git
echo "Step 1: Updating code..."
git stash 2>/dev/null
git checkout main 2>/dev/null || true
git pull origin main 2>/dev/null || true
echo "✅ Code updated"
echo ""

# 2. Setup/activate venv
echo "Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "   Creating venv..."
    python3 -m venv venv
fi

echo "   Activating venv..."
source venv/bin/activate

# Verify we're in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate venv"
    exit 1
fi
echo "✅ Virtual environment active: $VIRTUAL_ENV"
echo ""

# 3. Install dependencies in venv
echo "Step 3: Installing dependencies in venv..."
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>&1 | tail -5
echo "✅ Dependencies installed"
echo ""

# 4. Stop existing processes
echo "Step 4: Stopping existing processes..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*dashboard.py" 2>/dev/null
pkill -f "deploy_supervisor" 2>/dev/null
sleep 2
echo "✅ Processes stopped"
echo ""

# 5. Start with deploy_supervisor (has graceful fallbacks)
echo "Step 5: Starting with deploy_supervisor.py..."
echo "   (This has graceful fallbacks - non-critical services can fail)"
echo ""
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"

sleep 5

# 6. Check status
echo "Step 6: Checking status..."
if ps aux | grep "deploy_supervisor" | grep -v grep > /dev/null; then
    echo "✅ Supervisor started"
else
    echo "❌ Supervisor failed - check: screen -r supervisor"
fi

# Check individual services
if ps aux | grep "python.*main.py" | grep -v grep > /dev/null; then
    echo "✅ Trading bot running"
else
    echo "⚠️  Trading bot not running (may be waiting for secrets)"
fi

if ps aux | grep "python.*dashboard.py" | grep -v grep > /dev/null; then
    echo "✅ Dashboard running"
    DASHBOARD_IP=$(hostname -I | awk '{print $1}')
    echo "   Access at: http://$DASHBOARD_IP:5000"
else
    echo "⚠️  Dashboard not running"
fi
echo ""

# 7. Test SRE endpoint
echo "Step 7: Testing SRE endpoint..."
sleep 3
curl -s http://localhost:5000/api/sre/health 2>/dev/null | python3 -m json.tool 2>/dev/null | head -10 || {
    echo "⚠️  SRE endpoint not ready (wait 10 seconds)"
}
echo ""

echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "The deploy_supervisor has graceful fallbacks:"
echo "  - Dashboard can fail without stopping bot"
echo "  - Services skip if secrets missing"
echo "  - Non-critical services don't block critical ones"
echo ""
echo "To check logs:"
echo "  screen -r supervisor"
echo ""
echo "To manually activate venv later:"
echo "  source venv/bin/activate"
echo ""
