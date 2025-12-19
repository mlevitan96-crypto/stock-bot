#!/bin/bash
# DEPLOY_NOW.sh - Bulletproof deployment script
# Handles git conflicts, uses venv, works with deploy_supervisor

set -e  # Exit on error

cd ~/stock-bot

echo "=========================================="
echo "DEPLOYMENT - HANDLING EVERYTHING"
echo "=========================================="
echo ""

# 1. Handle git conflicts - accept incoming changes
echo "Step 1: Resolving git conflicts..."
echo "----------------------------------------"
# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "Current branch: $CURRENT_BRANCH"

# If not on main, switch (accepting incoming changes)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Switching to main branch (accepting incoming changes)..."
    git fetch origin main
    git reset --hard origin/main
else
    # On main, but may have conflicts - accept incoming
    echo "On main branch, resolving conflicts..."
    git fetch origin main
    # Accept incoming changes for any conflicts
    git reset --hard origin/main 2>/dev/null || {
        # If reset fails, try merge with strategy
        git merge origin/main -X theirs 2>/dev/null || {
            # Last resort: stash and reset
            git stash
            git reset --hard origin/main
        }
    }
fi
echo "✅ Git conflicts resolved"
echo ""

# 2. Setup venv
echo "Step 2: Setting up virtual environment..."
echo "----------------------------------------"
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate venv"
    exit 1
fi
echo "✅ Virtual environment: $VIRTUAL_ENV"
echo ""

# 3. Install dependencies
echo "Step 3: Installing dependencies..."
echo "----------------------------------------"
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>&1 | tail -3
echo "✅ Dependencies installed"
echo ""

# 4. Stop existing processes (deploy_supervisor will restart them)
echo "Step 4: Stopping existing processes..."
echo "----------------------------------------"
pkill -f "deploy_supervisor" 2>/dev/null && echo "   Stopped deploy_supervisor" || echo "   No supervisor found"
pkill -f "python.*main.py" 2>/dev/null && echo "   Stopped main.py" || echo "   No main.py found"
pkill -f "python.*dashboard.py" 2>/dev/null && echo "   Stopped dashboard.py" || echo "   No dashboard.py found"
sleep 3
echo "✅ Processes stopped"
echo ""

# 5. Start deploy_supervisor (it handles everything with graceful fallbacks)
echo "Step 5: Starting deploy_supervisor..."
echo "----------------------------------------"
echo "   (This manages all services with graceful fallbacks)"
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"

sleep 5

# 6. Check status
echo "Step 6: Checking status..."
echo "----------------------------------------"
if ps aux | grep "deploy_supervisor" | grep -v grep > /dev/null; then
    echo "✅ Supervisor running"
else
    echo "❌ Supervisor failed - check: screen -r supervisor"
fi

# Check services
if ps aux | grep "python.*main.py" | grep -v grep > /dev/null; then
    echo "✅ Trading bot running"
else
    echo "⚠️  Trading bot not running (checking logs...)"
    screen -r supervisor -X hardcopy /tmp/supervisor.log 2>/dev/null || true
    tail -20 /tmp/supervisor.log 2>/dev/null || echo "   (Check: screen -r supervisor)"
fi

if ps aux | grep "python.*dashboard.py" | grep -v grep > /dev/null; then
    echo "✅ Dashboard running"
    DASHBOARD_IP=$(hostname -I | awk '{print $1}')
    echo "   Access: http://$DASHBOARD_IP:5000"
else
    echo "⚠️  Dashboard not running"
fi
echo ""

# 7. Test SRE endpoint
echo "Step 7: Testing SRE endpoint..."
echo "----------------------------------------"
sleep 3
curl -s http://localhost:5000/api/sre/health 2>/dev/null | python3 -m json.tool 2>/dev/null | head -5 || {
    echo "⚠️  SRE endpoint not ready (wait 10 seconds)"
}
echo ""

echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "deploy_supervisor is managing everything:"
echo "  - Graceful fallbacks if services fail"
echo "  - Auto-restart on crashes"
echo "  - Non-critical services don't block critical ones"
echo ""
echo "To check status:"
echo "  screen -r supervisor"
echo ""
echo "To view logs:"
echo "  tail -f logs/supervisor.jsonl"
echo ""
