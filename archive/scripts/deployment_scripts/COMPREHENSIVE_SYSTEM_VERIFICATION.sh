#!/bin/bash
# Comprehensive verification of entire data flow: UW API -> Cache -> Signals -> Learning

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE SYSTEM VERIFICATION"
echo "=========================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VERIFY_DIR="verification_${TIMESTAMP}"
mkdir -p "$VERIFY_DIR"

echo "[1] Verifying UW Daemon Status..."
{
    echo "=== UW DAEMON PROCESS ==="
    if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "✅ Running"
        ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep
    else
        echo "❌ NOT running"
    fi
} > "$VERIFY_DIR/1_daemon_status.txt"
cat "$VERIFY_DIR/1_daemon_status.txt"

echo ""
echo "[2] Verifying Cache Status and All Endpoints..."
python3 << PYEOF > "$VERIFY_DIR/2_cache_analysis.json"
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
analysis = {
    "timestamp": int(time.time()),
    "cache_exists": cache_file.exists(),
    "cache_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
    "endpoints_status": {}
}

if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        tickers = [k for k in cache_data.keys() if not k.startswith("_")]
        analysis["ticker_count"] = len(tickers)
        
        # Check market-wide endpoints
        market_tide = cache_data.get("_market_tide", {})
        analysis["endpoints_status"]["market_tide"] = {
            "exists": bool(market_tide),
            "has_data": bool(market_tide.get("data")),
            "last_update": market_tide.get("last_update", 0),
            "age_minutes": (time.time() - market_tide.get("last_update", 0)) / 60 if market_tide.get("last_update") else 999
        }
        
        top_net = cache_data.get("_top_net_impact", {})
        analysis["endpoints_status"]["top_net_impact"] = {
            "exists": bool(top_net),
            "has_data": bool(top_net.get("data")),
            "last_update": top_net.get("last_update", 0),
            "age_minutes": (time.time() - top_net.get("last_update", 0)) / 60 if top_net.get("last_update") else 999
        }
        
        # Check per-ticker endpoints for sample tickers
        if tickers:
            sample_tickers = tickers[:3]  # Check first 3
            analysis["sample_tickers"] = {}
            
            for ticker in sample_tickers:
                ticker_data = cache_data.get(ticker, {})
                if isinstance(ticker_data, str):
                    try:
                        ticker_data = json.loads(ticker_data)
                    except:
                        ticker_data = {}
                
                analysis["sample_tickers"][ticker] = {
                    "flow_trades": len(ticker_data.get("flow_trades", [])),
                    "has_dark_pool": bool(ticker_data.get("dark_pool")),
                    "has_greeks": bool(ticker_data.get("greeks")),
                    "has_iv_rank": bool(ticker_data.get("iv_rank")),
                    "has_oi_change": bool(ticker_data.get("oi_change")),
                    "has_etf_flow": bool(ticker_data.get("etf_flow")),
                    "has_ftd_pressure": bool(ticker_data.get("ftd_pressure")),
                }
        
        # Count endpoints found
        endpoint_count = 0
        if analysis["endpoints_status"]["market_tide"]["has_data"]:
            endpoint_count += 1
        if analysis["endpoints_status"]["top_net_impact"]["has_data"]:
            endpoint_count += 1
        
        for ticker_data in analysis["sample_tickers"].values():
            if ticker_data["flow_trades"] > 0:
                endpoint_count += 1
            if ticker_data["has_dark_pool"]:
                endpoint_count += 1
            if ticker_data["has_greeks"]:
                endpoint_count += 1
            if ticker_data["has_iv_rank"]:
                endpoint_count += 1
            if ticker_data["has_oi_change"]:
                endpoint_count += 1
            if ticker_data["has_etf_flow"]:
                endpoint_count += 1
            if ticker_data["has_ftd_pressure"]:
                endpoint_count += 1
        
        analysis["total_endpoints_found"] = endpoint_count
        analysis["expected_endpoints"] = 11  # market_tide, top_net_impact, and 9 per-ticker endpoints
        
    except Exception as e:
        analysis["error"] = str(e)
        import traceback
        analysis["traceback"] = traceback.format_exc()

print(json.dumps(analysis, indent=2))
PYEOF

cat "$VERIFY_DIR/2_cache_analysis.json" | python3 -m json.tool

echo ""
echo "[3] Verifying Signal Components..."
python3 << PYEOF > "$VERIFY_DIR/3_signal_components.json"
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

try:
    from config.uw_signal_contracts import UW_ENDPOINT_CONTRACTS
    
    analysis = {
        "endpoints_defined": len(UW_ENDPOINT_CONTRACTS),
        "endpoint_list": list(UW_ENDPOINT_CONTRACTS.keys()),
        "status": "✅ Signal contracts loaded"
    }
except Exception as e:
    analysis = {
        "status": "❌ Failed to load signal contracts",
        "error": str(e)
    }

print(json.dumps(analysis, indent=2))
PYEOF

cat "$VERIFY_DIR/3_signal_components.json" | python3 -m json.tool

echo ""
echo "[4] Verifying Learning Engine Data Flow..."
python3 << PYEOF > "$VERIFY_DIR/4_learning_flow.json"
import json
from pathlib import Path

analysis = {
    "attribution_log": {
        "exists": Path("logs/attribution.jsonl").exists(),
        "size_bytes": Path("logs/attribution.jsonl").stat().st_size if Path("logs/attribution.jsonl").exists() else 0
    },
    "learning_state": {
        "exists": Path("state/learning_processing_state.json").exists()
    },
    "weight_updates": {
        "exists": Path("data/weight_learning.jsonl").exists(),
        "size_bytes": Path("data/weight_learning.jsonl").stat().st_size if Path("data/weight_learning.jsonl").exists() else 0
    }
}

