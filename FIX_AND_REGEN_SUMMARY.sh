#!/bin/bash
# Fix and regenerate the comprehensive summary with correct paths
# Also fixes the diagnostic script to properly detect signal components in attribution.jsonl

cd ~/stock-bot
DIAG_DIR=$(ls -td signal_diagnostics_* | head -1)

if [ -z "$DIAG_DIR" ]; then
    echo "❌ No diagnostic directory found"
    exit 1
fi

echo "Fixing summary for: $DIAG_DIR"
echo ""

# First, fix the learning engine status to check context.components instead of signals
echo "[1] Fixing learning engine status check..."
python3 << PYEOF > "$DIAG_DIR/learning_engine_status_FIXED.json" 2>&1
import json
import time
from pathlib import Path

results = {
    "attribution_file": {},
    "comprehensive_learning": {},
    "learning_state": {},
    "recent_trades_with_signals": 0,
    "signal_components_used": []
}

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
                    if entry.get("type") == "attribution":
                        results["recent_trades_with_signals"] += 1
                        
                        # Check context.components (correct location)
                        context = entry.get("context", {})
                        components = context.get("components", {})
                        
                        # Also check direct components (fallback)
                        if not components:
                            components = entry.get("components", {})
                        
                        # Extract all component names that have non-zero values
                        for comp_name, comp_value in components.items():
                            if comp_value not in (None, 0, 0.0, "", []):
                                signal_components_used.add(comp_name)
                except Exception as e:
                    pass
            
            results["attribution_file"] = {
                "exists": True,
                "total_entries": len(lines),
                "recent_entries": len(recent_lines),
                "age_sec": time.time() - attribution_file.stat().st_mtime,
                "signal_components_used": sorted(list(signal_components_used))
            }
            results["signal_components_used"] = sorted(list(signal_components_used))
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

echo "✅ Fixed learning engine status"
echo ""

# Regenerate summary with correct paths and fixed learning data
echo "[2] Regenerating comprehensive summary..."
python3 << PYEOF > "$DIAG_DIR/COMPREHENSIVE_SUMMARY_FIXED.json" 2>&1
import json
from pathlib import Path

DIAG_DIR = "$DIAG_DIR"

summary = {
    "diagnostic_timestamp": "$(date +%Y%m%d_%H%M%S)",
    "overall_status": "unknown",
    "issues": [],
    "recommendations": [],
    "signal_components": {},
    "uw_endpoints": {},
    "learning_integration": {}
}

