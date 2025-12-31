#!/bin/bash
# Verify all files are present on droplet
cd ~/stock-bot

echo "Checking for new files..."
ls -la momentum_ignition_filter.py analyze_today_vs_backtest.py shadow_analysis_blocked_trades.py 2>&1

echo ""
echo "Checking main.py for momentum_ignition integration..."
grep -c "momentum_ignition" main.py 2>&1 || echo "0"

echo ""
echo "Checking main.py for profit_taking acceleration..."
grep -c "profit_acceleration\|profit_taking" main.py 2>&1 || echo "0"

echo ""
echo "Git status:"
git log --oneline -3
