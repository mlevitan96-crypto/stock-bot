#!/bin/bash
# Setup Dashboard Proxy
# Run this once to set up the proxy that always routes port 5000 to active instance

cd /root/stock-bot
source venv/bin/activate

# Stop any existing dashboard on port 5000
pkill -f "dashboard.py" || true
sleep 2

# Start the proxy
nohup python3 dashboard_proxy.py > logs/proxy.log 2>&1 &
sleep 3

# Verify proxy is running
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Dashboard proxy is running on port 5000"
    echo "Proxy PID: $(pgrep -f dashboard_proxy.py)"
else
    echo "❌ Proxy failed to start. Check logs/proxy.log"
    exit 1
fi
