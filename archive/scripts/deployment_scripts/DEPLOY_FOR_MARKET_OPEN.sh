#!/bin/bash
# DEPLOY FOR MARKET OPEN - RUN THIS NOW

cd ~/stock-bot

echo "=========================================="
echo "DEPLOYING FOR MARKET OPEN"
echo "=========================================="
echo ""

# Pull latest
git pull origin main

# Verify syntax
echo "[1] Verifying syntax..."
if ! python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "❌ CRITICAL: Syntax errors!"
    exit 1
fi
echo "✅ Syntax OK"

# Stop everything
echo ""
echo "[2] Stopping all services..."
pkill -f "deploy_supervisor|uw.*daemon|uw_flow_daemon|main.py|dashboard.py|heartbeat_keeper" 2>/dev/null
sleep 5

# Start supervisor
echo ""
echo "[3] Starting supervisor..."
source venv/bin/activate
nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &
SUPERVISOR_PID=$!

echo "Supervisor PID: $SUPERVISOR_PID"
echo "Waiting 10 seconds for services to start..."
sleep 10

# Verify services
echo ""
echo "[4] Verifying services..."
SERVICES_OK=true

if ! pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "❌ UW daemon not running"
    SERVICES_OK=false
else
    echo "✅ UW daemon running"
fi

if ! pgrep -f "main.py" > /dev/null; then
    echo "❌ Trading bot not running"
    SERVICES_OK=false
else
    echo "✅ Trading bot running"
fi

if ! pgrep -f "dashboard.py" > /dev/null; then
    echo "❌ Dashboard not running"
    SERVICES_OK=false
else
    echo "✅ Dashboard running"
fi

# Check daemon logs
echo ""
echo "[5] Checking daemon status..."
sleep 5
if [ -f "logs/uw_daemon.log" ]; then
    if grep -q "LOOP ENTERED\|Polling\|Retrieved" logs/uw_daemon.log; then
        echo "✅ Daemon is working"
    else
        echo "⚠️  Daemon started but no activity yet (may be normal)"
        tail -10 logs/uw_daemon.log
    fi
fi

# Final status
echo ""
echo "=========================================="
if [ "$SERVICES_OK" = true ]; then
    echo "✅ SYSTEM READY FOR MARKET OPEN"
    echo ""
    echo "All services running. Monitor with:"
    echo "  tail -f logs/supervisor.log"
    echo "  tail -f logs/uw_daemon.log"
    echo ""
    echo "Dashboard: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "⚠️  SOME SERVICES NOT RUNNING"
    echo "Check logs: logs/supervisor.log"
fi
echo "=========================================="
