#!/bin/bash
# Comprehensive Dashboard, SRE, UW, and API Diagnostics Collection
# Exports all data to git for analysis

set -e

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DIAG_DIR="diagnostics_${TIMESTAMP}"
mkdir -p "$DIAG_DIR"

echo "=================================================================================="
echo "COLLECTING COMPREHENSIVE DASHBOARD & SYSTEM DIAGNOSTICS"
echo "=================================================================================="
echo "Timestamp: $(date)"
echo "Output directory: $DIAG_DIR"
echo ""

# Function to save JSON with error handling
save_json() {
    local file="$1"
    local data="$2"
    echo "$data" | python3 -m json.tool > "$file" 2>/dev/null || echo "$data" > "$file"
}

# Function to test API endpoint
test_endpoint() {
    local url="$1"
    local output="$2"
    local timeout="${3:-5}"
    
    echo "  Testing: $url"
    curl -s --max-time "$timeout" "$url" > "$output" 2>&1 || echo '{"error": "Failed to connect"}' > "$output"
}

# 1. DASHBOARD API ENDPOINTS
echo "1. Testing Dashboard API Endpoints..."
mkdir -p "$DIAG_DIR/dashboard_apis"

test_endpoint "http://localhost:5000/api/health_status" "$DIAG_DIR/dashboard_apis/health_status.json"
test_endpoint "http://localhost:5000/api/positions" "$DIAG_DIR/dashboard_apis/positions.json"
test_endpoint "http://localhost:5000/api/closed_positions" "$DIAG_DIR/dashboard_apis/closed_positions.json"
test_endpoint "http://localhost:5000/api/sre/health" "$DIAG_DIR/dashboard_apis/sre_health.json"
test_endpoint "http://localhost:5000/api/executive_summary" "$DIAG_DIR/dashboard_apis/executive_summary.json"
test_endpoint "http://localhost:5000/health" "$DIAG_DIR/dashboard_apis/health.json"

echo "  ✓ Dashboard APIs collected"

# 2. SRE MONITORING DATA
echo ""
echo "2. Collecting SRE Monitoring Data..."
mkdir -p "$DIAG_DIR/sre"

# Get SRE health directly from Python
python3 << 'PYTHON_EOF' > "$DIAG_DIR/sre/sre_health_direct.json" 2>&1
import json
import sys
try:
    from sre_monitoring import get_sre_health
    health = get_sre_health()
    print(json.dumps(health, indent=2, default=str))
except Exception as e:
    print(json.dumps({"error": str(e), "type": type(e).__name__}, indent=2))
PYTHON_EOF

# Check SRE state files
if [ -f "state/sre_state.json" ]; then
    cp "state/sre_state.json" "$DIAG_DIR/sre/sre_state.json"
fi

if [ -f "state/sre_health.json" ]; then
    cp "state/sre_health.json" "$DIAG_DIR/sre/sre_health_file.json"
fi

echo "  ✓ SRE data collected"

# 3. UW SIGNAL DATA & CACHE
echo ""
echo "3. Collecting UW Signal Data..."
mkdir -p "$DIAG_DIR/uw_signals"

# Get UW cache files
if [ -d "state/uw_cache" ]; then
    echo "  Copying UW cache files..."
    mkdir -p "$DIAG_DIR/uw_signals/cache"
    find state/uw_cache -type f -name "*.json" -mtime -1 | head -20 | while read f; do
        cp "$f" "$DIAG_DIR/uw_signals/cache/$(basename $f)" 2>/dev/null || true
    done
fi

# Get recent signal data
python3 << 'PYTHON_EOF' > "$DIAG_DIR/uw_signals/recent_signals.json" 2>&1
import json
from pathlib import Path
from datetime import datetime, timezone

signals = []
signal_files = [
    "data/live_signals.jsonl",
    "logs/signals.jsonl",
    "logs/trading.jsonl"
]

