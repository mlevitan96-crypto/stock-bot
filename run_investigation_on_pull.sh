#!/bin/bash
# This script runs automatically when pulled from git
# It triggers an investigation immediately

cd ~/stock-bot

echo "=========================================="
echo "RUNNING INVESTIGATION (Triggered by Git Pull)"
echo "=========================================="
echo ""

# Run investigation (ALWAYS use comprehensive version first - it has the fixes)
# Use comprehensive version which works around registry issues
if [ -f "comprehensive_no_trades_diagnosis.py" ]; then
    echo "Running comprehensive diagnosis (has all fixes)..."
    python3 comprehensive_no_trades_diagnosis.py 2>&1
    INVEST_EXIT=$?
    if [ $INVEST_EXIT -ne 0 ]; then
        echo "WARNING: Comprehensive diagnosis failed, trying original..."
        python3 investigate_no_trades.py 2>&1
    fi
else
    echo "WARNING: comprehensive_no_trades_diagnosis.py not found, using original..."
    python3 investigate_no_trades.py 2>&1
fi

# Commit and push results
if [ -f "investigate_no_trades.json" ]; then
    touch .last_investigation_run
    git add investigate_no_trades.json .last_investigation_run 2>/dev/null
    git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
    echo "✓ Investigation results pushed to git"
else
    echo "⚠ Investigation file not created - check for errors above"
fi
