#!/bin/bash
# Monitor UW daemon to verify all 11 endpoints are being fetched

cd ~/stock-bot

echo "=========================================="
echo "UW DAEMON ENDPOINT MONITORING"
echo "=========================================="
echo ""

# Check which processes are running
echo "[1] Checking UW daemon processes..."
UW_PIDS=$(pgrep -f "uw.*daemon|uw_flow_daemon")
if [ -n "$UW_PIDS" ]; then
    echo "✅ UW daemon processes running:"
    ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep
    echo ""
    
    # If multiple, kill the old one
    PIDS_ARRAY=($UW_PIDS)
    if [ ${#PIDS_ARRAY[@]} -gt 1 ]; then
        echo "⚠️  Multiple processes detected - keeping newest, killing older ones..."
        NEWEST_PID=${PIDS_ARRAY[-1]}
        for pid in "${PIDS_ARRAY[@]}"; do
            if [ "$pid" != "$NEWEST_PID" ]; then
                echo "  Killing old process: $pid"
                kill $pid 2>/dev/null
            fi
        done
        sleep 2
        echo "✅ Cleaned up old processes"
        echo ""
    fi
else
    echo "❌ No UW daemon processes found"
    echo ""
fi

# Check recent logs for new endpoints
echo "[2] Checking logs for new endpoint activity..."
if [ -f "logs/uw_daemon.log" ]; then
    echo "Recent endpoint activity (last 50 lines):"
    tail -50 logs/uw_daemon.log | grep -E "market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greek|Updated|Error" | tail -20
    echo ""
else
    echo "⚠️  No log file found yet"
    echo ""
fi

# Check cache for enriched signals
echo "[3] Checking cache for enriched signals..."
python3 << 'PYEOF'
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache_data = json.loads(cache_file.read_text())
    sample_symbol = [k for k in cache_data.keys() if not k.startswith("_")][0] if cache_data else None
    
    if sample_symbol:
        symbol_data = cache_data.get(sample_symbol, {})
        if isinstance(symbol_data, str):
            try:
                symbol_data = json.loads(symbol_data)
            except:
                symbol_data = {}
        
        print(f"Sample symbol: {sample_symbol}")
        print("")
        
        # Check per-ticker enriched signals
        enriched_signals = {
            "greeks": symbol_data.get("greeks", {}),
            "etf_flow": symbol_data.get("etf_flow"),
            "oi_change": symbol_data.get("oi_change"),
            "iv_rank": symbol_data.get("iv_rank"),
            "ftd_pressure": symbol_data.get("ftd_pressure"),
        }
        
        print("Per-ticker enriched signals:")
        for sig, value in enriched_signals.items():
            if value and value not in (None, 0, 0.0, "", [], {}):
                if isinstance(value, dict):
                    print(f"  ✅ {sig}: {len(value)} fields")
                else:
                    print(f"  ✅ {sig}: {value}")
            else:
                print(f"  ❌ {sig}: not found")
        
        print("")
        
        # Check market-wide data
        print("Market-wide data:")
        market_tide = cache_data.get("_market_tide", {})
        if market_tide and market_tide.get("data"):
            last_update = market_tide.get("last_update", 0)
            age_min = (time.time() - last_update) / 60 if last_update else 999
            print(f"  ✅ market_tide: found (age: {age_min:.1f} min)")
        else:
            print(f"  ❌ market_tide: not found")
        
        top_net = cache_data.get("_top_net_impact", {})
        if top_net and top_net.get("data"):
            last_update = top_net.get("last_update", 0)
            age_min = (time.time() - last_update) / 60 if last_update else 999
            print(f"  ✅ top_net_impact: found (age: {age_min:.1f} min)")
        else:
            print(f"  ❌ top_net_impact: not found")
else:
    print("❌ Cache file not found")
PYEOF

echo ""
echo "[4] Next steps:"
echo "  - Wait 5-15 minutes for per-ticker endpoints to poll"
echo "  - Check logs: tail -f logs/uw_daemon.log"
echo "  - Re-run diagnostics: ./COMPREHENSIVE_FIX_ALL_SIGNALS.sh"
echo ""
