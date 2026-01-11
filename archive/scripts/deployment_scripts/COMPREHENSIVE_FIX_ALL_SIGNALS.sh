#!/bin/bash
# COMPREHENSIVE FIX FOR ALL 19 SIGNAL COMPONENTS
# Checks everything, identifies issues, and provides fixes
# Based on MEMORY_BANK.md and diagnostic findings

set +e
cd ~/stock-bot

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FIX_DIR="comprehensive_fix_${TIMESTAMP}"
mkdir -p "$FIX_DIR"

echo "=========================================="
echo "COMPREHENSIVE SIGNAL & LEARNING FIX"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# STEP 1: Check which signal components are being logged
echo "[STEP 1] Checking signal components in attribution.jsonl..."
python3 << 'PYEOF' > "$FIX_DIR/signal_components_logged.json" 2>&1
import json
from pathlib import Path
from collections import Counter

attribution_file = Path("logs/attribution.jsonl")
results = {
    "total_entries": 0,
    "entries_with_components": 0,
    "components_found": [],
    "component_frequency": {},
    "sample_entry": None
}

if attribution_file.exists():
    try:
        with open(attribution_file, "r") as f:
            lines = [l for l in f if l.strip()]
            results["total_entries"] = len(lines)
            
            component_counter = Counter()
            sample_with_components = None
            
            for line in lines[-100:]:  # Check last 100 entries
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "attribution":
                        context = entry.get("context", {})
                        components = context.get("components", {})
                        
                        if components:
                            results["entries_with_components"] += 1
                            if not sample_with_components:
                                sample_with_components = {
                                    "symbol": entry.get("symbol"),
                                    "components_count": len(components),
                                    "component_names": list(components.keys())[:10]
                                }
                            
                            for comp_name in components.keys():
                                component_counter[comp_name] += 1
                except:
                    pass
            
            results["components_found"] = sorted(list(component_counter.keys()))
            results["component_frequency"] = dict(component_counter.most_common())
            results["sample_entry"] = sample_with_components
    except Exception as e:
        results["error"] = str(e)

print(json.dumps(results, indent=2))
PYEOF

echo "✅ Signal components logged analysis complete"
echo ""

# STEP 2: Check enrichment service status
echo "[STEP 2] Checking enrichment service..."
python3 << 'PYEOF' > "$FIX_DIR/enrichment_service_status.json" 2>&1
import json
import subprocess
from pathlib import Path

results = {
    "service_running": False,
    "service_pid": None,
    "service_file_exists": Path("cache_enrichment_service.py").exists(),
    "enrichment_in_main": False,
    "cache_has_enriched_data": False
}

# Check if service is running
try:
    proc = subprocess.run(["pgrep", "-f", "cache_enrichment"], capture_output=True, timeout=2)
    if proc.returncode == 0:
        pids = proc.stdout.decode().strip().split('\n')
        if pids and pids[0]:
            results["service_running"] = True
            results["service_pid"] = int(pids[0])
except:
    pass

# Check if main.py calls enrichment
try:
    main_code = Path("main.py").read_text(encoding='utf-8', errors='ignore')
    results["enrichment_in_main"] = "enrich_signal" in main_code or "uw_enrich" in main_code
except:
    pass

# Check if cache has enriched data
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    try:
        cache_data = json.loads(cache_file.read_text())
        sample_symbol = [k for k in cache_data.keys() if not k.startswith("_")][0] if cache_data else None
        if sample_symbol:
            symbol_data = cache_data.get(sample_symbol, {})
            if isinstance(symbol_data, str):
                try:
                    symbol_data = json.loads(symbol_data)
                except:
                    symbol_data = {}
            
            # Check for enriched signals
            enriched_signals = [
                "greeks_gamma", "etf_flow", "market_tide", "oi_change",
                "iv_rank", "ftd_pressure", "congress", "institutional"
            ]
            found_enriched = [sig for sig in enriched_signals if symbol_data.get(sig) not in (None, 0, 0.0, "", [])]
            results["cache_has_enriched_data"] = len(found_enriched) > 0
            results["enriched_signals_found"] = found_enriched
    except Exception as e:
        results["cache_error"] = str(e)

print(json.dumps(results, indent=2))
PYEOF

echo "✅ Enrichment service check complete"
echo ""

# STEP 3: Check UW daemon and cache freshness
echo "[STEP 3] Checking UW daemon and cache..."
python3 << 'PYEOF' > "$FIX_DIR/uw_daemon_status.json" 2>&1
import json
import subprocess
import time
from pathlib import Path

