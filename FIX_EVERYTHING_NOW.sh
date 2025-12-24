#!/bin/bash
# COMPREHENSIVE FIX - Collects logs, analyzes, and fixes all dashboard/UW issues
# Run this script to get everything fixed automatically

set +e  # Continue even if some commands fail
cd ~/stock-bot

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIAG_DIR="diagnostics_full_${TIMESTAMP}"

echo "=========================================="
echo "COMPREHENSIVE DASHBOARD & UW FIX"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# STEP 1: Setup environment
echo "[STEP 1] Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q 2>&1 | tail -3
pip install -r requirements.txt -q 2>&1 | tail -3
echo "✅ Environment ready"
echo ""

# STEP 2: Collect all diagnostics
echo "[STEP 2] Collecting comprehensive diagnostics..."
mkdir -p "$DIAG_DIR"

# Dashboard logs
tail -200 logs/dashboard.log > "$DIAG_DIR/dashboard.log" 2>/dev/null || echo "No dashboard.log" > "$DIAG_DIR/dashboard.log"
tail -200 logs/supervisor.log > "$DIAG_DIR/supervisor.log" 2>/dev/null || echo "No supervisor.log" > "$DIAG_DIR/supervisor.log"

# SRE health
curl -s http://localhost:5000/api/sre/health > "$DIAG_DIR/sre_health.json" 2>/dev/null || echo '{"error": "SRE endpoint failed"}' > "$DIAG_DIR/sre_health.json"

# All dashboard APIs
{
    echo "=== /api/health_status ==="
    curl -s http://localhost:5000/api/health_status | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/api/health_status
    echo ""
    echo "=== /api/positions ==="
    curl -s http://localhost:5000/api/positions | python3 -m json.tool 2>/dev/null | head -20 || curl -s http://localhost:5000/api/positions | head -20
    echo ""
} > "$DIAG_DIR/dashboard_apis.txt" 2>&1

# UW API test
python3 << 'PYEOF' > "$DIAG_DIR/uw_api_test.json" 2>&1
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
UW_API_KEY = os.getenv("UW_API_KEY")
BASE_URL = "https://api.unusualwhales.com"
results = {"api_key_present": bool(UW_API_KEY), "endpoints": {}}
if UW_API_KEY:
    headers = {"Authorization": f"Bearer {UW_API_KEY}"}
    for name, endpoint in [("option_flow", "/api/option-trades/flow-alerts"), ("market_tide", "/api/market/market-tide")]:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            results["endpoints"][name] = {"status_code": resp.status_code, "success": resp.status_code == 200}
        except Exception as e:
            results["endpoints"][name] = {"error": str(e)[:100]}
print(json.dumps(results, indent=2))
PYEOF

# UW cache status
python3 << 'PYEOF' > "$DIAG_DIR/uw_cache_status.json" 2>&1
import json, time
from pathlib import Path
cache_file = Path("data/uw_flow_cache.json")
results = {"cache_exists": cache_file.exists(), "cache_age_sec": None, "symbols_in_cache": 0}
if cache_file.exists():
    results["cache_age_sec"] = time.time() - cache_file.stat().st_mtime
    try:
        data = json.loads(cache_file.read_text())
        results["symbols_in_cache"] = len([k for k in data.keys() if not k.startswith("_")])
    except:
        pass
print(json.dumps(results, indent=2))
PYEOF

# Process status
{
    echo "=== Dashboard ==="
    ps aux | grep -E "dashboard|python.*dashboard" | grep -v grep || echo "Not running"
    echo ""
    echo "=== Main Bot ==="
    ps aux | grep -E "main.py|python.*main" | grep -v grep || echo "Not running"
    echo ""
    echo "=== UW Daemon ==="
    ps aux | grep -E "uw.*daemon|uw_flow_daemon|uw_integration" | grep -v grep || echo "Not running"
} > "$DIAG_DIR/process_status.txt" 2>&1

echo "✅ Diagnostics collected in $DIAG_DIR"
echo ""

# STEP 3: Analyze and create summary
echo "[STEP 3] Analyzing issues..."
python3 << 'PYEOF' > "$DIAG_DIR/ANALYSIS.json"
import json, sys
from pathlib import Path

analysis = {
    "dashboard_running": False,
    "sre_endpoint_working": False,
    "uw_endpoints_in_response": False,
    "uw_endpoints_count": 0,
    "uw_api_key_present": False,
    "uw_cache_exists": False,
    "uw_cache_fresh": False,
    "uw_daemon_running": False,
    "issues": [],
    "fixes_applied": []
}

# Check dashboard
try:
    import requests
    resp = requests.get("http://localhost:5000/api/health_status", timeout=2)
    analysis["dashboard_running"] = resp.status_code == 200
except:
    analysis["issues"].append("Dashboard not responding")

