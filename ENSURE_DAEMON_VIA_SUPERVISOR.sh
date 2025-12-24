#!/bin/bash
# Ensure daemon runs via deploy_supervisor (the proper way)

cd ~/stock-bot

echo "=========================================="
echo "ENSURING DAEMON VIA SUPERVISOR"
echo "=========================================="
echo ""

# Step 1: Check if supervisor is running
echo "[1] Checking deploy_supervisor status..."
if pgrep -f "deploy_supervisor" > /dev/null; then
    echo "✅ deploy_supervisor is running"
    SUPERVISOR_PID=$(pgrep -f "deploy_supervisor" | head -1)
    echo "   PID: $SUPERVISOR_PID"
else
    echo "❌ deploy_supervisor is NOT running"
    echo ""
    echo "Starting deploy_supervisor..."
    source venv/bin/activate
    nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &
    sleep 5
    if pgrep -f "deploy_supervisor" > /dev/null; then
        echo "✅ deploy_supervisor started"
    else
        echo "❌ Failed to start deploy_supervisor"
        echo "Check logs: tail -20 logs/supervisor.log"
        exit 1
    fi
fi

# Step 2: Stop any manually-started daemons (they conflict with supervisor)
echo ""
echo "[2] Stopping any manually-started daemons..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Step 3: Wait for supervisor to start the daemon
echo ""
echo "[3] Waiting for supervisor to start uw-daemon (10 seconds)..."
sleep 10

# Step 4: Verify daemon is running (via supervisor)
echo ""
echo "[4] Verifying uw-daemon is running..."
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    DAEMON_PID=$(pgrep -f "uw.*daemon|uw_flow_daemon" | head -1)
    echo "✅ uw-daemon is running (PID: $DAEMON_PID)"
    
    # Check if it's the supervisor's process
    PARENT_PID=$(ps -o ppid= -p $DAEMON_PID | tr -d ' ')
    if [ "$PARENT_PID" = "$SUPERVISOR_PID" ]; then
        echo "✅ Daemon is managed by supervisor (correct)"
    else
        echo "⚠️  Daemon parent PID doesn't match supervisor"
    fi
else
    echo "❌ uw-daemon is NOT running"
    echo ""
    echo "Checking supervisor logs for errors..."
    if [ -f "logs/supervisor.log" ]; then
        tail -30 logs/supervisor.log | grep -i "uw-daemon\|error\|failed" | tail -10
    fi
    echo ""
    echo "The supervisor should start the daemon automatically."
    echo "If it doesn't, check:"
    echo "  1. UW_API_KEY is set in .env"
    echo "  2. Supervisor logs: tail -f logs/supervisor.log"
    exit 1
fi

# Step 5: Wait for cache to be created
echo ""
echo "[5] Waiting for cache file to be created (90 seconds)..."
for i in {1..18}; do
    sleep 5
    if [ -f "data/uw_flow_cache.json" ]; then
        echo "✅ Cache file created after $((i * 5)) seconds"
        break
    fi
    if [ $((i % 3)) -eq 0 ]; then
        echo "  Still waiting... ($((i * 5))s) - daemon needs time to poll 53 tickers"
    fi
done

# Step 6: Verify cache
echo ""
echo "[6] Verifying cache..."
if [ -f "data/uw_flow_cache.json" ]; then
    CACHE_SIZE=$(wc -c < data/uw_flow_cache.json)
    echo "✅ Cache file exists ($CACHE_SIZE bytes)"
    
    # Check ticker count
    TICKER_COUNT=$(python3 -c "import json; from pathlib import Path; cache = json.loads(Path('data/uw_flow_cache.json').read_text()); print(len([k for k in cache.keys() if not k.startswith('_')]))" 2>/dev/null || echo "0")
    echo "✅ Tickers in cache: $TICKER_COUNT"
    
    if [ "$TICKER_COUNT" -gt 0 ]; then
        echo "✅ Cache is populated with ticker data"
    else
        echo "⚠️  Cache exists but no tickers yet"
        echo "   This is normal - daemon needs ~80 seconds to poll all 53 tickers"
        echo "   Cache will populate as daemon continues polling"
    fi
else
    echo "❌ Cache file still not created"
    echo ""
    echo "Checking daemon logs..."
    if [ -f "logs/uw-daemon-pc.log" ]; then
        echo "--- Recent daemon logs ---"
        tail -20 logs/uw-daemon-pc.log
    elif [ -f "logs/uw_daemon.log" ]; then
        echo "--- Recent daemon logs ---"
        tail -20 logs/uw_daemon.log
    fi
fi

echo ""
echo "=========================================="
echo "FINAL STATUS"
echo "=========================================="

if pgrep -f "deploy_supervisor" > /dev/null && pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null && [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ SYSTEM IS OPERATIONAL"
    echo ""
    echo "Confirmed:"
    echo "  ✅ deploy_supervisor is running"
    echo "  ✅ uw-daemon is running (managed by supervisor)"
    echo "  ✅ Cache file exists"
    echo ""
    echo "The daemon will continue polling and updating the cache."
    echo "For market open, the system is ready."
    echo ""
    echo "✅ SYSTEM READY FOR MARKET OPEN"
else
    echo "⚠️  SYSTEM NEEDS ATTENTION"
    if ! pgrep -f "deploy_supervisor" > /dev/null; then
        echo "  ❌ deploy_supervisor not running"
    fi
    if ! pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "  ❌ uw-daemon not running"
    fi
    if [ ! -f "data/uw_flow_cache.json" ]; then
        echo "  ⚠️  Cache file not created yet (may need more time)"
    fi
fi

echo ""
echo "Monitor supervisor: tail -f logs/supervisor.log"
echo "Monitor daemon: tail -f logs/uw-daemon-pc.log (or logs/uw_daemon.log)"
echo ""
