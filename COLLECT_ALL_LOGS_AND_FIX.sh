#!/bin/bash
# Comprehensive Log Collection and Dashboard Fix Script
# Collects ALL logs, analyzes issues, and provides fixes

set +e  # Continue even if commands fail

cd ~/stock-bot
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIAG_DIR="diagnostics_full_${TIMESTAMP}"
mkdir -p "$DIAG_DIR"

echo "=========================================="
echo "COMPREHENSIVE LOG COLLECTION & ANALYSIS"
echo "=========================================="
echo ""

# 1. Collect all dashboard logs
echo "[1] Collecting dashboard logs..."
tail -200 logs/dashboard.log > "$DIAG_DIR/dashboard.log" 2>/dev/null || echo "No dashboard.log" > "$DIAG_DIR/dashboard.log"
tail -200 logs/supervisor.log > "$DIAG_DIR/supervisor.log" 2>/dev/null || echo "No supervisor.log" > "$DIAG_DIR/supervisor.log"

# 2. Collect all SRE monitoring data
echo "[2] Collecting SRE monitoring data..."
curl -s http://localhost:5000/api/sre/health > "$DIAG_DIR/sre_health.json" 2>/dev/null || echo '{"error": "SRE endpoint failed"}' > "$DIAG_DIR/sre_health.json"
python3 -m json.tool "$DIAG_DIR/sre_health.json" > "$DIAG_DIR/sre_health_formatted.json" 2>/dev/null || cp "$DIAG_DIR/sre_health.json" "$DIAG_DIR/sre_health_formatted.json"

# 3. Collect all dashboard API endpoints
echo "[3] Testing all dashboard API endpoints..."
{
    echo "=== /api/health_status ==="
    curl -s http://localhost:5000/api/health_status | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/api/health_status
    echo ""
    echo "=== /api/positions ==="
    curl -s http://localhost:5000/api/positions | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/api/positions
    echo ""
    echo "=== /api/closed_positions ==="
    curl -s http://localhost:5000/api/closed_positions | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/api/closed_positions
    echo ""
    echo "=== /api/executive_summary ==="
    curl -s http://localhost:5000/api/executive_summary | python3 -m json.tool 2>/dev/null | head -50 || curl -s http://localhost:5000/api/executive_summary | head -50
    echo ""
} > "$DIAG_DIR/dashboard_apis.txt" 2>&1

# 4. Collect UW API connectivity test
echo "[4] Testing UW API connectivity..."
python3 << 'PYEOF' > "$DIAG_DIR/uw_api_test.json" 2>&1
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
UW_API_KEY = os.getenv("UW_API_KEY")
BASE_URL = "https://api.unusualwhales.com"

results = {
    "api_key_present": bool(UW_API_KEY),
    "base_url": BASE_URL,
    "endpoints": {}
}

if not UW_API_KEY:
    results["error"] = "UW_API_KEY not found in environment"
    print(json.dumps(results, indent=2))
    sys.exit(0)

headers = {"Authorization": f"Bearer {UW_API_KEY}"}
test_symbol = "AAPL"

# Test all endpoints from config
endpoints_to_test = [
    ("option_flow", "/api/option-trades/flow-alerts"),
    ("dark_pool", f"/api/darkpool/{test_symbol}"),
    ("greeks", f"/api/stock/{test_symbol}/greeks"),
    ("net_impact", "/api/market/top-net-impact"),
    ("market_tide", "/api/market/market-tide"),
    ("greek_exposure", f"/api/stock/{test_symbol}/greek-exposure"),
    ("oi_change", f"/api/stock/{test_symbol}/oi-change"),
    ("etf_flow", f"/api/etfs/{test_symbol}/in-outflow"),
    ("iv_rank", f"/api/stock/{test_symbol}/iv-rank"),
    ("shorts_ftds", f"/api/shorts/{test_symbol}/ftds"),
    ("max_pain", f"/api/stock/{test_symbol}/max-pain"),
]