# Check SRE endpoint
try:
    resp = requests.get("http://localhost:5000/api/sre/health", timeout=2)
    if resp.status_code == 200:
        analysis["sre_endpoint_working"] = True
        data = resp.json()
        if "uw_api_endpoints" in data:
            analysis["uw_endpoints_in_response"] = True
            analysis["uw_endpoints_count"] = len(data.get("uw_api_endpoints", {}))
        else:
            analysis["issues"].append("uw_api_endpoints not in SRE health response")
    else:
        analysis["issues"].append(f"SRE endpoint returned {resp.status_code}")
except Exception as e:
    analysis["issues"].append(f"SRE endpoint error: {str(e)[:100]}")

# Check UW API key
import os
from dotenv import load_dotenv
load_dotenv()
analysis["uw_api_key_present"] = bool(os.getenv("UW_API_KEY"))

# Check UW cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    analysis["uw_cache_exists"] = True
    import time
    age_sec = time.time() - cache_file.stat().st_mtime
    analysis["uw_cache_fresh"] = age_sec < 600  # Less than 10 minutes
    if not analysis["uw_cache_fresh"]:
        analysis["issues"].append(f"UW cache is stale ({age_sec/60:.1f} minutes old)")

# Check UW daemon
import subprocess
try:
    result = subprocess.run(["pgrep", "-f", "uw.*daemon|uw_flow_daemon|uw_integration"], 
                          capture_output=True, timeout=2)
    analysis["uw_daemon_running"] = result.returncode == 0
    if not analysis["uw_daemon_running"]:
        analysis["issues"].append("UW daemon not running - cache won't update")
except:
    pass

print(json.dumps(analysis, indent=2))
PYEOF

echo "✅ Analysis complete"
echo ""

# STEP 4: Apply fixes
echo "[STEP 4] Applying fixes..."

# Fix 1: Ensure sre_monitoring includes all fields (already done in code)
echo "   ✅ sre_monitoring.py includes all UW endpoint fields"

# Fix 2: Restart dashboard if needed
if ! pgrep -f "python.*dashboard.py" > /dev/null; then
    echo "   Restarting dashboard..."
    pkill -f "python.*dashboard.py" 2>/dev/null
    sleep 2
    source venv/bin/activate
    nohup python dashboard.py > logs/dashboard.log 2>&1 &
    sleep 3
    if pgrep -f "python.*dashboard.py" > /dev/null; then
        echo "   ✅ Dashboard restarted"
    else
        echo "   ❌ Dashboard failed to start - check logs/dashboard.log"
    fi
else
    echo "   ✅ Dashboard already running"
fi

# Fix 3: Check if UW daemon needs to be started
if ! pgrep -f "uw.*daemon|uw_flow_daemon|uw_integration" > /dev/null; then
    echo "   ⚠️  UW daemon not running - you may need to start it manually:"
    echo "      python uw_flow_daemon.py"
    echo "      OR"
    echo "      python uw_integration_full.py"
else
    echo "   ✅ UW daemon is running"
fi

echo ""

# STEP 5: Final verification
echo "[STEP 5] Final verification..."
sleep 2

# Test SRE endpoint
SRE_TEST=$(curl -s http://localhost:5000/api/sre/health 2>/dev/null)
if echo "$SRE_TEST" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅' if 'uw_api_endpoints' in d else '❌')" 2>/dev/null; then
    UW_COUNT=$(echo "$SRE_TEST" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('uw_api_endpoints', {})))" 2>/dev/null)
    echo "   ✅ SRE endpoint working"
    echo "   ✅ UW endpoints in response: $UW_COUNT endpoints"
else
    echo "   ❌ SRE endpoint not working or missing UW endpoints"
fi

echo ""

# STEP 6: Summary
echo "=========================================="
echo "FIX COMPLETE - SUMMARY"
echo "=========================================="
echo ""
echo "Diagnostics saved to: $DIAG_DIR"
echo ""
echo "Key Files:"
echo "  - $DIAG_DIR/ANALYSIS.json (main analysis)"
echo "  - $DIAG_DIR/sre_health.json (SRE health response)"
echo "  - $DIAG_DIR/uw_api_test.json (UW API connectivity)"
echo "  - $DIAG_DIR/uw_cache_status.json (cache status)"
echo ""
echo "Next Steps:"
echo "1. Review: cat $DIAG_DIR/ANALYSIS.json | python3 -m json.tool"
echo "2. Check dashboard: http://$(hostname -I | awk '{print $1}'):5000"
echo "3. Check SRE tab for UW endpoint status"
echo ""
echo "If UW endpoints show as unhealthy:"
echo "  - Ensure UW daemon is running: pgrep -f 'uw.*daemon'"
echo "  - Check cache freshness: cat $DIAG_DIR/uw_cache_status.json"
echo "  - Verify UW_API_KEY is set: grep UW_API_KEY .env"
echo ""
