#!/bin/bash
# Collect ALL logs and diagnostic data, then push to GitHub

cd ~/stock-bot

echo "=========================================="
echo "COLLECTING ALL LOGS FOR ANALYSIS"
echo "=========================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIAG_DIR="diagnostics_${TIMESTAMP}"
mkdir -p "$DIAG_DIR"

# Stop existing daemon
echo "[1] Stopping existing daemon..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear logs for fresh run
echo "[2] Clearing logs for fresh run..."
rm -f logs/uw_daemon.log .cursor/debug.log 2>/dev/null
mkdir -p .cursor logs

# Start daemon and let it run for 2 minutes
echo "[3] Starting daemon for 2 minutes to collect data..."
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 120 seconds for polling cycles..."
sleep 120

# Stop daemon
echo "[4] Stopping daemon..."
kill $DAEMON_PID 2>/dev/null
sleep 2

# Collect all logs
echo "[5] Collecting all logs and diagnostic data..."

# Daemon logs
if [ -f "logs/uw_daemon.log" ]; then
    cp logs/uw_daemon.log "$DIAG_DIR/uw_daemon_full.log"
    tail -500 logs/uw_daemon.log > "$DIAG_DIR/uw_daemon_recent.log"
    echo "✅ Collected daemon logs"
else
    echo "⚠️  No daemon log" > "$DIAG_DIR/uw_daemon_full.log"
fi

# Debug log
if [ -f ".cursor/debug.log" ]; then
    cp .cursor/debug.log "$DIAG_DIR/debug.log"
    echo "✅ Collected debug log"
else
    echo "⚠️  No debug log file created" > "$DIAG_DIR/debug.log"
fi

# Cache status
echo "[6] Collecting cache status..."
python3 << PYEOF > "$DIAG_DIR/cache_analysis.json"
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
analysis = {
    "timestamp": int(time.time()),
    "cache_exists": cache_file.exists(),
    "cache_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
}

if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        analysis["ticker_count"] = len(tickers)
        analysis["metadata_keys"] = [k for k in cache_data.keys() if k.startswith("_")]
        
        # Check market-wide endpoints
        analysis["market_tide"] = {
            "exists": "_market_tide" in cache_data,
            "has_data": bool(cache_data.get("_market_tide", {}).get("data")),
            "last_update": cache_data.get("_market_tide", {}).get("last_update", 0)
        }
        analysis["top_net_impact"] = {
            "exists": "_top_net_impact" in cache_data,
            "has_data": bool(cache_data.get("_top_net_impact", {}).get("data")),
            "last_update": cache_data.get("_top_net_impact", {}).get("last_update", 0)
        }
        
        # Sample ticker analysis
        if tickers:
            sample = tickers[0]
            sample_data = cache_data.get(sample, {})
            if isinstance(sample_data, str):
                try:
                    sample_data = json.loads(sample_data)
                except:
                    sample_data = {}
            
            analysis["sample_ticker"] = sample
            analysis["sample_data"] = {
                "flow_trades": len(sample_data.get("flow_trades", [])),
                "has_dark_pool": bool(sample_data.get("dark_pool")),
                "has_greeks": bool(sample_data.get("greeks")),
                "has_iv_rank": bool(sample_data.get("iv_rank")),
                "has_oi_change": bool(sample_data.get("oi_change")),
                "has_etf_flow": bool(sample_data.get("etf_flow")),
                "has_ftd_pressure": bool(sample_data.get("ftd_pressure")),
            }
    except Exception as e:
        analysis["error"] = str(e)

print(json.dumps(analysis, indent=2))
PYEOF

# Process status
echo "[7] Collecting process status..."
ps aux | grep -E "uw.*daemon|uw_flow_daemon|python.*uw" | grep -v grep > "$DIAG_DIR/processes.txt" || echo "No processes" > "$DIAG_DIR/processes.txt"

# Environment
echo "[8] Collecting environment info..."
{
    echo "Python version: $(python3 --version)"
    echo "Working directory: $(pwd)"
    echo "UW_API_KEY: ${UW_API_KEY:+SET}${UW_API_KEY:-NOT SET}"
    echo "Timestamp: $(date)"
} > "$DIAG_DIR/environment.txt"

# Smart poller state
echo "[9] Collecting smart poller state..."
if [ -f "state/smart_poller_state.json" ]; then
    cp state/smart_poller_state.json "$DIAG_DIR/smart_poller_state.json"
else
    echo "{}" > "$DIAG_DIR/smart_poller_state.json"
fi

# Log analysis
echo "[10] Analyzing logs..."
python3 << PYEOF > "$DIAG_DIR/log_analysis.json"
import json
import re
from pathlib import Path

log_file = Path("logs/uw_daemon.log")
analysis = {
    "log_exists": log_file.exists(),
    "line_count": 0,
    "endpoint_activity": {},
    "errors": [],
    "polling_activity": []
}

if log_file.exists():
    with log_file.open() as f:
        lines = f.readlines()
        analysis["line_count"] = len(lines)
        
        for line in lines:
            # Check for endpoint polling
            if "Polling" in line:
                analysis["polling_activity"].append(line.strip())
                # Extract endpoint name
                match = re.search(r"Polling (\w+)", line)
                if match:
                    endpoint = match.group(1)
                    analysis["endpoint_activity"][endpoint] = analysis["endpoint_activity"].get(endpoint, 0) + 1
            
            # Check for errors
            if "Error" in line or "error" in line or "Exception" in line or "Traceback" in line:
                analysis["errors"].append(line.strip())

# Limit arrays
analysis["polling_activity"] = analysis["polling_activity"][-50:]
analysis["errors"] = analysis["errors"][-20:]

print(json.dumps(analysis, indent=2))
PYEOF

# Create summary
echo "[11] Creating summary..."
cat > "$DIAG_DIR/SUMMARY.txt" << EOF
COMPREHENSIVE DIAGNOSTIC COLLECTION
====================================
Timestamp: $(date)
Directory: $DIAG_DIR

FILES COLLECTED:
- uw_daemon_full.log: Complete daemon log
- uw_daemon_recent.log: Last 500 lines
- debug.log: Debug instrumentation log (if exists)
- cache_analysis.json: Cache status and endpoint data
- processes.txt: Running processes
- environment.txt: Environment variables
- smart_poller_state.json: Poller state
- log_analysis.json: Log analysis

NEXT STEPS:
1. Review cache_analysis.json for endpoint data
2. Review log_analysis.json for polling activity
3. Check uw_daemon_recent.log for errors
4. Verify all 11 endpoints are being polled
EOF

# Push to GitHub
echo "[12] Pushing to GitHub..."
git add "$DIAG_DIR"/* 2>/dev/null || true
git commit -m "Comprehensive diagnostic collection: $TIMESTAMP" 2>/dev/null || echo "No changes to commit"

# Handle git push
if git push origin main 2>&1 | tee "$DIAG_DIR/git_push_output.txt"; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "⚠️  Git push had issues, trying pull and retry..."
    git pull --rebase origin main 2>/dev/null || git pull origin main 2>/dev/null
    git add "$DIAG_DIR"/* 2>/dev/null || true
    git commit -m "Comprehensive diagnostic collection: $TIMESTAMP" 2>/dev/null || true
    git push origin main 2>&1 | tee -a "$DIAG_DIR/git_push_output.txt" || true
fi

echo ""
echo "=========================================="
echo "COLLECTION COMPLETE"
echo "=========================================="
echo "Directory: $DIAG_DIR"
echo "Files:"
ls -lh "$DIAG_DIR"/
echo ""
echo "Review the files and check GitHub for the commit."