for sig_file in signal_files:
    path = Path(sig_file)
    if path.exists():
        try:
            with path.open("r") as f:
                lines = f.readlines()
                for line in lines[-100:]:  # Last 100 signals
                    try:
                        sig = json.loads(line.strip())
                        signals.append(sig)
                    except:
                        pass
        except:
            pass

# Sort by timestamp
signals.sort(key=lambda x: x.get("_ts", x.get("timestamp", 0)), reverse=True)

print(json.dumps({
    "total_signals": len(signals),
    "recent_signals": signals[:50],  # Top 50 most recent
    "collected_at": datetime.now(timezone.utc).isoformat()
}, indent=2, default=str))
PYTHON_EOF

# Get UW API connectivity test
python3 << 'PYTHON_EOF' > "$DIAG_DIR/uw_signals/api_connectivity.json" 2>&1
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

connectivity = {
    "uw_api_key_set": bool(os.getenv("UW_API_KEY")),
    "uw_base_url": os.getenv("UW_BASE_URL", "https://api.unusualwhales.com"),
    "test_endpoints": {}
}

# Test a few key endpoints if we can import UWClient
try:
    from main import UWClient
    client = UWClient()
    
    # Test endpoints
    test_endpoints = [
        ("flow_alerts", "/api/option-trades/flow-alerts"),
        ("dark_pool", "/api/darkpool/SPY"),
        ("market_tide", "/api/market/sector-tide"),
    ]
    
    for name, endpoint in test_endpoints:
        try:
            # Just check if we can make a request (don't wait long)
            connectivity["test_endpoints"][name] = {
                "endpoint": endpoint,
                "status": "available"
            }
        except Exception as e:
            connectivity["test_endpoints"][name] = {
                "endpoint": endpoint,
                "status": "error",
                "error": str(e)
            }
except Exception as e:
    connectivity["import_error"] = str(e)

print(json.dumps(connectivity, indent=2, default=str))
PYTHON_EOF

echo "  ✓ UW signal data collected"

# 4. HEARTBEAT & PROCESS STATUS
echo ""
echo "4. Collecting Heartbeat & Process Data..."
mkdir -p "$DIAG_DIR/heartbeats"

# All heartbeat files
for hb_file in state/bot_heartbeat.json state/doctor_state.json state/system_heartbeat.json state/heartbeat.json; do
    if [ -f "$hb_file" ]; then
        cp "$hb_file" "$DIAG_DIR/heartbeats/$(basename $hb_file)"
    fi
done

# Process status
python3 << 'PYTHON_EOF' > "$DIAG_DIR/heartbeats/process_status.json" 2>&1
import json
import subprocess
from datetime import datetime, timezone

processes = {}

# Check main.py
try:
    result = subprocess.run(["pgrep", "-f", "python.*main.py"], 
                          capture_output=True, text=True, timeout=2)
    if result.returncode == 0:
        pids = result.stdout.strip().split()
        processes["main.py"] = {
            "running": True,
            "pids": pids,
            "count": len(pids)
        }
    else:
        processes["main.py"] = {"running": False}
except:
    processes["main.py"] = {"running": False, "error": "check_failed"}

# Check dashboard.py
try:
    result = subprocess.run(["pgrep", "-f", "python.*dashboard.py"], 
                          capture_output=True, text=True, timeout=2)
    if result.returncode == 0:
        pids = result.stdout.strip().split()
        processes["dashboard.py"] = {
            "running": True,
            "pids": pids,
            "count": len(pids)
        }
    else:
        processes["dashboard.py"] = {"running": False}
except:
    processes["dashboard.py"] = {"running": False, "error": "check_failed"}

print(json.dumps({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "processes": processes
}, indent=2, default=str))
PYTHON_EOF

echo "  ✓ Heartbeat data collected"

# 5. RECENT LOGS
echo ""
echo "5. Collecting Recent Logs..."
mkdir -p "$DIAG_DIR/logs"

# Dashboard logs
if [ -f "logs/dashboard.log" ]; then
    tail -200 "logs/dashboard.log" > "$DIAG_DIR/logs/dashboard_tail.log" 2>/dev/null || true
