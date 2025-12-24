#!/bin/bash
# Collect all diagnostic data and push to GitHub for analysis

cd ~/stock-bot

echo "=========================================="
echo "COLLECTING DIAGNOSTIC DATA FOR ANALYSIS"
echo "=========================================="
echo ""

# Create diagnostics directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIAG_DIR="diagnostics_${TIMESTAMP}"
mkdir -p "$DIAG_DIR"

echo "[1] Collecting UW daemon logs..."
if [ -f "logs/uw_daemon.log" ]; then
    cp logs/uw_daemon.log "$DIAG_DIR/uw_daemon.log"
    tail -500 logs/uw_daemon.log > "$DIAG_DIR/uw_daemon_recent.log"
    echo "✅ Collected UW daemon logs"
else
    echo "⚠️  No UW daemon log found" > "$DIAG_DIR/uw_daemon.log"
fi

echo "[2] Collecting cache status..."
python3 << PYEOF > "$DIAG_DIR/cache_status.json"
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
diagnostics = {
    "cache_exists": cache_file.exists(),
    "timestamp": int(time.time()),
    "cache_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
}

if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        diagnostics["ticker_count"] = len(tickers)
        diagnostics["metadata"] = cache_data.get("_metadata", {})
        
        # Sample first ticker
        if tickers:
            sample = tickers[0]
            symbol_data = cache_data.get(sample, {})
            if isinstance(symbol_data, str):
                try:
                    symbol_data = json.loads(symbol_data)
                except:
                    symbol_data = {}
            
            diagnostics["sample_ticker"] = sample
            diagnostics["sample_data"] = {
                "has_flow_trades": len(symbol_data.get("flow_trades", [])) > 0,
                "has_dark_pool": bool(symbol_data.get("dark_pool")),
                "has_greeks": bool(symbol_data.get("greeks")),
                "has_oi_change": bool(symbol_data.get("oi_change")),
                "has_etf_flow": bool(symbol_data.get("etf_flow")),
                "has_iv_rank": bool(symbol_data.get("iv_rank")),
                "has_ftd_pressure": bool(symbol_data.get("ftd_pressure")),
                "greeks_keys": list(symbol_data.get("greeks", {}).keys()) if symbol_data.get("greeks") else [],
            }
        
        # Market-wide data
        diagnostics["market_tide"] = {
            "exists": bool(cache_data.get("_market_tide", {}).get("data")),
            "last_update": cache_data.get("_market_tide", {}).get("last_update", 0),
        }
        diagnostics["top_net_impact"] = {
            "exists": bool(cache_data.get("_top_net_impact", {}).get("data")),
            "last_update": cache_data.get("_top_net_impact", {}).get("last_update", 0),
        }
    except Exception as e:
        diagnostics["error"] = str(e)

print(json.dumps(diagnostics, indent=2))
PYEOF

echo "[3] Collecting endpoint verification..."
python3 << PYEOF > "$DIAG_DIR/endpoint_verification.json"
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
verification = {
    "timestamp": int(time.time()),
    "endpoints": {}
}

if cache_file.exists():
    cache_data = json.loads(cache_file.read_text())
    tickers = [k for k in cache_data.keys() if not k.startswith("_")]
    
    if tickers:
        sample = tickers[0]
        symbol_data = cache_data.get(sample, {})
        if isinstance(symbol_data, str):
            try:
                symbol_data = json.loads(symbol_data)
            except:
                symbol_data = {}
        
        greeks = symbol_data.get("greeks", {})
        
        verification["endpoints"] = {
            "option_flow": len(symbol_data.get("flow_trades", [])) > 0,
            "dark_pool": bool(symbol_data.get("dark_pool")),
            "greek_exposure": bool(greeks.get("gamma_exposure") or greeks.get("total_gamma")),
            "greeks": bool(greeks),
            "iv_rank": bool(symbol_data.get("iv_rank")),
            "market_tide": bool(cache_data.get("_market_tide", {}).get("data")),
            "max_pain": bool(greeks.get("max_pain")),
            "net_impact": bool(cache_data.get("_top_net_impact", {}).get("data")),
            "oi_change": bool(symbol_data.get("oi_change")),
            "etf_flow": bool(symbol_data.get("etf_flow")),
            "shorts_ftds": bool(symbol_data.get("ftd_pressure")),
        }
        
        verification["sample_ticker"] = sample
        verification["sample_data_keys"] = list(symbol_data.keys())

