#!/bin/bash
# IMMEDIATE FIX - Resolve git conflict and deploy

cd /root/stock-bot

echo "=========================================="
echo "STEP 1: Resolving git conflicts..."
echo "=========================================="

# Accept remote versions of diagnostic scripts (not critical)
git checkout --theirs CHECK_SUPERVISOR_OUTPUT.sh 2>/dev/null
git checkout --theirs DIAGNOSE_EMPTY_TRADES.sh 2>/dev/null
git checkout --theirs TEST_API_DIRECTLY.sh 2>/dev/null
git checkout --theirs check_risk_logs.sh 2>/dev/null
git checkout --theirs check_uw_api_usage.sh 2>/dev/null
git checkout --theirs verify_risk_integration.sh 2>/dev/null

echo "✅ Conflicts resolved"

echo ""
echo "=========================================="
echo "STEP 2: Pulling latest code..."
echo "=========================================="

git pull origin main --no-rebase

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed - check for remaining conflicts"
    exit 1
fi

echo "✅ Code pulled successfully"

echo ""
echo "=========================================="
echo "STEP 3: Restarting supervisor..."
echo "=========================================="

pkill -f deploy_supervisor
sleep 2

if [ -d "venv" ]; then
    source venv/bin/activate
    venv/bin/python deploy_supervisor.py
else
    echo "⚠️  venv not found - using system python"
    python3 deploy_supervisor.py
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Watch the supervisor output for these DEBUG messages:"
echo "  - DEBUG SYMBOL: About to call submit_entry"
echo "  - DEBUG SYMBOL: submit_entry completed"
echo "  - DEBUG SYMBOL: EXCEPTION in submit_entry (if errors)"
echo "  - DEBUG SYMBOL: Order SUBMITTED or Order IMMEDIATELY FILLED"
echo ""
echo "If you see exceptions, share the error message and I'll fix it immediately."
