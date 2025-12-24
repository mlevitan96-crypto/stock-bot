#!/bin/bash
# Restart UW daemon with the bug fix for new endpoints

cd ~/stock-bot

echo "=========================================="
echo "RESTARTING UW DAEMON WITH FIXES"
echo "=========================================="
echo ""

# Pull latest code
echo "[1] Pulling latest code..."
git pull origin main
echo ""

# Stop existing daemon
echo "[2] Stopping existing UW daemon..."
pkill -f "uw.*daemon|uw_flow_daemon"
sleep 3

# Verify stopped
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "⚠️  Some processes still running, force killing..."
    pkill -9 -f "uw.*daemon|uw_flow_daemon"
    sleep 2
fi

# Start with fixes
echo "[3] Starting UW daemon with fixes..."
source venv/bin/activate
nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &

# Wait for startup
sleep 3

# Verify it's running
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "✅ UW daemon started successfully"
    echo ""
    echo "Process info:"
    ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep
    echo ""
    echo "Recent logs (last 20 lines):"
    tail -20 logs/uw_daemon.log
    echo ""
    echo "[4] Next steps:"
    echo "  - Monitor logs: tail -f logs/uw_daemon.log"
    echo "  - Wait 5-15 minutes for endpoints to poll"
    echo "  - Run: ./MONITOR_UW_DAEMON_ENDPOINTS.sh"
else
    echo "❌ Failed to start UW daemon"
    echo ""
    echo "Error logs:"
    tail -50 logs/uw_daemon.log
    exit 1
fi
