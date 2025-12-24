#!/bin/bash
# COMPREHENSIVE SIGNAL & UW API DIAGNOSTICS
# Tests all 19 signal components, their UW API endpoints, and learning engine integration
# Outputs detailed report for GitHub analysis

set +e  # Continue even if commands fail
cd ~/stock-bot

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DIAG_DIR="signal_diagnostics_${TIMESTAMP}"
mkdir -p "$DIAG_DIR"

echo "=========================================="
echo "COMPREHENSIVE SIGNAL & UW API DIAGNOSTICS"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# STEP 1: Check all 19 signal components
echo "[STEP 1] Analyzing all 19 signal components..."
python3 << 'PYEOF' > "$DIAG_DIR/signal_components_analysis.json" 2>&1
import json
import time
from pathlib import Path

# All 19 signal components from config
ALL_SIGNALS = [
    "flow", "dark_pool", "insider", "iv_term_skew", "smile_slope",
    "whale_persistence", "event_alignment", "temporal_motif", "toxicity_penalty",
    "regime_modifier", "congress", "shorts_squeeze", "institutional",
    "market_tide", "calendar_catalyst", "greeks_gamma", "ftd_pressure",
    "iv_rank", "oi_change", "etf_flow", "squeeze_score", "freshness_factor"
]

# Map signals to their UW API endpoints
SIGNAL_TO_ENDPOINT = {
    "flow": "/api/option-trades/flow-alerts",
    "dark_pool": "/api/darkpool/{ticker}",
    "insider": "/api/insider/{ticker}",
    "market_tide": "/api/market/market-tide",
    "greeks_gamma": "/api/stock/{ticker}/greek-exposure",
    "oi_change": "/api/stock/{ticker}/oi-change",
    "etf_flow": "/api/etfs/{ticker}/in-outflow",
    "iv_rank": "/api/stock/{ticker}/iv-rank",
    "ftd_pressure": "/api/shorts/{ticker}/ftds",
    "shorts_squeeze": "/api/shorts/{ticker}/data",
    "congress": "/api/congress/{ticker}",
    "institutional": "/api/institution/{ticker}/ownership",
    "calendar_catalyst": "/api/calendar/{ticker}",
}

results = {
    "timestamp": time.time(),
    "total_signals": len(ALL_SIGNALS),
    "signals_checked": 0,
    "signals_with_data": 0,
    "signals_without_data": 0,
    "signals": {},
    "uw_cache_status": {},
    "learning_engine_status": {}
}

# Check UW cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        cache_age = time.time() - cache_file.stat().st_mtime
        results["uw_cache_status"] = {
            "exists": True,
            "age_sec": cache_age,
            "age_minutes": cache_age / 60,
            "symbols_count": len([k for k in cache_data.keys() if not k.startswith("_")]),
            "sample_symbols": [k for k in cache_data.keys() if not k.startswith("_")][:10]
        }
        
        # Check each signal in cache
        sample_symbol = results["uw_cache_status"]["sample_symbols"][0] if results["uw_cache_status"]["sample_symbols"] else None
        if sample_symbol:
            symbol_data = cache_data.get(sample_symbol, {})
            if isinstance(symbol_data, str):
                try:
                    symbol_data = json.loads(symbol_data)
                except:
                    symbol_data = {}
            
            for signal in ALL_SIGNALS:
                signal_key = signal.replace("_", "")  # Try variations
                has_data = False
                data_value = None
                
                # Check various key formats
                for key in [signal, signal_key, f"{signal}_data", f"{signal}_value"]:
                    if key in symbol_data and symbol_data[key] not in (None, 0, 0.0, "", []):
                        has_data = True
                        data_value = symbol_data[key]
                        break
                
                # Also check nested structures
                if not has_data:
                    for key, value in symbol_data.items():
                        if signal in key.lower() and value not in (None, 0, 0.0, "", []):
                            has_data = True
                            data_value = value
                            break
                
                results["signals"][signal] = {
                    "has_data_in_cache": has_data,
                    "data_sample": str(data_value)[:100] if data_value else None,
                    "uw_endpoint": SIGNAL_TO_ENDPOINT.get(signal, "unknown"),
                    "type": "core" if signal in ["flow", "dark_pool", "insider"] else 
                           "computed" if signal in ["iv_term_skew", "smile_slope"] else "enriched"
                }
                
                if has_data:
                    results["signals_with_data"] += 1
                else:
                    results["signals_without_data"] += 1
                results["signals_checked"] += 1
    except Exception as e:
        results["uw_cache_status"]["error"] = str(e)