for name, endpoint in endpoints_to_test:
    try:
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, headers=headers, timeout=5)
        results["endpoints"][name] = {
            "endpoint": endpoint,
            "status_code": resp.status_code,
            "success": resp.status_code == 200,
            "response_size": len(resp.text),
            "error": None
        }
        if resp.status_code != 200:
            try:
                error_data = resp.json()
                results["endpoints"][name]["error"] = str(error_data).replace(UW_API_KEY, "***REDACTED***")[:200]
            except:
                results["endpoints"][name]["error"] = resp.text[:200]
    except Exception as e:
        results["endpoints"][name] = {
            "endpoint": endpoint,
            "status_code": None,
            "success": False,
            "error": str(e)
        }

print(json.dumps(results, indent=2))
PYEOF

# 5. Collect UW cache status
echo "[5] Checking UW cache status..."
python3 << 'PYEOF' > "$DIAG_DIR/uw_cache_status.json" 2>&1
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
results = {
    "cache_exists": cache_file.exists(),
    "cache_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
    "cache_age_sec": None,
    "symbols_in_cache": 0,
    "sample_symbols": [],
    "cache_structure": {}
}

if cache_file.exists():
    try:
        import time
        results["cache_age_sec"] = time.time() - cache_file.stat().st_mtime
        data = json.loads(cache_file.read_text())
        results["symbols_in_cache"] = len([k for k in data.keys() if not k.startswith("_")])
        results["sample_symbols"] = [k for k in data.keys() if not k.startswith("_")][:10]
        
        # Check structure of first symbol
        if results["sample_symbols"]:
            first_symbol = results["sample_symbols"][0]
            symbol_data = data.get(first_symbol, {})
            if isinstance(symbol_data, str):
                try:
                    symbol_data = json.loads(symbol_data)
                except:
                    pass
            results["cache_structure"] = {
                "sample_symbol": first_symbol,
                "keys": list(symbol_data.keys()) if isinstance(symbol_data, dict) else "not_dict"
            }
    except Exception as e:
        results["error"] = str(e)

print(json.dumps(results, indent=2))
PYEOF

# 6. Collect process status
echo "[6] Collecting process status..."
{
    echo "=== Dashboard Process ==="
    ps aux | grep -E "dashboard|python.*dashboard" | grep -v grep
    echo ""
    echo "=== Main Bot Process ==="
    ps aux | grep -E "main.py|python.*main" | grep -v grep
    echo ""
    echo "=== Supervisor Process ==="
    ps aux | grep -E "deploy_supervisor|supervisor" | grep -v grep
    echo ""
    echo "=== Port 5000 ==="
    lsof -i :5000 2>/dev/null || netstat -tlnp | grep 5000 || echo "Port 5000 is free"
    echo ""
} > "$DIAG_DIR/process_status.txt" 2>&1

# 7. Collect heartbeat files
echo "[7] Collecting heartbeat files..."
{
    echo "=== bot_heartbeat.json ==="
    cat state/bot_heartbeat.json 2>/dev/null | python3 -m json.tool 2>/dev/null || cat state/bot_heartbeat.json 2>/dev/null || echo "File not found"
    echo ""
    echo "=== doctor_state.json ==="
    cat state/doctor_state.json 2>/dev/null | python3 -m json.tool 2>/dev/null || cat state/doctor_state.json 2>/dev/null || echo "File not found"
    echo ""
} > "$DIAG_DIR/heartbeats.txt" 2>&1

# 8. Collect recent orders
echo "[8] Collecting recent orders..."
tail -50 data/live_orders.jsonl 2>/dev/null > "$DIAG_DIR/recent_orders.jsonl" || echo "No orders file" > "$DIAG_DIR/recent_orders.jsonl"

# 9. Check Python environment
echo "[9] Checking Python environment..."
{
    echo "=== Python Version ==="
    python3 --version
    echo ""
    echo "=== Flask Installation ==="
    python3 -c "import flask; print(f'Flask {flask.__version__}')" 2>&1 || echo "Flask not installed"
    echo ""
    echo "=== Virtual Environment ==="
    if [ -d "venv" ]; then
        echo "venv exists"
        source venv/bin/activate 2>/dev/null
        python -c "import flask; print(f'Flask in venv: {flask.__version__}')" 2>&1 || echo "Flask not in venv"
    else
        echo "venv does not exist"
    fi
    echo ""
} > "$DIAG_DIR/python_env.txt" 2>&1

# 10. Check sre_monitoring module
echo "[10] Checking sre_monitoring module..."
python3 << 'PYEOF' > "$DIAG_DIR/sre_module_check.json" 2>&1
import json
import sys