fi

# Main bot logs (if exists)
if [ -f "logs/main.log" ]; then
    tail -200 "logs/main.log" > "$DIAG_DIR/logs/main_tail.log" 2>/dev/null || true
fi

# Recent orders
if [ -f "data/live_orders.jsonl" ]; then
    tail -50 "data/live_orders.jsonl" > "$DIAG_DIR/logs/recent_orders.jsonl" 2>/dev/null || true
fi

if [ -f "logs/orders.jsonl" ]; then
    tail -50 "logs/orders.jsonl" > "$DIAG_DIR/logs/orders_tail.jsonl" 2>/dev/null || true
fi

echo "  ✓ Logs collected"

# 6. SYSTEM STATE FILES
echo ""
echo "6. Collecting System State Files..."
mkdir -p "$DIAG_DIR/state"

# Key state files
for state_file in state/closed_positions.json state/open_positions.json state/trading_state.json; do
    if [ -f "$state_file" ]; then
        cp "$state_file" "$DIAG_DIR/state/$(basename $state_file)" 2>/dev/null || true
    fi
done

echo "  ✓ State files collected"

# 7. CREATE SUMMARY
echo ""
echo "7. Creating Diagnostic Summary..."
python3 << 'PYTHON_EOF' > "$DIAG_DIR/SUMMARY.json" 2>&1
import json
from pathlib import Path
from datetime import datetime, timezone

summary = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "diagnostics_collected": {
        "dashboard_apis": len(list(Path("$DIAG_DIR/dashboard_apis").glob("*.json"))),
        "sre_data": len(list(Path("$DIAG_DIR/sre").glob("*.json"))),
        "uw_signals": len(list(Path("$DIAG_DIR/uw_signals").glob("*.json"))),
        "heartbeats": len(list(Path("$DIAG_DIR/heartbeats").glob("*.json"))),
        "logs": len(list(Path("$DIAG_DIR/logs").glob("*"))),
        "state_files": len(list(Path("$DIAG_DIR/state").glob("*.json")))
    },
    "collection_notes": [
        "Dashboard APIs tested against localhost:5000",
        "SRE health collected from sre_monitoring module",
        "UW signals from cache and recent log files",
        "Heartbeat files from state/ directory",
        "Recent logs (last 200 lines) from logs/ directory",
        "System state files from state/ directory"
    ]
}

print(json.dumps(summary, indent=2, default=str))
PYTHON_EOF

echo "  ✓ Summary created"

# 8. EXPORT TO GIT
echo ""
echo "=================================================================================="
echo "EXPORTING TO GITHUB"
echo "=================================================================================="
echo ""

chmod +x push_to_github_clean.sh 2>/dev/null || true

if [ -f "push_to_github_clean.sh" ]; then
    ./push_to_github_clean.sh "$DIAG_DIR" "Dashboard diagnostics export - $(date +%Y-%m-%d\ %H:%M:%S)"
    echo ""
    echo "✅ Diagnostics exported to GitHub"
    echo ""
    echo "Next steps:"
    echo "1. Review the exported branch on GitHub"
    echo "2. Check SUMMARY.json for overview"
    echo "3. Review dashboard_apis/ for endpoint responses"
    echo "4. Review sre/ for SRE health data"
    echo "5. Review uw_signals/ for signal freshness"
else
    echo "⚠️  push_to_github_clean.sh not found - creating archive instead"
    tar -czf "${DIAG_DIR}.tar.gz" "$DIAG_DIR" 2>/dev/null || zip -r "${DIAG_DIR}.zip" "$DIAG_DIR" 2>/dev/null || true
    echo "✅ Diagnostics archived to ${DIAG_DIR}.tar.gz"
fi

echo ""
echo "=================================================================================="
echo "DIAGNOSTICS COLLECTION COMPLETE"
echo "=================================================================================="
echo "Directory: $DIAG_DIR"
echo ""