else:
    results["uw_cache_status"] = {"exists": False, "error": "Cache file not found"}

# Check learning engine integration
learning_files = [
    Path("logs/attribution.jsonl"),
    Path("data/comprehensive_learning.jsonl"),
    Path("state/learning_processing_state.json")
]

for lf in learning_files:
    if lf.exists():
        try:
            if lf.suffix == ".jsonl":
                # Count lines
                with open(lf, "r") as f:
                    lines = [l for l in f if l.strip()]
                    results["learning_engine_status"][lf.name] = {
                        "exists": True,
                        "entries": len(lines),
                        "age_sec": time.time() - lf.stat().st_mtime
                    }
            else:
                data = json.loads(lf.read_text())
                results["learning_engine_status"][lf.name] = {
                    "exists": True,
                    "keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
                    "age_sec": time.time() - lf.stat().st_mtime
                }
        except Exception as e:
            results["learning_engine_status"][lf.name] = {"error": str(e)}

print(json.dumps(results, indent=2))
PYEOF

echo "✅ Signal components analyzed"
echo ""

# STEP 2: Test all UW API endpoints
echo "[STEP 2] Testing all UW API endpoints..."
python3 << 'PYEOF' > "$DIAG_DIR/uw_endpoints_test.json" 2>&1
import os
import json
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
UW_API_KEY = os.getenv("UW_API_KEY")
BASE_URL = "https://api.unusualwhales.com"

# All UW endpoints from config
ENDPOINTS = [
    ("option_flow", "/api/option-trades/flow-alerts", None),
    ("dark_pool", "/api/darkpool/AAPL", "AAPL"),
    ("greeks", "/api/stock/AAPL/greeks", "AAPL"),
    ("net_impact", "/api/market/top-net-impact", None),
    ("market_tide", "/api/market/market-tide", None),
    ("greek_exposure", "/api/stock/AAPL/greek-exposure", "AAPL"),
    ("oi_change", "/api/stock/AAPL/oi-change", "AAPL"),
    ("etf_flow", "/api/etfs/AAPL/in-outflow", "AAPL"),
    ("iv_rank", "/api/stock/AAPL/iv-rank", "AAPL"),
    ("shorts_ftds", "/api/shorts/AAPL/ftds", "AAPL"),
    ("max_pain", "/api/stock/AAPL/max-pain", "AAPL"),
    ("insider", "/api/insider/AAPL", "AAPL"),
    ("congress", "/api/congress/AAPL", "AAPL"),
    ("institutional", "/api/institution/AAPL/ownership", "AAPL"),
    ("calendar", "/api/calendar/AAPL", "AAPL"),
]

results = {
    "api_key_present": bool(UW_API_KEY),
    "base_url": BASE_URL,
    "timestamp": time.time(),
    "endpoints_tested": 0,
    "endpoints_working": 0,
    "endpoints_failed": 0,
    "endpoints": {}
}

if not UW_API_KEY:
    results["error"] = "UW_API_KEY not found"
    print(json.dumps(results, indent=2))
    exit(0)

headers = {"Authorization": f"Bearer {UW_API_KEY}"}

for name, endpoint, ticker in ENDPOINTS:
    results["endpoints_tested"] += 1
    try:
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        resp = requests.get(url, headers=headers, timeout=10)
        latency_ms = (time.time() - start_time) * 1000
        
        results["endpoints"][name] = {
            "endpoint": endpoint,
            "status_code": resp.status_code,
            "success": resp.status_code == 200,
            "latency_ms": round(latency_ms, 2),
            "response_size": len(resp.text),
            "error": None
        }
        
        if resp.status_code == 200:
            results["endpoints_working"] += 1
            try:
                data = resp.json()
                results["endpoints"][name]["response_keys"] = list(data.keys())[:10] if isinstance(data, dict) else "not_dict"
            except:
                pass
        else:
            results["endpoints_failed"] += 1
            try:
                error_data = resp.json()
                results["endpoints"][name]["error"] = str(error_data).replace(UW_API_KEY, "***REDACTED***")[:200]
            except:
                results["endpoints"][name]["error"] = resp.text[:200]
    except Exception as e:
        results["endpoints_failed"] += 1
        results["endpoints"][name] = {
            "endpoint": endpoint,
            "status_code": None,
            "success": False,
            "error": str(e)[:200]
        }