try:
    signal_analysis = json.loads(Path(f"{DIAG_DIR}/signal_components_analysis.json").read_text())
    learning_status = json.loads(Path(f"{DIAG_DIR}/learning_engine_status_FIXED.json").read_text())
    sre_health = json.loads(Path(f"{DIAG_DIR}/sre_health_full.json").read_text())
    
    # Signal components
    summary["signal_components"] = {
        "total": signal_analysis.get("total_signals", 0),
        "with_data": signal_analysis.get("signals_with_data", 0),
        "without_data": signal_analysis.get("signals_without_data", 0),
        "cache_status": signal_analysis.get("uw_cache_status", {}),
        "healthy_in_sre": sre_health.get("signal_components_healthy", 0),
        "total_in_sre": sre_health.get("signal_components_total", 0),
        "details": signal_analysis.get("signals", {})
    }
    
    # UW endpoints from SRE health (more reliable)
    uw_endpoints = sre_health.get("uw_api_endpoints", {})
    summary["uw_endpoints"] = {
        "total": len(uw_endpoints),
        "healthy": sre_health.get("uw_api_healthy_count", 0),
        "details": uw_endpoints
    }
    
    # Learning integration (using FIXED data)
    summary["learning_integration"] = {
        "attribution_entries": learning_status.get("attribution_file", {}).get("total_entries", 0),
        "signal_components_used": learning_status.get("signal_components_used", []),
        "recent_trades_with_signals": learning_status.get("recent_trades_with_signals", 0),
        "comprehensive_learning_exists": learning_status.get("comprehensive_learning", {}).get("exists", False),
        "comprehensive_learning_entries": learning_status.get("comprehensive_learning", {}).get("entries", 0)
    }
    
    # Identify issues
    if summary["signal_components"]["without_data"] > summary["signal_components"]["with_data"]:
        summary["issues"].append(f"Most signals ({summary['signal_components']['without_data']}/{summary['signal_components']['total']}) have no data in cache")
    
    if len(summary["learning_integration"]["signal_components_used"]) == 0:
        summary["issues"].append("CRITICAL: No signal components found in attribution.jsonl context.components - signals not being logged to learning engine")
    else:
        summary["issues"].append(f"✅ Signal components ARE being logged: {len(summary['learning_integration']['signal_components_used'])} components found")
    
    if summary["learning_integration"]["recent_trades_with_signals"] == 0:
        summary["issues"].append("No recent trades with signal attribution found")
    
    # Recommendations
    cache_age_min = summary["signal_components"]["cache_status"].get("age_minutes", 999)
    if cache_age_min > 10:
        summary["recommendations"].append(f"UW cache is stale ({cache_age_min:.1f} min old) - restart UW daemon")
    
    if summary["signal_components"]["without_data"] > 10:
        summary["recommendations"].append(f"Most enriched signals ({summary['signal_components']['without_data']}) have no data - check enrichment service")
    
    if len(summary["learning_integration"]["signal_components_used"]) == 0:
        summary["recommendations"].append("CRITICAL: Fix attribution logging - ensure context.components includes all signal components")
    else:
        summary["recommendations"].append(f"✅ Learning engine is receiving {len(summary['learning_integration']['signal_components_used'])} signal components")
    
    # Overall status
    critical_issues = [i for i in summary["issues"] if "CRITICAL" in i and "✅" not in i]
    if len(critical_issues) > 0:
        summary["overall_status"] = "critical"
    elif len(summary["issues"]) == 0:
        summary["overall_status"] = "healthy"
    elif len([i for i in summary["issues"] if "✅" not in i]) <= 2:
        summary["overall_status"] = "degraded"
    else:
        summary["overall_status"] = "critical"
        
except Exception as e:
    import traceback
    summary["error"] = str(e)
    summary["traceback"] = traceback.format_exc()

print(json.dumps(summary, indent=2))
PYEOF

echo "✅ Fixed summary created: $DIAG_DIR/COMPREHENSIVE_SUMMARY_FIXED.json"
echo ""
echo "Quick Summary:"
cat "$DIAG_DIR/COMPREHENSIVE_SUMMARY_FIXED.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  Status: {d.get('overall_status', 'unknown')}\")
print(f\"  Signals with data: {d.get('signal_components', {}).get('with_data', 0)}/{d.get('signal_components', {}).get('total', 0)}\")
print(f\"  UW endpoints healthy: {d.get('uw_endpoints', {}).get('healthy', 0)}/{d.get('uw_endpoints', {}).get('total', 0)}\")
print(f\"  Signal components in learning: {len(d.get('learning_integration', {}).get('signal_components_used', []))}\")
print(f\"  Issues: {len([i for i in d.get('issues', []) if '✅' not in i])}\")
print(f\"  Critical Issues: {len([i for i in d.get('issues', []) if 'CRITICAL' in i and '✅' not in i])}\")
if d.get('issues'):
    print(f\"\\n  Issues:\")
    for issue in d.get('issues', []):
        print(f\"    - {issue}\")
if d.get('recommendations'):
    print(f\"\\n  Recommendations:\")
    for rec in d.get('recommendations', []):
        print(f\"    - {rec}\")
" 2>/dev/null

echo ""
echo "View full summary:"
echo "  cat $DIAG_DIR/COMPREHENSIVE_SUMMARY_FIXED.json | python3 -m json.tool"
echo ""
echo "Check signal components in attribution:"
echo "  tail -5 logs/attribution.jsonl | python3 -c \"import sys, json; [print(json.dumps(json.loads(l).get('context', {}).get('components', {}), indent=2)) for l in sys.stdin if l.strip()]\""
