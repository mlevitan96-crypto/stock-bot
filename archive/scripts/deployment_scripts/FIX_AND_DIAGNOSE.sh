#!/bin/bash
# Fix git conflicts and run trading diagnostic

echo "=================================================================================="
echo "FIXING GIT AND RUNNING TRADING DIAGNOSTIC"
echo "=================================================================================="

cd ~/stock-bot

# 1. Stash local changes
echo ""
echo "1. Stashing local changes..."
git stash

# 2. Pull latest
echo ""
echo "2. Pulling latest code..."
git pull origin main

# 3. Run diagnostic
echo ""
echo "3. Running trading diagnostic..."
echo ""
python3 diagnose_trading_issues.py

echo ""
echo "=================================================================================="
echo "DIAGNOSTIC COMPLETE"
echo "=================================================================================="
