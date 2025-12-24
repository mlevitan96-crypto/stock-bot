#!/bin/bash
# Fully automated investigation - runs on droplet, commits to git, Cursor reads results
# This script does EVERYTHING - no copy/paste needed

cd ~/stock-bot

echo "=========================================="
echo "AUTOMATED INVESTIGATION: No Trades Today"
echo "=========================================="
echo ""

# Step 1: Pull latest code (get investigation script)
echo "Step 1: Pulling latest code..."
git pull origin main --no-rebase || true

# Step 2: Make scripts executable
echo "Step 2: Setting permissions..."
chmod +x investigate_no_trades.py run_investigation.sh 2>/dev/null || true

# Step 3: Run investigation
echo "Step 3: Running comprehensive investigation..."
python3 investigate_no_trades.py

# Step 4: Commit and push results
echo ""
echo "Step 4: Committing results to git..."
git add investigate_no_trades.json 2>/dev/null || true
git commit -m "Investigation: No trades today - $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

echo ""
echo "=========================================="
echo "✅ INVESTIGATION COMPLETE"
echo "=========================================="
echo ""
echo "Results saved to: investigate_no_trades.json"
echo "Committed and pushed to git"
echo "Cursor can now read the results!"
echo ""