# Count attribution entries
if analysis["attribution_log"]["exists"]:
    try:
        with Path("logs/attribution.jsonl").open() as f:
            lines = [l for l in f if l.strip()]
            analysis["attribution_log"]["entry_count"] = len(lines)
            if lines:
                # Check if entries have component data
                sample = json.loads(lines[-1])
                analysis["attribution_log"]["has_components"] = "components" in sample.get("context", {})
    except Exception as e:
        analysis["attribution_log"]["error"] = str(e)

print(json.dumps(analysis, indent=2))
PYEOF

cat "$VERIFY_DIR/4_learning_flow.json" | python3 -m json.tool

echo ""
echo "[5] Checking Recent Daemon Activity..."
if [ -f "logs/uw_daemon.log" ]; then
    {
        echo "=== Last 30 lines of daemon log ==="
        tail -30 logs/uw_daemon.log
        echo ""
        echo "=== Endpoint polling activity (last 100 lines) ==="
        tail -100 logs/uw_daemon.log | grep -E "Polling|Updated|market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greek" | tail -20
    } > "$VERIFY_DIR/5_daemon_activity.txt"
    cat "$VERIFY_DIR/5_daemon_activity.txt"
else
    echo "⚠️  No daemon log file"
fi

echo ""
echo "[6] Creating Summary..."
python3 << PYEOF > "$VERIFY_DIR/6_summary.txt"
import json
from pathlib import Path

# Load all analysis files
cache_analysis = json.loads(Path("$VERIFY_DIR/2_cache_analysis.json").read_text())
signal_analysis = json.loads(Path("$VERIFY_DIR/3_signal_components.json").read_text())
learning_analysis = json.loads(Path("$VERIFY_DIR/4_learning_flow.json").read_text())

print("=" * 80)
print("COMPREHENSIVE SYSTEM VERIFICATION SUMMARY")
print("=" * 80)
print()

# Daemon status
daemon_status = Path("$VERIFY_DIR/1_daemon_status.txt").read_text()
if "✅ Running" in daemon_status:
    print("✅ UW DAEMON: Running")
else:
    print("❌ UW DAEMON: NOT Running")
print()

# Cache status
if cache_analysis.get("cache_exists"):
    print(f"✅ CACHE: Exists ({cache_analysis.get('cache_size_bytes', 0)} bytes)")
    print(f"   Tickers: {cache_analysis.get('ticker_count', 0)}")
    print(f"   Endpoints found: {cache_analysis.get('total_endpoints_found', 0)}/{cache_analysis.get('expected_endpoints', 11)}")
    
    # Market-wide
    mt = cache_analysis.get("endpoints_status", {}).get("market_tide", {})
    if mt.get("has_data"):
        print(f"   ✅ market_tide: {mt.get('age_minutes', 0):.1f} min old")
    else:
        print(f"   ❌ market_tide: Not found")
    
    tn = cache_analysis.get("endpoints_status", {}).get("top_net_impact", {})
    if tn.get("has_data"):
        print(f"   ✅ top_net_impact: {tn.get('age_minutes', 0):.1f} min old")
    else:
        print(f"   ❌ top_net_impact: Not found")
    
    # Per-ticker
    print("   Per-ticker endpoints (sample):")
    for ticker, data in cache_analysis.get("sample_tickers", {}).items():
        found = sum([
            data.get("flow_trades", 0) > 0,
            data.get("has_dark_pool", False),
            data.get("has_greeks", False),
            data.get("has_iv_rank", False),
            data.get("has_oi_change", False),
            data.get("has_etf_flow", False),
            data.get("has_ftd_pressure", False)
        ])
        print(f"     {ticker}: {found}/7 endpoints")
else:
    print("❌ CACHE: Does not exist")
print()

# Signal components
if signal_analysis.get("status") == "✅ Signal contracts loaded":
    print(f"✅ SIGNAL CONTRACTS: {signal_analysis.get('endpoints_defined', 0)} endpoints defined")
else:
    print(f"❌ SIGNAL CONTRACTS: {signal_analysis.get('status', 'Unknown')}")
print()

# Learning flow
print("LEARNING ENGINE DATA FLOW:")
attr = learning_analysis.get("attribution_log", {})
if attr.get("exists"):
    print(f"   ✅ Attribution log: {attr.get('entry_count', 0)} entries")
    if attr.get("has_components"):
        print("   ✅ Entries have component data")
    else:
        print("   ⚠️  Entries missing component data")
else:
    print("   ❌ Attribution log: Not found")

weight = learning_analysis.get("weight_updates", {})
if weight.get("exists"):
    print(f"   ✅ Weight updates log: {weight.get('size_bytes', 0)} bytes")
else:
    print("   ⚠️  Weight updates log: Not found")
print()

# Overall status
print("=" * 80)
print("OVERALL STATUS")
print("=" * 80)

issues = []
if "❌" in daemon_status:
    issues.append("Daemon not running")
if not cache_analysis.get("cache_exists"):
    issues.append("Cache file missing")
if cache_analysis.get("total_endpoints_found", 0) < 5:
    issues.append(f"Only {cache_analysis.get('total_endpoints_found', 0)} endpoints found (expected 11+)")
if not attr.get("exists"):
    issues.append("Attribution log missing")

if issues:
    print("⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
else:
    print("✅ SYSTEM OPERATIONAL")
    print("   - Daemon running")
    print("   - Cache populated")
    print("   - Endpoints being polled")
    print("   - Data flowing to learning engine")
PYEOF

cat "$VERIFY_DIR/6_summary.txt"

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo "All data saved to: $VERIFY_DIR/"
echo ""
