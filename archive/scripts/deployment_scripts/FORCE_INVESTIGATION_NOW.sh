#!/bin/bash
# Force investigation to run immediately and push results
# This script should be run on the droplet

cd ~/stock-bot

echo "=========================================="
echo "FORCING INVESTIGATION TO RUN NOW"
echo "=========================================="
echo ""

# Pull latest code first
echo "Step 1: Pulling latest code..."
git pull origin main --no-rebase 2>&1 | tail -5
echo ""

# Run comprehensive diagnosis
echo "Step 2: Running comprehensive diagnosis..."
if [ -f "comprehensive_no_trades_diagnosis.py" ]; then
    python3 comprehensive_no_trades_diagnosis.py 2>&1
    DIAG_EXIT=$?
else
    echo "⚠ comprehensive_no_trades_diagnosis.py not found, using investigate_no_trades.py"
    python3 investigate_no_trades.py 2>&1
    DIAG_EXIT=$?
fi
echo ""

# Check if results file was created
if [ -f "investigate_no_trades.json" ]; then
    echo "Step 3: Committing and pushing results..."
    touch .last_investigation_run
    git add investigate_no_trades.json .last_investigation_run 2>/dev/null
    git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null
    git push origin main 2>/dev/null
    echo "✓ Results pushed to git"
else
    echo "❌ Investigation file not created (exit code: $DIAG_EXIT)"
    echo "   Check errors above"
    exit 1
fi

echo ""
echo "=========================================="
echo "INVESTIGATION COMPLETE"
echo "=========================================="