print(json.dumps(results, indent=2))
PYEOF

echo "✅ UW endpoints tested"
echo ""

# STEP 3: Check SRE health response
echo "[STEP 3] Checking SRE health response..."
curl -s http://localhost:5000/api/sre/health > "$DIAG_DIR/sre_health_full.json" 2>/dev/null || echo '{"error": "SRE endpoint failed"}' > "$DIAG_DIR/sre_health_full.json"

# Extract signal components and UW endpoints
python3 << 'PYEOF' > "$DIAG_DIR/sre_health_summary.json" 2>&1
import json
from pathlib import Path

sre_file = Path("$DIAG_DIR/sre_health_full.json")
if sre_file.exists():
    try:
        data = json.loads(sre_file.read_text())
        
        summary = {
            "signal_components_count": len(data.get("signal_components", {})),
            "uw_endpoints_count": len(data.get("uw_api_endpoints", {})),
            "signal_components": {},
            "uw_endpoints": {}
        }
        
        # Signal components summary
        for name, health in data.get("signal_components", {}).items():
            summary["signal_components"][name] = {
                "status": health.get("status"),
                "type": health.get("signal_type"),
                "data_freshness_sec": health.get("data_freshness_sec"),
                "signals_generated_1h": health.get("signals_generated_1h", 0)
            }
        
        # UW endpoints summary
        for name, health in data.get("uw_api_endpoints", {}).items():
            summary["uw_endpoints"][name] = {
                "status": health.get("status"),
                "endpoint": health.get("endpoint"),
                "error_rate_1h": health.get("error_rate_1h", 0),
                "last_error": health.get("last_error")
            }
        
        print(json.dumps(summary, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
else:
    print(json.dumps({"error": "SRE health file not found"}, indent=2))
PYEOF

echo "✅ SRE health analyzed"
echo ""

# STEP 4: Check learning engine integration
echo "[STEP 4] Checking learning engine integration..."
python3 << 'PYEOF' > "$DIAG_DIR/learning_engine_status.json" 2>&1
import json
import time
from pathlib import Path

results = {
    "attribution_file": {},
    "comprehensive_learning": {},
    "learning_state": {},
    "recent_trades_with_signals": 0
}

# Check attribution.jsonl (signals -> trades mapping)
attribution_file = Path("logs/attribution.jsonl")
if attribution_file.exists():
    try:
        with open(attribution_file, "r") as f:
            lines = [l for l in f if l.strip()]
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            
            signal_components_used = set()
            for line in recent_lines:
                try:
                    entry = json.loads(line)
                    if "signals" in entry:
                        for sig_name, sig_value in entry.get("signals", {}).items():
                            if sig_value not in (None, 0, 0.0, ""):
                                signal_components_used.add(sig_name)
                    if entry.get("type") == "attribution":
                        results["recent_trades_with_signals"] += 1
                except:
                    pass
            
            results["attribution_file"] = {
                "exists": True,
                "total_entries": len(lines),
                "recent_entries": len(recent_lines),
                "age_sec": time.time() - attribution_file.stat().st_mtime,
                "signal_components_used": sorted(list(signal_components_used))
            }
    except Exception as e:
        results["attribution_file"] = {"error": str(e)}
else:
    results["attribution_file"] = {"exists": False}

# Check comprehensive learning
learning_file = Path("data/comprehensive_learning.jsonl")
if learning_file.exists():
    try:
        with open(learning_file, "r") as f:
            lines = [l for l in f if l.strip()]
            results["comprehensive_learning"] = {
                "exists": True,
                "entries": len(lines),
                "age_sec": time.time() - learning_file.stat().st_mtime
            }
    except Exception as e:
        results["comprehensive_learning"] = {"error": str(e)}
else:
    results["comprehensive_learning"] = {"exists": False}

# Check learning state
state_file = Path("state/learning_processing_state.json")
if state_file.exists():
    try:
        data = json.loads(state_file.read_text())
        results["learning_state"] = {
            "exists": True,
            "keys": list(data.keys()),
            "age_sec": time.time() - state_file.stat().st_mtime
        }
    except Exception as e:
        results["learning_state"] = {"error": str(e)}
else:
    results["learning_state"] = {"exists": False}

print(json.dumps(results, indent=2))
PYEOF

echo "✅ Learning engine checked"
echo ""

# STEP 5: Create comprehensive summary
echo "[STEP 5] Creating comprehensive summary..."
python3 << 'PYEOF' > "$DIAG_DIR/COMPREHENSIVE_SUMMARY.json" 2>&1
import json
from pathlib import Path

summary = {
    "diagnostic_timestamp": "$TIMESTAMP",
    "overall_status": "unknown",
    "issues": [],
    "recommendations": [],
    "signal_components": {},
    "uw_endpoints": {},
    "learning_integration": {}
}

# Load all diagnostic files
try:
    signal_analysis = json.loads(Path("$DIAG_DIR/signal_components_analysis.json").read_text())
    uw_test = json.loads(Path("$DIAG_DIR/uw_endpoints_test.json").read_text())
    sre_summary = json.loads(Path("$DIAG_DIR/sre_health_summary.json").read_text())
    learning_status = json.loads(Path("$DIAG_DIR/learning_engine_status.json").read_text())
    
    # Signal components
    summary["signal_components"] = {
        "total": signal_analysis.get("total_signals", 0),
        "with_data": signal_analysis.get("signals_with_data", 0),
        "without_data": signal_analysis.get("signals_without_data", 0),
        "cache_status": signal_analysis.get("uw_cache_status", {}),
        "details": signal_analysis.get("signals", {})
    }
    
    # UW endpoints
    summary["uw_endpoints"] = {
        "total_tested": uw_test.get("endpoints_tested", 0),
        "working": uw_test.get("endpoints_working", 0),
        "failed": uw_test.get("endpoints_failed", 0),
        "api_key_present": uw_test.get("api_key_present", False),
        "details": uw_test.get("endpoints", {})
    }
    
    # Learning integration
    summary["learning_integration"] = {
        "attribution_entries": learning_status.get("attribution_file", {}).get("total_entries", 0),
        "signal_components_used": learning_status.get("attribution_file", {}).get("signal_components_used", []),
        "recent_trades_with_signals": learning_status.get("recent_trades_with_signals", 0),
        "comprehensive_learning_exists": learning_status.get("comprehensive_learning", {}).get("exists", False)
    }
    
    # Identify issues
    if summary["signal_components"]["without_data"] > summary["signal_components"]["with_data"]:
        summary["issues"].append(f"Most signals ({summary['signal_components']['without_data']}) have no data in cache")
    
    if summary["uw_endpoints"]["failed"] > 0:
        summary["issues"].append(f"{summary['uw_endpoints']['failed']} UW API endpoints are failing")
    
    if not summary["uw_endpoints"]["api_key_present"]:
        summary["issues"].append("UW_API_KEY not found - endpoints cannot be tested")
    
    if summary["learning_integration"]["recent_trades_with_signals"] == 0:
        summary["issues"].append("No recent trades with signal attribution found")
    
    # Recommendations
    if summary["signal_components"]["cache_status"].get("age_minutes", 999) > 10:
        summary["recommendations"].append("UW cache is stale - restart UW daemon")
    
    if summary["uw_endpoints"]["failed"] > 0:
        summary["recommendations"].append("Fix failing UW API endpoints - check API key and rate limits")
    
    if summary["signal_components"]["without_data"] > 10:
        summary["recommendations"].append("Most enriched signals have no data - check enrichment service")
    
    # Overall status
    if len(summary["issues"]) == 0:
        summary["overall_status"] = "healthy"
    elif len(summary["issues"]) <= 2:
        summary["overall_status"] = "degraded"
    else:
        summary["overall_status"] = "critical"
        
except Exception as e:
    summary["error"] = str(e)

print(json.dumps(summary, indent=2))
PYEOF

echo "✅ Summary created"
echo ""

# STEP 6: Create readable report
echo "[STEP 6] Creating readable report..."
cat > "$DIAG_DIR/DIAGNOSTIC_REPORT.md" << 'REPORT_EOF'
# Comprehensive Signal & UW API Diagnostic Report

Generated: $TIMESTAMP

## Executive Summary

$(cat "$DIAG_DIR/COMPREHENSIVE_SUMMARY.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Overall Status: {d.get('overall_status', 'unknown').upper()}\"); print(f\"Total Issues: {len(d.get('issues', []))}\"); print(f\"Recommendations: {len(d.get('recommendations', []))}\")")

## Signal Components Status

$(cat "$DIAG_DIR/signal_components_analysis.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Total Signals: {d.get('total_signals', 0)}\"); print(f\"With Data: {d.get('signals_with_data', 0)}\"); print(f\"Without Data: {d.get('signals_without_data', 0)}\"); print(f\"\\nCache Status:\"); cache=d.get('uw_cache_status', {}); print(f\"  Exists: {cache.get('exists', False)}\"); print(f\"  Age: {cache.get('age_minutes', 0):.1f} minutes\"); print(f\"  Symbols: {cache.get('symbols_count', 0)}\")")

## UW API Endpoints Status

$(cat "$DIAG_DIR/uw_endpoints_test.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Total Tested: {d.get('endpoints_tested', 0)}\"); print(f\"Working: {d.get('endpoints_working', 0)}\"); print(f\"Failed: {d.get('endpoints_failed', 0)}\"); print(f\"API Key Present: {d.get('api_key_present', False)}\")")

## Learning Engine Integration

$(cat "$DIAG_DIR/learning_engine_status.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Attribution Entries: {d.get('attribution_file', {}).get('total_entries', 0)}\"); print(f\"Recent Trades with Signals: {d.get('recent_trades_with_signals', 0)}\"); print(f\"Signal Components Used: {len(d.get('attribution_file', {}).get('signal_components_used', []))}\")")

## Detailed Files

- `signal_components_analysis.json` - Full signal component analysis
- `uw_endpoints_test.json` - Complete UW API endpoint test results
- `sre_health_summary.json` - SRE health summary
- `learning_engine_status.json` - Learning engine integration status
- `COMPREHENSIVE_SUMMARY.json` - Complete summary with issues and recommendations

REPORT_EOF

echo "✅ Report created"
echo ""

# STEP 7: Summary
echo "=========================================="
echo "DIAGNOSTICS COMPLETE"
echo "=========================================="
echo ""
echo "All diagnostics saved to: $DIAG_DIR"
echo ""
echo "Key Files:"
echo "  - $DIAG_DIR/COMPREHENSIVE_SUMMARY.json (main summary)"
echo "  - $DIAG_DIR/DIAGNOSTIC_REPORT.md (readable report)"
echo "  - $DIAG_DIR/signal_components_analysis.json (all 19 signals)"
echo "  - $DIAG_DIR/uw_endpoints_test.json (all UW endpoints)"
echo ""
echo "Quick Summary:"
cat "$DIAG_DIR/COMPREHENSIVE_SUMMARY.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Status: {d.get('overall_status', 'unknown')}\"); print(f\"  Signals with data: {d.get('signal_components', {}).get('with_data', 0)}/{d.get('signal_components', {}).get('total', 0)}\"); print(f\"  UW endpoints working: {d.get('uw_endpoints', {}).get('working', 0)}/{d.get('uw_endpoints', {}).get('total_tested', 0)}\"); print(f\"  Issues: {len(d.get('issues', []))}\")" 2>/dev/null || echo "  (Summary parsing failed)"
echo ""
echo "Next: Push to GitHub for analysis"
echo "  git add $DIAG_DIR"
echo "  git commit -m 'Signal diagnostics: $TIMESTAMP'"
echo "  git push origin main"
echo ""
