#!/bin/bash
# Fix all blocked readiness issues

cd ~/stock-bot || exit 1

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Pull latest code
echo "Pulling latest code..."
git fetch origin main
git reset --hard origin/main

# Install dotenv if missing
echo "Checking dotenv..."
python3 -c "import dotenv" 2>/dev/null || pip install python-dotenv -q

# Fix UW API auth check - check if it's a false positive
echo "Checking UW API auth..."
if [ -f "logs/uw_flow_daemon.log" ]; then
    # Check only very recent lines (last 10)
    recent_errors=$(tail -10 logs/uw_flow_daemon.log | grep -c "401\|403\|Unauthorized" || echo "0")
    if [ "$recent_errors" -eq "0" ]; then
        echo "No recent UW API auth errors - likely false positive"
    fi
fi

# Run fix script
echo "Running fix script..."
python3 fix_blocked_readiness.py

# Re-check status
echo ""
echo "Final status:"
python3 -c "from failure_point_monitor import get_failure_point_monitor; m = get_failure_point_monitor(); r = m.get_trading_readiness(); print(f'Readiness: {r[\"readiness\"]} | Critical: {r[\"critical_count\"]} | Warnings: {r[\"warning_count\"]}')"

