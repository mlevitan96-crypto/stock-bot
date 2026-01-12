#!/bin/bash
# Deploy Dashboard Fixes to Droplet
# Run this script from your local machine with SSH access to the droplet

set -e

echo "============================================================"
echo "DASHBOARD FIXES DEPLOYMENT TO DROPLET"
echo "============================================================"
echo ""

# Deploy target (use "alpaca" alias or direct IP)
DEPLOY_TARGET="${1:-alpaca}"
PROJECT_DIR="/root/stock-bot"

echo "[1/5] Pulling latest code from GitHub..."
ssh $DEPLOY_TARGET "cd $PROJECT_DIR && git fetch origin main && git reset --hard origin/main"
echo "✅ Code pulled successfully"
echo ""

echo "[2/5] Verifying latest commit..."
COMMIT=$(ssh $DEPLOY_TARGET "cd $PROJECT_DIR && git log -1 --oneline")
echo "✅ Current commit: $COMMIT"
echo ""

echo "[3/5] Checking dashboard status..."
DASHBOARD_STATUS=$(ssh $DEPLOY_TARGET "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1" || echo "")
if [ -n "$DASHBOARD_STATUS" ]; then
    echo "✅ Dashboard is running"
    echo "   $DASHBOARD_STATUS"
else
    echo "ℹ️  Dashboard process not found (may be under systemd/supervisor)"
fi
echo ""

echo "[4/5] Restarting dashboard..."
# Try killing dashboard first (supervisor will restart)
ssh $DEPLOY_TARGET "pkill -f 'python.*dashboard.py' || true"
echo "   Waiting 5 seconds for restart..."
sleep 5

# Also try systemd restart
ssh $DEPLOY_TARGET "systemctl restart trading-bot.service || true"
sleep 3
echo "✅ Dashboard restart initiated"
echo ""

echo "[5/5] Verifying dashboard is responding..."
HEALTH=$(ssh $DEPLOY_TARGET "curl -s http://localhost:5000/health 2>&1 | head -5" || echo "")
if echo "$HEALTH" | grep -q "healthy\|status"; then
    echo "✅ Dashboard is responding"
    echo "   $HEALTH"
else
    echo "⚠️  Dashboard health check had issues"
    echo "   $HEALTH"
fi
echo ""

echo "============================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "Verify dashboard is accessible:"
echo "   http://104.236.102.57:5000/"
echo ""
echo "Test endpoints:"
echo "   http://104.236.102.57:5000/health"
echo "   http://104.236.102.57:5000/api/positions"
echo "   http://104.236.102.57:5000/api/health_status"
echo ""
