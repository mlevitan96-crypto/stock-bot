#!/bin/bash
# Quick script to check recent risk management activity

echo "=== Recent Risk Management Events (last 20 lines) ==="
grep -i "risk_management" logs/*.log 2>/dev/null | tail -20

echo ""
echo "=== Risk Freeze Events ==="
grep -i "freeze" logs/*.log 2>/dev/null | grep -i "risk\|daily_loss\|drawdown\|equity_floor" | tail -10

echo ""
echo "=== Current Risk State Files ==="
if [ -f "state/governor_freezes.json" ]; then
    echo "Freeze state:"
    cat state/governor_freezes.json | python3 -m json.tool 2>/dev/null || cat state/governor_freezes.json
else
    echo "No freeze state file (good - no freezes active)"
fi

echo ""
if [ -f "state/daily_start_equity.json" ]; then
    echo "Daily start equity:"
    cat state/daily_start_equity.json | python3 -m json.tool 2>/dev/null || cat state/daily_start_equity.json
else
    echo "No daily start equity file (will be created on first run)"
fi

echo ""
if [ -f "state/peak_equity.json" ]; then
    echo "Peak equity:"
    cat state/peak_equity.json | python3 -m json.tool 2>/dev/null || cat state/peak_equity.json
else
    echo "No peak equity file (will be created on first run)"
fi
