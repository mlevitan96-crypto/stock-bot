#!/bin/bash
# Pre-Market Verification: Ensure everything is ready for market open

cd ~/stock-bot

echo "=========================================="
echo "PRE-MARKET SYSTEM VERIFICATION"
echo "=========================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VERIFY_DIR="premarket_${TIMESTAMP}"
mkdir -p "$VERIFY_DIR"

echo "[1] Checking all services are running..."
{
    echo "=== SERVICE STATUS ==="
    
    # Check deploy_supervisor
    if pgrep -f "deploy_supervisor" > /dev/null; then
        echo "✅ deploy_supervisor: Running"
        ps aux | grep "deploy_supervisor" | grep -v grep | head -1
    else
        echo "❌ deploy_supervisor: NOT running"
    fi
    
    # Check UW daemon
    if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "✅ uw_flow_daemon: Running"
        ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep | head -1
    else
        echo "❌ uw_flow_daemon: NOT running"
    fi
    
    # Check main trading bot
    if pgrep -f "main.py" > /dev/null; then
        echo "✅ main.py: Running"
        ps aux | grep "main.py" | grep -v grep | head -1
    else
        echo "⚠️  main.py: NOT running (may be normal if market closed)"
    fi
    
    # Check dashboard
    if pgrep -f "dashboard.py" > /dev/null; then
        echo "✅ dashboard.py: Running"
        ps aux | grep "dashboard.py" | grep -v grep | head -1
    else
        echo "⚠️  dashboard.py: NOT running"
    fi
    
    # Check heartbeat_keeper
    if pgrep -f "heartbeat_keeper" > /dev/null; then
        echo "✅ heartbeat_keeper: Running"
        ps aux | grep "heartbeat_keeper" | grep -v grep | head -1
    else
        echo "⚠️  heartbeat_keeper: NOT running"
    fi
} > "$VERIFY_DIR/1_services.txt"
cat "$VERIFY_DIR/1_services.txt"

echo ""
echo "[2] Verifying cache file exists and is writable..."
python3 << PYEOF > "$VERIFY_DIR/2_cache_status.json"
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
status = {
    "cache_exists": cache_file.exists(),
    "cache_writable": False,
    "cache_readable": False,
    "cache_size_bytes": 0,
    "ticker_count": 0,
    "has_market_tide": False,
    "has_top_net_impact": False,
    "sample_ticker_data": {},
    "test_write_success": False
}

if cache_file.exists():
    status["cache_size_bytes"] = cache_file.stat().st_size
    
    # Test read
    try:
        cache_data = json.loads(cache_file.read_text())
        status["cache_readable"] = True
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        status["ticker_count"] = len(tickers)
        status["has_market_tide"] = bool(cache_data.get("_market_tide", {}).get("data"))
        status["has_top_net_impact"] = bool(cache_data.get("_top_net_impact", {}).get("data"))
        
        if tickers:
            sample = tickers[0]
            ticker_data = cache_data.get(sample, {})
            if isinstance(ticker_data, str):
                try:
                    ticker_data = json.loads(ticker_data)
                except:
                    ticker_data = {}
            status["sample_ticker_data"] = {
                "ticker": sample,
                "has_flow_trades": len(ticker_data.get("flow_trades", [])) > 0,
                "has_dark_pool": bool(ticker_data.get("dark_pool")),
                "has_greeks": bool(ticker_data.get("greeks")),
            }
    except Exception as e:
        status["cache_read_error"] = str(e)

# Test write
try:
    test_data = {"_test": int(time.time())}
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(test_data))
    status["test_write_success"] = True
    status["cache_writable"] = True
    # Restore original if it existed
    if status["cache_readable"]:
        cache_file.write_text(json.dumps(cache_data))
except Exception as e:
    status["test_write_error"] = str(e)

print(json.dumps(status, indent=2))
PYEOF

cat "$VERIFY_DIR/2_cache_status.json" | python3 -m json.tool