print(json.dumps(verification, indent=2))
PYEOF

echo "[4] Collecting process status..."
ps aux | grep -E "uw.*daemon|uw_flow_daemon|main.py|dashboard|sre_monitoring|cache_enrichment" | grep -v grep > "$DIAG_DIR/processes.txt"

echo "[5] Collecting log file sizes..."
ls -lh logs/*.log 2>/dev/null > "$DIAG_DIR/log_sizes.txt" || echo "No log files found" > "$DIAG_DIR/log_sizes.txt"

echo "[6] Collecting recent UW daemon activity..."
if [ -f "logs/uw_daemon.log" ]; then
    tail -200 logs/uw_daemon.log | grep -E "Updated|Error|market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greek|greeks|Polling|API returned" > "$DIAG_DIR/recent_activity.txt" || echo "No recent activity found" > "$DIAG_DIR/recent_activity.txt"
fi

echo "[7] Collecting SRE monitoring status..."
if [ -f "sre_monitoring.py" ]; then
    python3 << PYEOF > "$DIAG_DIR/sre_status.json" 2>&1
import json
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path.cwd()))
    from sre_monitoring import get_signal_health, get_api_endpoint_health
    
    signal_health = get_signal_health()
    api_health = get_api_endpoint_health()
    
    status = {
        "signal_health": signal_health,
        "api_endpoint_health": api_health,
        "timestamp": int(__import__("time").time()),
    }
    
    print(json.dumps(status, indent=2, default=str))
except Exception as e:
    print(json.dumps({"error": str(e), "traceback": __import__("traceback").format_exc()}, indent=2))
PYEOF
fi

echo "[8] Collecting smart poller state..."
if [ -f "state/smart_poller_state.json" ]; then
    cp state/smart_poller_state.json "$DIAG_DIR/smart_poller_state.json"
fi

echo "[9] Creating summary..."
cat > "$DIAG_DIR/SUMMARY.txt" << EOF
Diagnostic Collection Summary
=============================
Timestamp: $(date)
Collection Directory: $DIAG_DIR

Files Collected:
- uw_daemon.log (full log)
- uw_daemon_recent.log (last 500 lines)
- cache_status.json (cache analysis)
- endpoint_verification.json (endpoint status)
- processes.txt (running processes)
- log_sizes.txt (log file sizes)
- recent_activity.txt (recent daemon activity)
- sre_status.json (SRE monitoring status)
- smart_poller_state.json (poller state)

Next Steps:
1. Review diagnostic files
2. Identify issues
3. Fix code
4. Deploy fixes
EOF

echo "[10] Committing to git..."
git add "$DIAG_DIR"/* 2>/dev/null || true
git add "$DIAG_DIR" 2>/dev/null || true
git commit -m "Diagnostic data collection: $TIMESTAMP" 2>/dev/null || echo "⚠️  Git commit failed (may be no changes)"

echo "[11] Pushing to GitHub..."
git push origin main 2>&1 | tee "$DIAG_DIR/git_push_output.txt"

echo ""
echo "=========================================="
echo "DIAGNOSTIC COLLECTION COMPLETE"
echo "=========================================="
echo ""
echo "Directory: $DIAG_DIR"
echo "Files collected and pushed to GitHub"
echo ""
echo "Review the diagnostic files in: $DIAG_DIR/"
echo "Or check GitHub for the latest commit"
echo ""
