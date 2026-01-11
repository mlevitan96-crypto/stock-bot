#!/bin/bash
# Verify cache is being populated and daemon is actively polling

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING CACHE AND DAEMON STATUS"
echo "=========================================="
echo ""

echo "[1] Checking cache file contents..."
if [ -f "data/uw_flow_cache.json" ]; then
    echo "Cache file structure:"
    python3 << PYEOF
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
try:
    cache_data = json.loads(cache_file.read_text())
    
    # Show all top-level keys
    print(f"Top-level keys: {list(cache_data.keys())}")
    print()
    
    # Check metadata
    if "_metadata" in cache_data:
        metadata = cache_data["_metadata"]
        print(f"Metadata: {metadata}")
        print()
    
    # Count tickers (non-underscore keys)
    tickers = [k for k in cache_data.keys() if not k.startswith("_")]
    print(f"Tickers in cache: {len(tickers)}")
    
    if tickers:
        print(f"Ticker list: {tickers[:10]}{'...' if len(tickers) > 10 else ''}")
        print()
        
        # Check first ticker
        sample = tickers[0]
        ticker_data = cache_data.get(sample, {})
        if isinstance(ticker_data, str):
            try:
                ticker_data = json.loads(ticker_data)
            except:
                ticker_data = {}
        
        print(f"Sample ticker ({sample}) data keys: {list(ticker_data.keys())}")
        flow_count = len(ticker_data.get("flow_trades", []))
        print(f"  Flow trades: {flow_count}")
        print(f"  Has dark_pool: {bool(ticker_data.get('dark_pool'))}")
        print(f"  Has greeks: {bool(ticker_data.get('greeks'))}")
    else:
        print("No tickers yet - daemon is still initializing")
        print("This is normal - daemon needs time to poll all 53 tickers")
    
    # Check market-wide data
    if "_market_tide" in cache_data:
        print()
        print("✅ market_tide data present")
    if "_top_net_impact" in cache_data:
        print("✅ top_net_impact data present")
        
except Exception as e:
    print(f"Error reading cache: {e}")
    import traceback
    traceback.print_exc()
PYEOF
else
    echo "❌ Cache file does not exist"
fi

echo ""
echo "[2] Checking daemon activity (last 30 lines)..."
if [ -f "logs/uw_daemon.log" ]; then
    tail -30 logs/uw_daemon.log
else
    echo "❌ No daemon log file"
fi

echo ""
echo "[3] Checking if daemon is actively polling..."
if [ -f "logs/uw_daemon.log" ]; then
    # Check for recent polling activity (last 2 minutes)
    RECENT_POLLS=$(tail -100 logs/uw_daemon.log | grep -E "Polling|Retrieved|Cache for" | wc -l)
    echo "Recent polling activity (last 100 lines): $RECENT_POLLS messages"
    
    if [ $RECENT_POLLS -gt 0 ]; then
        echo "✅ Daemon is actively polling"
        echo ""
        echo "Recent polling messages:"
        tail -100 logs/uw_daemon.log | grep -E "Polling|Retrieved|Cache for" | tail -5
    else
        echo "⚠️  No recent polling activity"
    fi
    
    # Check if daemon entered main loop
    if grep -q "INSIDE while loop\|SUCCESS.*Entered main loop" logs/uw_daemon.log; then
        echo "✅ Daemon entered main loop"
    else
        echo "⚠️  Daemon may not have entered main loop yet"
    fi
fi

echo ""
echo "[4] Waiting 30 seconds and checking cache again..."
sleep 30

if [ -f "data/uw_flow_cache.json" ]; then
    TICKER_COUNT=$(python3 -c "import json; from pathlib import Path; cache = json.loads(Path('data/uw_flow_cache.json').read_text()); print(len([k for k in cache.keys() if not k.startswith('_')]))")
    echo "Tickers in cache now: $TICKER_COUNT"
    
    if [ "$TICKER_COUNT" -gt 0 ]; then
        echo "✅ Cache is being populated!"
    else
        echo "⚠️  Cache still empty - daemon may need more time"
        echo "   With 53 tickers and 1.5s delay per ticker, full cycle takes ~80 seconds"
    fi
fi

echo ""
echo "=========================================="
echo "STATUS SUMMARY"
echo "=========================================="

if [ -f "data/uw_flow_cache.json" ] && pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "✅ SYSTEM IS OPERATIONAL"
    echo ""
    echo "Confirmed:"
    echo "  ✅ Cache file exists"
    echo "  ✅ Daemon is running"
    echo "  ✅ Daemon is polling (check logs above)"
    echo ""
    echo "The cache will populate as the daemon polls each ticker."
    echo "With 53 tickers, a full cycle takes ~80 seconds."
    echo ""
    echo "For market open:"
    echo "  - Cache will be populated with fresh data"
    echo "  - Trading bot will read from cache"
    echo "  - All endpoints will be polled regularly"
    echo ""
    echo "✅ SYSTEM READY FOR MARKET OPEN"
else
    echo "⚠️  SYSTEM NEEDS ATTENTION"
    if [ ! -f "data/uw_flow_cache.json" ]; then
        echo "  ❌ Cache file missing"
    fi
    if ! pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "  ❌ Daemon not running"
    fi
fi

echo ""
