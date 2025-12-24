#!/bin/bash
# Verify Deployment - Check all fixes are applied and system is running
# Run on droplet: bash VERIFY_DEPLOYMENT.sh

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING DEPLOYMENT"
echo "=========================================="
echo ""

# 1. Check if fixes are applied
echo "[1] Checking if fixes are applied..."
echo ""

# Check hardcoded path fix
if grep -q "StateFiles.ADAPTIVE_GATE_STATE" signals/uw_adaptive.py 2>/dev/null; then
    echo "  ✅ Hardcoded path fix: Applied (using StateFiles.ADAPTIVE_GATE_STATE)"
else
    echo "  ❌ Hardcoded path fix: NOT applied"
fi

# Check API endpoint fix in uw_flow_daemon.py
if grep -q "APIConfig.UW_BASE_URL" uw_flow_daemon.py 2>/dev/null; then
    echo "  ✅ API endpoint fix (uw_flow_daemon): Applied (using APIConfig.UW_BASE_URL)"
else
    echo "  ❌ API endpoint fix (uw_flow_daemon): NOT applied"
fi

# Check API endpoint fix in main.py
if grep -q "APIConfig.ALPACA_BASE_URL" main.py 2>/dev/null; then
    echo "  ✅ API endpoint fix (main.py): Applied (using APIConfig.ALPACA_BASE_URL)"
else
    echo "  ❌ API endpoint fix (main.py): NOT applied"
fi

# Check missing endpoints
if grep -q "def get_insider" uw_flow_daemon.py 2>/dev/null; then
    echo "  ✅ Missing endpoints: Added (insider, calendar, congress, institutional)"
else
    echo "  ❌ Missing endpoints: NOT added"
fi

# Check polling intervals
if grep -q '"insider":' uw_flow_daemon.py 2>/dev/null; then
    echo "  ✅ Polling intervals: Added for new endpoints"
else
    echo "  ❌ Polling intervals: NOT added"
fi

echo ""

# 2. Run comprehensive audit
echo "[2] Running comprehensive code audit..."
echo ""
python3 COMPREHENSIVE_CODE_AUDIT.py 2>&1 | tail -50
echo ""

# 3. Check service status
echo "[3] Checking service status..."
echo ""
if pgrep -f deploy_supervisor > /dev/null; then
    echo "  ✅ Supervisor: Running (PID: $(pgrep -f deploy_supervisor))"
else
    echo "  ❌ Supervisor: NOT running"
fi

if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "  ✅ UW Daemon: Running (PID: $(pgrep -f 'uw.*daemon|uw_flow_daemon'))"
else
    echo "  ❌ UW Daemon: NOT running"
fi

if pgrep -f "main.py" > /dev/null; then
    echo "  ✅ Trading Bot: Running (PID: $(pgrep -f main.py))"
else
    echo "  ⚠️  Trading Bot: NOT running (may be normal if market is closed)"
fi

if pgrep -f "dashboard.py" > /dev/null; then
    echo "  ✅ Dashboard: Running (PID: $(pgrep -f dashboard.py))"
else
    echo "  ❌ Dashboard: NOT running"
fi

echo ""

# 4. Check recent daemon logs
echo "[4] Recent daemon activity (last 20 lines)..."
echo ""
if [ -f "logs/uw_daemon.log" ]; then
    tail -20 logs/uw_daemon.log | grep -E "Polling|Updated|insider|calendar|congress|institutional|Error|Starting" | tail -10 || tail -5 logs/uw_daemon.log
else
    echo "  ⚠️  No daemon log file found"
fi

echo ""

# 5. Check cache status
echo "[5] Cache status..."
if [ -f "data/uw_flow_cache.json" ]; then
    CACHE_SIZE=$(stat -f%z "data/uw_flow_cache.json" 2>/dev/null || stat -c%s "data/uw_flow_cache.json" 2>/dev/null || echo "0")
    echo "  ✅ Cache file exists ($(numfmt --to=iec-i --suffix=B $CACHE_SIZE 2>/dev/null || echo "${CACHE_SIZE} bytes"))"
    
    # Check for new endpoints in cache
    python3 << 'PYEOF'
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        sample_ticker = [k for k in cache_data.keys() if not k.startswith("_")][0] if cache_data else None
        if sample_ticker:
            ticker_data = cache_data.get(sample_ticker, {})
            if isinstance(ticker_data, str):
                try:
                    ticker_data = json.loads(ticker_data)
                except:
                    ticker_data = {}
            
            endpoints_found = []
            if ticker_data.get("insider"):
                endpoints_found.append("insider")
            if ticker_data.get("calendar"):
                endpoints_found.append("calendar")
            if ticker_data.get("congress"):
                endpoints_found.append("congress")
            if ticker_data.get("institutional"):
                endpoints_found.append("institutional")
            
            if endpoints_found:
                print(f"  ✅ New endpoints in cache: {', '.join(endpoints_found)}")
            else:
                print("  ⚠️  New endpoints not yet in cache (may need time to poll)")
    except Exception as e:
        print(f"  ⚠️  Could not check cache: {e}")
else:
    print("  ⚠️  Cache file not found")
PYEOF
else
    echo "  ⚠️  Cache file not found (daemon may need time to create it)"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "If any fixes show ❌, run: bash APPLY_FIXES_MANUAL.sh"
echo ""
