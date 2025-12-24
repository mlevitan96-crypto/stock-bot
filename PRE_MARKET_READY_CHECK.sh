#!/bin/bash
# Pre-Market Ready Check: Comprehensive verification for market open

cd ~/stock-bot

echo "=========================================="
echo "PRE-MARKET READY CHECK"
echo "=========================================="
echo ""

# Step 1: Ensure daemon is running continuously
echo "[1] Ensuring UW daemon is running..."
if ! pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "⚠️  Daemon not running - starting it..."
    source venv/bin/activate
    nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
    sleep 3
    if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "✅ Daemon started"
    else
        echo "❌ Failed to start daemon"
    fi
else
    echo "✅ Daemon already running"
fi

# Step 2: Wait for cache to be created (give it time)
echo ""
echo "[2] Waiting for cache file to be created (30 seconds)..."
sleep 30

# Step 3: Verify cache exists and has data
echo ""
echo "[3] Verifying cache status..."
python3 << PYEOF
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
print(f"Cache file exists: {cache_file.exists()}")

if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        print(f"✅ Cache has {len(tickers)} tickers")
        print(f"✅ Cache size: {cache_file.stat().st_size} bytes")
        
        # Check for market-wide data
        if cache_data.get("_market_tide", {}).get("data"):
            print("✅ market_tide data present")
        else:
            print("⚠️  market_tide data missing (will be polled during market hours)")
        
        # Check sample ticker
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
                print("⚠️  Cache exists but no flow trades yet (will populate during market hours)")
        else:
            print("⚠️  Cache exists but no tickers yet")
    except Exception as e:
        print(f"❌ Error reading cache: {e}")
else:
    print("❌ Cache file does not exist")
    print("⚠️  Daemon may need more time to create cache")
    print("   Check logs: tail -f logs/uw_daemon.log")
PYEOF

# Step 4: Verify trading bot can read cache
echo ""
echo "[4] Verifying trading bot can read cache..."
python3 << PYEOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from config.registry import CacheFiles, read_json
    
    cache_file = CacheFiles.UW_FLOW_CACHE
    if cache_file.exists():
        cache_data = read_json(cache_file, default={})
        print("✅ Trading bot can read cache")
        print(f"✅ Cache contains {len([k for k in cache_data.keys() if not k.startswith('_')])} tickers")
    else:
        print("⚠️  Cache file not found (will be created by daemon)")
except Exception as e:
    print(f"❌ Error: {e}")
PYEOF

# Step 5: Check all services
echo ""
echo "[5] Service status:"
echo "  deploy_supervisor: $(pgrep -f 'deploy_supervisor' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  uw_flow_daemon: $(pgrep -f 'uw.*daemon|uw_flow_daemon' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  heartbeat_keeper: $(pgrep -f 'heartbeat_keeper' > /dev/null && echo '✅ Running' || echo '⚠️  Not running')"
echo "  dashboard: $(pgrep -f 'dashboard.py' > /dev/null && echo '✅ Running' || echo '⚠️  Not running')"

# Step 6: Final summary
echo ""
echo "=========================================="
echo "PRE-MARKET STATUS"
echo "=========================================="

if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null && [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ SYSTEM READY FOR MARKET OPEN"
    echo ""
    echo "Confirmed:"
    echo "  ✅ UW daemon is running"
    echo "  ✅ Cache file exists"
    echo "  ✅ Trading bot can read cache"
    echo ""
    echo "The system will:"
    echo "  1. Continue polling UW API during market hours"
    echo "  2. Update cache with fresh data"
    echo "  3. Trading bot will read from cache for signals"
    echo "  4. Execute trades based on signals"
else
    echo "⚠️  SYSTEM NEEDS ATTENTION"
    echo ""
    if ! pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "  ❌ UW daemon not running - start it with:"
        echo "     nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &"
    fi
    if [ ! -f "data/uw_flow_cache.json" ]; then
        echo "  ⚠️  Cache file not created yet - daemon may need more time"
        echo "     Monitor: tail -f logs/uw_daemon.log"
    fi
fi

echo ""
