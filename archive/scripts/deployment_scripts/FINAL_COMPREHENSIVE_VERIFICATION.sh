#!/bin/bash
# Final comprehensive verification: Run daemon, verify all endpoints, check data flow

cd ~/stock-bot

echo "=========================================="
echo "FINAL COMPREHENSIVE SYSTEM VERIFICATION"
echo "=========================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VERIFY_DIR="verification_${TIMESTAMP}"
mkdir -p "$VERIFY_DIR"

# Step 1: Stop existing and clear logs
echo "[1] Stopping existing daemon and clearing logs..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2
rm -f logs/uw_daemon.log .cursor/debug.log 2>/dev/null
mkdir -p .cursor logs

# Step 2: Run daemon for 2 minutes to collect data
echo "[2] Starting daemon for 2 minutes to collect endpoint data..."
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 120 seconds for polling cycles..."
sleep 120

# Stop daemon
echo "[3] Stopping daemon..."
kill $DAEMON_PID 2>/dev/null
sleep 2

# Step 4: Comprehensive analysis
echo "[4] Analyzing system status..."
python3 << PYEOF > "$VERIFY_DIR/comprehensive_analysis.json"
import json
import time
import re
from pathlib import Path

analysis = {
    "timestamp": int(time.time()),
    "daemon_status": {},
    "cache_status": {},
    "endpoint_activity": {},
    "learning_flow": {},
    "issues": [],
    "warnings": []
}

# Check daemon process
import subprocess
daemon_running = subprocess.run(["pgrep", "-f", "uw.*daemon|uw_flow_daemon"], 
                                capture_output=True, text=True).returncode == 0
analysis["daemon_status"]["running"] = daemon_running

# Check cache
cache_file = Path("data/uw_flow_cache.json")
analysis["cache_status"]["exists"] = cache_file.exists()
if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        analysis["cache_status"]["ticker_count"] = len(tickers)
        
        # Market-wide endpoints
        mt = cache_data.get("_market_tide", {})
        analysis["cache_status"]["market_tide"] = {
            "exists": bool(mt),
            "has_data": bool(mt.get("data")),
            "age_minutes": (time.time() - mt.get("last_update", 0)) / 60 if mt.get("last_update") else 999
        }
        
        tn = cache_data.get("_top_net_impact", {})
        analysis["cache_status"]["top_net_impact"] = {
            "exists": bool(tn),
            "has_data": bool(tn.get("data")),
            "age_minutes": (time.time() - tn.get("last_update", 0)) / 60 if tn.get("last_update") else 999
        }
        
        # Per-ticker endpoints (sample 3 tickers)
        if tickers:
            sample = tickers[0]
            ticker_data = cache_data.get(sample, {})
            if isinstance(ticker_data, str):
                try:
                    ticker_data = json.loads(ticker_data)
                except:
                    ticker_data = {}
            
            analysis["cache_status"]["sample_ticker"] = sample
            analysis["cache_status"]["sample_endpoints"] = {
                "flow_trades": len(ticker_data.get("flow_trades", [])),
                "dark_pool": bool(ticker_data.get("dark_pool")),
                "greeks": bool(ticker_data.get("greeks")),
                "iv_rank": bool(ticker_data.get("iv_rank")),
                "oi_change": bool(ticker_data.get("oi_change")),
                "etf_flow": bool(ticker_data.get("etf_flow")),
                "ftd_pressure": bool(ticker_data.get("ftd_pressure")),
            }
    except Exception as e:
        analysis["cache_status"]["error"] = str(e)

# Check daemon log for endpoint activity
log_file = Path("logs/uw_daemon.log")
if log_file.exists():
    log_content = log_file.read_text()
    
    # Count endpoint polling
    endpoints = ["market_tide", "top_net_impact", "option_flow", "dark_pool", 
                 "greek_exposure", "greeks", "iv_rank", "oi_change", 
                 "etf_flow", "shorts_ftds", "max_pain"]
    
    for endpoint in endpoints:
        count = len(re.findall(rf"Polling.*{endpoint}|Updated.*{endpoint}", log_content, re.IGNORECASE))
        analysis["endpoint_activity"][endpoint] = count
    
    # Check for errors
    errors = re.findall(r"Error|Exception|Traceback", log_content, re.IGNORECASE)
    analysis["endpoint_activity"]["error_count"] = len(errors)
    
    # Check if loop was entered
    if "run() method called" in log_content:
        analysis["endpoint_activity"]["loop_entered"] = True
    if "SUCCESS.*Entered main loop" in log_content or "INSIDE while loop" in log_content:
        analysis["endpoint_activity"]["loop_confirmed"] = True