results = {
    "uw_daemon_running": False,
    "uw_daemon_pid": None,
    "cache_exists": False,
    "cache_age_sec": None,
    "cache_symbols": 0
}

# Check UW daemon
try:
    proc = subprocess.run(["pgrep", "-f", "uw.*daemon|uw_flow_daemon|uw_integration"], 
                         capture_output=True, timeout=2)
    if proc.returncode == 0:
        pids = proc.stdout.decode().strip().split('\n')
        if pids and pids[0]:
            results["uw_daemon_running"] = True
            results["uw_daemon_pid"] = int(pids[0])
except:
    pass

# Check cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    results["cache_exists"] = True
    results["cache_age_sec"] = time.time() - cache_file.stat().st_mtime
    try:
        cache_data = json.loads(cache_file.read_text())
        results["cache_symbols"] = len([k for k in cache_data.keys() if not k.startswith("_")])
    except:
        pass

print(json.dumps(results, indent=2))
PYEOF

echo "✅ UW daemon check complete"
echo ""

# STEP 4: Create comprehensive analysis and fix recommendations
echo "[STEP 4] Creating comprehensive analysis..."
FIX_DIR_ABS=$(cd "$FIX_DIR" && pwd)
DIAG_DIR_ABS=$(cd "$(ls -td signal_diagnostics_* 2>/dev/null | head -1)" 2>/dev/null && pwd 2>/dev/null || echo "")
# Use the actual working directory as base
WORK_DIR=$(pwd)
python3 << PYEOF > "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" 2>&1
import json
import os
from pathlib import Path

# Load all diagnostic data - use working directory + relative path (most reliable)
work_dir = Path("${WORK_DIR}")
fix_dir = work_dir / "${FIX_DIR}"

# Check if fix_dir exists
if not fix_dir.exists():
    # Try absolute path
    fix_dir_abs_str = "${FIX_DIR_ABS}"
    if fix_dir_abs_str and not fix_dir_abs_str.startswith('$'):
        fix_dir = Path(fix_dir_abs_str)
    else:
        # Last resort: use current directory
        fix_dir = Path("${FIX_DIR}")

diag_dir_str = "${DIAG_DIR_ABS}"
diag_dir = Path(diag_dir_str) if diag_dir_str and diag_dir_str and not diag_dir_str.startswith('$') else None

analysis = {
    "timestamp": "$TIMESTAMP",
    "overall_status": "unknown",
    "issues": [],
    "fixes_needed": [],
    "signal_components": {},
    "enrichment": {},
    "uw_daemon": {},
    "learning_engine": {}
}

