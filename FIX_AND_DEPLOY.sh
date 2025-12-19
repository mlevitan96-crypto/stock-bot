#!/bin/bash
# FIX_AND_DEPLOY.sh - Handles git conflicts FIRST, then deploys

set -e

cd ~/stock-bot

echo "=========================================="
echo "FIXING GIT CONFLICTS AND DEPLOYING"
echo "=========================================="
echo ""

# STEP 1: Fix git conflicts FIRST (before pulling script)
echo "Step 1: Resolving git conflicts..."
echo "----------------------------------------"
# Stash or discard local changes to allow pull
git stash 2>/dev/null || true
git fetch origin main

# Reset to origin/main (accepts all incoming changes)
git reset --hard origin/main 2>/dev/null || {
    # If reset fails, try merge with theirs strategy
    git merge origin/main -X theirs 2>/dev/null || {
        # Last resort: force reset
        git checkout -f main 2>/dev/null || true
        git reset --hard origin/main
    }
}

echo "✅ Git conflicts resolved"
echo ""

# STEP 2: Now pull (should work now)
echo "Step 2: Pulling latest code..."
echo "----------------------------------------"
git pull origin main --no-rebase 2>&1 | tail -3
echo "✅ Code updated"
echo ""

# STEP 3: Setup venv
echo "Step 3: Setting up virtual environment..."
echo "----------------------------------------"
if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate venv"
    exit 1
fi
echo "✅ Virtual environment: $VIRTUAL_ENV"
echo ""

# STEP 4: Install dependencies
echo "Step 4: Installing dependencies..."
echo "----------------------------------------"
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>&1 | tail -3
echo "✅ Dependencies installed"
echo ""

# STEP 5: Stop existing processes
echo "Step 5: Stopping existing processes..."
echo "----------------------------------------"
pkill -f "deploy_supervisor" 2>/dev/null && echo "   Stopped supervisor" || echo "   No supervisor"
pkill -f "python.*main.py" 2>/dev/null && echo "   Stopped bot" || echo "   No bot"
pkill -f "python.*dashboard.py" 2>/dev/null && echo "   Stopped dashboard" || echo "   No dashboard"
sleep 3
echo "✅ Processes stopped"
echo ""

# STEP 6: Verify .env exists and load it
echo "Step 6: Verifying environment setup..."
echo "----------------------------------------"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    # Load .env to pass to supervisor (supervisor will load it again, but this ensures it's there)
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
else
    echo "⚠️  .env file not found - secrets must be in environment variables"
fi
echo ""

# STEP 7: Start deploy_supervisor
echo "Step 7: Starting deploy_supervisor..."
echo "----------------------------------------"
# Note: deploy_supervisor.py uses load_dotenv() which will load .env file
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
sleep 5
echo "✅ Supervisor started"
echo ""

# STEP 8: Check status
echo "Step 8: Final status..."
echo "----------------------------------------"
if ps aux | grep "deploy_supervisor" | grep -v grep > /dev/null; then
    echo "✅ Supervisor running"
else
    echo "❌ Supervisor failed - check: screen -r supervisor"
fi

if ps aux | grep "python.*main.py" | grep -v grep > /dev/null; then
    echo "✅ Trading bot running"
else
    echo "⚠️  Trading bot not running"
fi

if ps aux | grep "python.*dashboard.py" | grep -v grep > /dev/null; then
    echo "✅ Dashboard running"
    IP=$(hostname -I | awk '{print $1}')
    echo "   Access: http://$IP:5000"
else
    echo "⚠️  Dashboard not running"
fi
echo ""

echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "Check logs: screen -r supervisor"
echo ""
