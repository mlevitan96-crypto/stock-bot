#!/bin/bash
# Complete workflow: Run investigation, wait for results, analyze, and fix
# This runs on the droplet and does everything

cd ~/stock-bot

echo "=========================================="
echo "COMPLETE INVESTIGATION AND FIX WORKFLOW"
echo "=========================================="
echo ""

# Step 1: Pull latest
echo "Step 1: Pulling latest code..."
git pull origin main --no-rebase 2>&1 | tail -3
echo ""

# Step 2: Run investigation
echo "Step 2: Running investigation..."
chmod +x FORCE_INVESTIGATION_NOW.sh
bash FORCE_INVESTIGATION_NOW.sh
INVEST_EXIT=$?

if [ $INVEST_EXIT -ne 0 ]; then
    echo "❌ Investigation failed - cannot proceed"
    exit 1
fi

echo ""
echo "Step 3: Waiting for results to be pushed..."
sleep 5

echo ""
echo "Step 4: Pulling results back..."
git pull origin main --no-rebase 2>&1 | tail -3

echo ""
echo "=========================================="
echo "INVESTIGATION COMPLETE - Results in investigate_no_trades.json"
echo "=========================================="