try:
    # Debug: print what we're looking for
    import sys
    print(f"DEBUG: fix_dir = {fix_dir}", file=sys.stderr)
    print(f"DEBUG: fix_dir.exists() = {fix_dir.exists()}", file=sys.stderr)
    
    # Load signal components logged
    signal_file = fix_dir / "signal_components_logged.json"
    print(f"DEBUG: signal_file = {signal_file}", file=sys.stderr)
    print(f"DEBUG: signal_file.exists() = {signal_file.exists()}", file=sys.stderr)
    if not signal_file.exists():
        raise FileNotFoundError(f"Signal components file not found: {signal_file}")
    logged_data = json.loads(signal_file.read_text())
    analysis["signal_components"] = {
        "total_logged": len(logged_data.get("components_found", [])),
        "components_list": logged_data.get("components_found", []),
        "component_frequency": logged_data.get("component_frequency", {}),
        "entries_with_components": logged_data.get("entries_with_components", 0),
        "total_entries": logged_data.get("total_entries", 0)
    }
    
    # Load enrichment status
    enrichment_file = fix_dir / "enrichment_service_status.json"
    if not enrichment_file.exists():
        raise FileNotFoundError(f"Enrichment status file not found: {enrichment_file}")
    enrichment_data = json.loads(enrichment_file.read_text())
    analysis["enrichment"] = {
        "service_running": enrichment_data.get("service_running", False),
        "service_file_exists": enrichment_data.get("service_file_exists", False),
        "enrichment_in_main": enrichment_data.get("enrichment_in_main", False),
        "cache_has_enriched_data": enrichment_data.get("cache_has_enriched_data", False),
        "enriched_signals_found": enrichment_data.get("enriched_signals_found", [])
    }
    
    # Load UW daemon status
    uw_file = fix_dir / "uw_daemon_status.json"
    if not uw_file.exists():
        raise FileNotFoundError(f"UW daemon status file not found: {uw_file}")
    uw_data = json.loads(uw_file.read_text())
    analysis["uw_daemon"] = {
        "running": uw_data.get("uw_daemon_running", False),
        "cache_exists": uw_data.get("cache_exists", False),
        "cache_age_minutes": (uw_data.get("cache_age_sec", 999999) / 60) if uw_data.get("cache_age_sec") else None,
        "cache_symbols": uw_data.get("cache_symbols", 0)
    }
    
    # Load learning integration from fixed summary
    if diag_dir and (diag_dir / "COMPREHENSIVE_SUMMARY_FIXED.json").exists():
        summary = json.loads((diag_dir / "COMPREHENSIVE_SUMMARY_FIXED.json").read_text())
        analysis["learning_engine"] = summary.get("learning_integration", {})
    
    # Identify issues
    if not analysis["uw_daemon"]["running"]:
        analysis["issues"].append("CRITICAL: UW daemon not running - cache won't update")
        analysis["fixes_needed"].append("Start UW daemon: python uw_flow_daemon.py or python uw_integration_full.py")
    
    if analysis["uw_daemon"]["cache_age_minutes"] and analysis["uw_daemon"]["cache_age_minutes"] > 10:
        analysis["issues"].append(f"UW cache is stale ({analysis['uw_daemon']['cache_age_minutes']:.1f} minutes old)")
        analysis["fixes_needed"].append("Restart UW daemon to refresh cache")
    
    if not analysis["enrichment"]["service_running"]:
        analysis["issues"].append("Enrichment service not running - enriched signals won't be populated")
        analysis["fixes_needed"].append("Start enrichment service: python cache_enrichment_service.py")
    
    if not analysis["enrichment"]["cache_has_enriched_data"]:
        analysis["issues"].append("Cache has no enriched signal data - enrichment service may not be working")
        analysis["fixes_needed"].append("Check enrichment service logs: tail -50 logs/cache_enrichment.log")
    
    if analysis["signal_components"]["total_logged"] < 10:
        analysis["issues"].append(f"Only {analysis['signal_components']['total_logged']} signal components being logged (expected ~19)")
        analysis["fixes_needed"].append("Verify all signal components are included in context.components when logging attribution")
    
    # Overall status
    critical_issues = [i for i in analysis["issues"] if "CRITICAL" in i]
    if len(critical_issues) > 0:
        analysis["overall_status"] = "critical"
    elif len(analysis["issues"]) == 0:
        analysis["overall_status"] = "healthy"
    elif len(analysis["issues"]) <= 2:
        analysis["overall_status"] = "degraded"
    else:
        analysis["overall_status"] = "critical"
        
except Exception as e:
    import traceback
    analysis["error"] = str(e)
    analysis["traceback"] = traceback.format_exc()

print(json.dumps(analysis, indent=2))
PYEOF

echo "✅ Comprehensive analysis complete"
echo ""

# STEP 5: Display summary
echo "=========================================="
echo "COMPREHENSIVE ANALYSIS SUMMARY"
echo "=========================================="
echo ""
cat "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Status: {d.get('overall_status', 'unknown').upper()}\")
print(f\"\\nSignal Components:\")
print(f\"  - Components being logged: {d.get('signal_components', {}).get('total_logged', 0)}\")
print(f\"  - Components list: {', '.join(d.get('signal_components', {}).get('components_list', [])[:10])}\")
print(f\"\\nEnrichment Service:\")
print(f\"  - Running: {d.get('enrichment', {}).get('service_running', False)}\")
print(f\"  - Cache has enriched data: {d.get('enrichment', {}).get('cache_has_enriched_data', False)}\")
print(f\"\\nUW Daemon:\")
print(f\"  - Running: {d.get('uw_daemon', {}).get('running', False)}\")
print(f\"  - Cache age: {d.get('uw_daemon', {}).get('cache_age_minutes', 0):.1f} minutes\")
print(f\"\\nIssues: {len(d.get('issues', []))}\")
if d.get('issues'):
    for issue in d.get('issues', []):
        print(f\"  - {issue}\")
print(f\"\\nFixes Needed:\")
if d.get('fixes_needed'):
    for fix in d.get('fixes_needed', []):
        print(f\"  - {fix}\")
" 2>/dev/null

echo ""
echo "All analysis saved to: $FIX_DIR"
echo ""
echo "Next: Review $FIX_DIR/COMPREHENSIVE_ANALYSIS.json for detailed findings"
echo ""
