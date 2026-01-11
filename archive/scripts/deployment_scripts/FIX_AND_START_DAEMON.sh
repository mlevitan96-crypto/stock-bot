#!/bin/bash
# Fix and start daemon properly to create cache

cd ~/stock-bot

echo "=========================================="
echo "FIXING AND STARTING DAEMON"
echo "=========================================="
echo ""

# Step 1: Stop all existing daemons
echo "[1] Stopping all existing daemon processes..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 3

# Verify they're stopped
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "⚠️  Some daemon processes still running - force killing..."
    pkill -9 -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
    sleep 2
fi

if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "❌ Failed to stop daemon processes"
    exit 1
else
    echo "✅ All daemon processes stopped"
fi

# Step 2: Ensure we have latest code
echo ""
echo "[2] Ensuring latest code..."
git pull origin main 2>&1 | head -5

# Step 3: Clear old logs
echo ""
echo "[3] Clearing old logs for fresh start..."
rm -f logs/uw_daemon.log 2>/dev/null
mkdir -p logs data

# Step 4: Verify daemon file exists and is executable
echo ""
echo "[4] Verifying daemon file..."
if [ ! -f "uw_flow_daemon.py" ]; then
    echo "❌ uw_flow_daemon.py not found"
    exit 1
fi

# Check Python syntax
python3 -m py_compile uw_flow_daemon.py 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Python syntax error in uw_flow_daemon.py"
    exit 1
fi
echo "✅ Daemon file is valid"

# Step 5: Start daemon in background
echo ""
echo "[5] Starting daemon..."
source venv/bin/activate
nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon started with PID: $DAEMON_PID"
sleep 3

# Verify it's running
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "✅ Daemon is running"
else
    echo "❌ Daemon failed to start - checking logs..."
    tail -20 logs/uw_daemon.log
    exit 1
fi

# Step 6: Wait for cache to be created
echo ""
echo "[6] Waiting for cache file to be created (60 seconds)..."
for i in {1..12}; do
    sleep 5
    if [ -f "data/uw_flow_cache.json" ]; then
        echo "✅ Cache file created after $((i * 5)) seconds"
        break
    fi
    echo "  Waiting... ($((i * 5))s)"
done

# Step 7: Verify cache was created
echo ""
echo "[7] Verifying cache..."
if [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ Cache file exists"
    CACHE_SIZE=$(wc -c < data/uw_flow_cache.json)
    echo "✅ Cache size: $CACHE_SIZE bytes"
    
    # Check content
    python3 << PYEOF
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
try:
    cache_data = json.loads(cache_file.read_text())
    tickers = [k for k in cache_data.keys() if not k.startswith("_")]
    print(f"✅ Cache has {len(tickers)} tickers")
    
    if tickers:
        sample = tickers[0]
        ticker_data = cache_data.get(sample, {})
        if isinstance(ticker_data, str):
            try:
                ticker_data = json.loads(ticker_data)
            except:
                ticker_data = {}
        
        flow_count = len(ticker_data.get("flow_trades", []))
        print(f"✅ Sample ticker ({sample}): {flow_count} flow trades")
        
        if flow_count > 0:
            print("✅ Cache has trading data - READY")
        else:
            print("⚠️  Cache exists but no flow trades yet")
    else:
        print("⚠️  Cache exists but no tickers yet")
except Exception as e:
    print(f"❌ Error reading cache: {e}")
PYEOF
else
    echo "❌ Cache file still not created after 60 seconds"
    echo ""
    echo "Checking daemon logs for errors..."
    tail -30 logs/uw_daemon.log
    echo ""
    echo "Daemon may need more time or there may be an issue."
    echo "Monitor with: tail -f logs/uw_daemon.log"
fi

echo ""
echo "=========================================="
echo "DAEMON STARTUP COMPLETE"
echo "=========================================="
echo ""
echo "Daemon PID: $DAEMON_PID"
echo "Log file: logs/uw_daemon.log"
echo "Cache file: data/uw_flow_cache.json"
echo ""
echo "Monitor daemon: tail -f logs/uw_daemon.log"
echo "Check cache: cat data/uw_flow_cache.json | python3 -m json.tool | head -50"