# Check learning flow
attr_log = Path("logs/attribution.jsonl")
analysis["learning_flow"]["attribution_log"] = {
    "exists": attr_log.exists(),
    "size_bytes": attr_log.stat().st_size if attr_log.exists() else 0
}

if attr_log.exists():
    try:
        with attr_log.open() as f:
            lines = [l for l in f if l.strip()]
            analysis["learning_flow"]["attribution_log"]["entry_count"] = len(lines)
            if lines:
                sample = json.loads(lines[-1])
                analysis["learning_flow"]["attribution_log"]["has_components"] = "components" in sample.get("context", {})
    except Exception as e:
        analysis["learning_flow"]["attribution_log"]["error"] = str(e)

# Generate issues/warnings
if not analysis["cache_status"].get("exists"):
    analysis["issues"].append("Cache file does not exist")
if not analysis["cache_status"].get("market_tide", {}).get("has_data"):
    analysis["warnings"].append("market_tide not in cache")
if not analysis["cache_status"].get("top_net_impact", {}).get("has_data"):
    analysis["warnings"].append("top_net_impact not in cache")

sample_ep = analysis["cache_status"].get("sample_endpoints", {})
missing = []
if sample_ep.get("flow_trades", 0) == 0:
    missing.append("flow_trades")
if not sample_ep.get("greeks"):
    missing.append("greeks")
if not sample_ep.get("iv_rank"):
    missing.append("iv_rank")
if not sample_ep.get("oi_change"):
    missing.append("oi_change")
if not sample_ep.get("etf_flow"):
    missing.append("etf_flow")
if not sample_ep.get("ftd_pressure"):
    missing.append("ftd_pressure")
if missing:
    analysis["warnings"].append(f"Missing per-ticker endpoints: {', '.join(missing)}")

print(json.dumps(analysis, indent=2))
PYEOF

cat "$VERIFY_DIR/comprehensive_analysis.json" | python3 -m json.tool

echo ""
echo "[5] Recent daemon activity..."
if [ -f "logs/uw_daemon.log" ]; then
    {
        echo "=== Last 50 lines ==="
        tail -50 logs/uw_daemon.log
        echo ""
        echo "=== Endpoint polling summary ==="
        tail -200 logs/uw_daemon.log | grep -E "Polling|Updated|market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greek" | tail -30
    } > "$VERIFY_DIR/daemon_activity.txt"
    cat "$VERIFY_DIR/daemon_activity.txt"
fi

echo ""
echo "[6] Creating summary report..."
cat > "$VERIFY_DIR/SUMMARY.txt" << EOF
COMPREHENSIVE SYSTEM VERIFICATION
==================================
Timestamp: $(date)
Directory: $VERIFY_DIR

FILES COLLECTED:
- comprehensive_analysis.json: Complete system analysis
- daemon_activity.txt: Recent daemon log activity

NEXT STEPS:
1. Review comprehensive_analysis.json for endpoint status
2. Check daemon_activity.txt for polling activity
3. Verify all 11 endpoints are being polled
4. Confirm data flows to learning engine
EOF

cat "$VERIFY_DIR/SUMMARY.txt"

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo "All data saved to: $VERIFY_DIR/"
echo ""
echo "Pushing to GitHub for analysis..."
git add "$VERIFY_DIR"/* 2>/dev/null || true
git commit -m "Comprehensive system verification: $TIMESTAMP" 2>/dev/null || echo "No changes"
git push origin main 2>&1 | head -5 || echo "Push may have issues - check manually"

echo ""
echo "✅ Verification complete. Review files in $VERIFY_DIR/"