results = {
    "module_importable": False,
    "get_sre_health_callable": False,
    "SREMonitoringEngine_importable": False,
    "error": None
}

try:
    from sre_monitoring import get_sre_health, SREMonitoringEngine
    results["module_importable"] = True
    results["get_sre_health_callable"] = callable(get_sre_health)
    results["SREMonitoringEngine_importable"] = True
    
    # Try to call it
    try:
        health = get_sre_health()
        results["get_sre_health_success"] = True
        results["health_keys"] = list(health.keys()) if isinstance(health, dict) else "not_dict"
    except Exception as e:
        results["get_sre_health_error"] = str(e)
except ImportError as e:
    results["error"] = f"Import error: {str(e)}"
except Exception as e:
    results["error"] = f"Other error: {str(e)}"

print(json.dumps(results, indent=2))
PYEOF

# 11. Create summary
echo "[11] Creating summary..."
python3 << 'PYEOF' > "$DIAG_DIR/SUMMARY.json"
import json
import sys
from pathlib import Path

summary = {
    "timestamp": "$TIMESTAMP",
    "dashboard_running": False,
    "dashboard_port_5000": False,
    "sre_endpoint_working": False,
    "uw_api_key_present": False,
    "uw_endpoints_working": 0,
    "uw_endpoints_total": 0,
    "issues": [],
    "recommendations": []
}

# Check dashboard
try:
    import requests
    resp = requests.get("http://localhost:5000/api/health_status", timeout=2)
    summary["dashboard_running"] = resp.status_code == 200
except:
    summary["issues"].append("Dashboard not responding on port 5000")

# Check SRE endpoint
try:
    resp = requests.get("http://localhost:5000/api/sre/health", timeout=2)
    if resp.status_code == 200:
        summary["sre_endpoint_working"] = True
        data = resp.json()
        if "uw_api_endpoints" in data:
            apis = data["uw_api_endpoints"]
            summary["uw_endpoints_total"] = len(apis)
            summary["uw_endpoints_working"] = sum(1 for h in apis.values() if h.get("status") == "healthy")
except Exception as e:
    summary["issues"].append(f"SRE endpoint error: {str(e)}")

# Check UW API key
import os
from dotenv import load_dotenv
load_dotenv()
summary["uw_api_key_present"] = bool(os.getenv("UW_API_KEY"))

# Read UW API test results
uw_test_file = Path("$DIAG_DIR/uw_api_test.json")
if uw_test_file.exists():
    try:
        uw_test = json.loads(uw_test_file.read_text())
        summary["uw_api_key_present"] = uw_test.get("api_key_present", False)
        endpoints = uw_test.get("endpoints", {})
        summary["uw_endpoints_total"] = len(endpoints)
        summary["uw_endpoints_working"] = sum(1 for e in endpoints.values() if e.get("success", False))
        
        for name, result in endpoints.items():
            if not result.get("success", False):
                summary["issues"].append(f"UW endpoint {name} failed: {result.get('error', 'unknown')}")
    except:
        pass

# Recommendations
if not summary["dashboard_running"]:
    summary["recommendations"].append("Restart dashboard: source venv/bin/activate && python dashboard.py")
if not summary["sre_endpoint_working"]:
    summary["recommendations"].append("Check sre_monitoring.py module and /api/sre/health endpoint")
if summary["uw_endpoints_working"] < summary["uw_endpoints_total"]:
    summary["recommendations"].append(f"Fix UW API endpoints: {summary['uw_endpoints_working']}/{summary['uw_endpoints_total']} working")
if not summary["uw_api_key_present"]:
    summary["recommendations"].append("Set UW_API_KEY in .env file")

print(json.dumps(summary, indent=2))
PYEOF

echo ""
echo "=========================================="
echo "COLLECTION COMPLETE"
echo "=========================================="
echo ""
echo "All logs collected in: $DIAG_DIR"
echo ""
echo "Summary:"
cat "$DIAG_DIR/SUMMARY.json" | python3 -m json.tool 2>/dev/null || cat "$DIAG_DIR/SUMMARY.json"
echo ""
echo "Next: Review $DIAG_DIR/SUMMARY.json for issues"
echo ""