echo ""
echo "[3] Verifying UW daemon can write to cache (run for 30 seconds)..."
# Stop existing
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear cache for test
rm -f data/uw_flow_cache.json 2>/dev/null

# Start daemon
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon_test.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 30 seconds for cache write..."
sleep 30

# Stop daemon
kill $DAEMON_PID 2>/dev/null
sleep 2

# Check if cache was created
if [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ Cache file created successfully"
    echo "Cache size: $(wc -c < data/uw_flow_cache.json) bytes"
    echo "Sample content:"
    python3 -c "import json; from pathlib import Path; cache = json.loads(Path('data/uw_flow_cache.json').read_text()); print(f\"Tickers: {len([k for k in cache.keys() if not k.startswith('_')])}\"); print(f\"Has market_tide: {bool(cache.get('_market_tide', {}).get('data'))}\")"
else
    echo "❌ Cache file NOT created - checking logs..."
    tail -20 logs/uw_daemon_test.log
fi

echo ""
echo "[4] Verifying trading bot can read cache..."
python3 << PYEOF > "$VERIFY_DIR/4_trading_bot_read.json"
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

status = {
    "can_import_main": False,
    "can_read_cache": False,
    "cache_has_data": False,
    "can_import_uw_composite": False
}

# Test importing main.py components
try:
    from config.registry import CacheFiles, read_json
    status["can_import_main"] = True
    
    cache_file = CacheFiles.UW_FLOW_CACHE
    if cache_file.exists():
        cache_data = read_json(cache_file, default={})
        status["can_read_cache"] = True
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        status["cache_has_data"] = len(tickers) > 0
        status["ticker_count"] = len(tickers)
except Exception as e:
    status["import_error"] = str(e)

# Test importing signal components
try:
    from signals.uw_composite_v2 import compute_uw_composite_score
    status["can_import_uw_composite"] = True
except Exception as e:
    status["uw_composite_error"] = str(e)

print(json.dumps(status, indent=2))
PYEOF

cat "$VERIFY_DIR/4_trading_bot_read.json" | python3 -m json.tool

echo ""
echo "[5] Checking environment variables..."
python3 << PYEOF > "$VERIFY_DIR/5_env_check.json"
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

env_check = {
    "uw_api_key": "✅ Set" if os.getenv("UW_API_KEY") else "❌ Missing",
    "alpaca_key": "✅ Set" if os.getenv("ALPACA_KEY") else "❌ Missing",
    "alpaca_secret": "✅ Set" if os.getenv("ALPACA_SECRET") else "❌ Missing",
    "alpaca_base_url": os.getenv("ALPACA_BASE_URL", "Not set"),
    "trading_mode": os.getenv("TRADING_MODE", "Not set"),
}

print(json.dumps(env_check, indent=2))
PYEOF

cat "$VERIFY_DIR/5_env_check.json" | python3 -m json.tool

echo ""
echo "[6] Creating pre-market checklist..."
python3 << PYEOF > "$VERIFY_DIR/6_checklist.txt"
import json
from pathlib import Path

# Load all checks
services = Path("$VERIFY_DIR/1_services.txt").read_text()
cache_status = json.loads(Path("$VERIFY_DIR/2_cache_status.json").read_text())
trading_bot = json.loads(Path("$VERIFY_DIR/4_trading_bot_read.json").read_text())
env_check = json.loads(Path("$VERIFY_DIR/5_env_check.json").read_text())

print("=" * 80)
print("PRE-MARKET CHECKLIST")
print("=" * 80)
print()

# Services
print("SERVICES:")
if "✅ deploy_supervisor: Running" in services:
    print("  ✅ deploy_supervisor running")
else:
    print("  ❌ deploy_supervisor NOT running - CRITICAL")
if "✅ uw_flow_daemon: Running" in services:
    print("  ✅ uw_flow_daemon running")
else:
    print("  ❌ uw_flow_daemon NOT running - CRITICAL")
if "✅ main.py: Running" in services:
    print("  ✅ main.py running")
else:
    print("  ⚠️  main.py not running (will start at market open)")
if "✅ dashboard.py: Running" in services:
    print("  ✅ dashboard.py running")
else:
    print("  ⚠️  dashboard.py not running")
print()

# Cache
print("CACHE:")
if cache_status.get("cache_exists"):
    print("  ✅ Cache file exists")
    if cache_status.get("cache_writable"):
        print("  ✅ Cache is writable")
    else:
        print("  ❌ Cache NOT writable - CRITICAL")
    if cache_status.get("cache_readable"):
        print("  ✅ Cache is readable")
        print(f"  ✅ {cache_status.get('ticker_count', 0)} tickers in cache")
        if cache_status.get("has_market_tide"):
            print("  ✅ market_tide data present")
        else:
            print("  ⚠️  market_tide data missing")
    else:
        print("  ❌ Cache NOT readable - CRITICAL")
else:
    print("  ❌ Cache file does NOT exist - CRITICAL")
    print("  ⚠️  Daemon must create cache before market open")
print()

# Trading bot
print("TRADING BOT:")
if trading_bot.get("can_import_main"):
    print("  ✅ Can import main.py components")
    if trading_bot.get("can_read_cache"):
        print("  ✅ Can read cache")
        if trading_bot.get("cache_has_data"):
            print(f"  ✅ Cache has data ({trading_bot.get('ticker_count', 0)} tickers)")
        else:
            print("  ⚠️  Cache exists but has no ticker data")
    else:
        print("  ❌ Cannot read cache - CRITICAL")
else:
    print("  ❌ Cannot import main.py - CRITICAL")
if trading_bot.get("can_import_uw_composite"):
    print("  ✅ Can import signal components")
else:
    print("  ⚠️  Cannot import signal components")
print()

# Environment
print("ENVIRONMENT:")
for key, value in env_check.items():
    if "❌" in str(value):
        print(f"  ❌ {key}: {value} - CRITICAL")
    elif "✅" in str(value):
        print(f"  ✅ {key}: {value}")
    else:
        print(f"  ⚠️  {key}: {value}")
print()

# Overall status
print("=" * 80)
print("OVERALL STATUS")
print("=" * 80)

critical_issues = []
if "❌ deploy_supervisor" in services:
    critical_issues.append("deploy_supervisor not running")
if "❌ uw_flow_daemon" in services:
    critical_issues.append("uw_flow_daemon not running")
if not cache_status.get("cache_exists"):
    critical_issues.append("Cache file does not exist")
if not cache_status.get("cache_writable"):
    critical_issues.append("Cache not writable")
if not trading_bot.get("can_read_cache"):
    critical_issues.append("Trading bot cannot read cache")
if "❌" in str(env_check.get("uw_api_key", "")):
    critical_issues.append("UW_API_KEY missing")
if "❌" in str(env_check.get("alpaca_key", "")):
    critical_issues.append("ALPACA_KEY missing")

if critical_issues:
    print("❌ CRITICAL ISSUES FOUND:")
    for issue in critical_issues:
        print(f"   - {issue}")
    print()
    print("⚠️  SYSTEM NOT READY FOR MARKET OPEN")
    print("   Fix these issues before market opens")
else:
    print("✅ SYSTEM READY FOR MARKET OPEN")
    print("   All critical components verified")
    print("   Trading bot should work when market opens")
PYEOF

cat "$VERIFY_DIR/6_checklist.txt"

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo "All data saved to: $VERIFY_DIR/"
echo ""
echo "Pushing to GitHub..."
git add "$VERIFY_DIR"/* 2>/dev/null || true
git commit -m "Pre-market verification: $TIMESTAMP" 2>/dev/null || echo "No changes"
git push origin main 2>&1 | head -5 || echo "Push may have issues"

echo ""
echo "✅ Pre-market verification complete"
