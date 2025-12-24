#!/bin/bash
# Analyze the latest diagnostic collection

cd ~/stock-bot

# Find latest diagnostics directory
LATEST_DIAG=$(ls -td diagnostics_* 2>/dev/null | head -1)

if [ -z "$LATEST_DIAG" ]; then
    echo "❌ No diagnostics directory found"
    exit 1
fi

echo "=========================================="
echo "ANALYZING DIAGNOSTICS: $LATEST_DIAG"
echo "=========================================="
echo ""

echo "[1] Cache Analysis:"
if [ -f "$LATEST_DIAG/cache_analysis.json" ]; then
    cat "$LATEST_DIAG/cache_analysis.json" | python3 -m json.tool
else
    echo "⚠️  Cache analysis not found"
fi

echo ""
echo "[2] Log Analysis:"
if [ -f "$LATEST_DIAG/log_analysis.json" ]; then
    cat "$LATEST_DIAG/log_analysis.json" | python3 -m json.tool
else
    echo "⚠️  Log analysis not found"
fi

echo ""
echo "[3] Daemon Log (last 50 lines):"
if [ -f "$LATEST_DIAG/uw_daemon_recent.log" ]; then
    tail -50 "$LATEST_DIAG/uw_daemon_recent.log"
else
    echo "⚠️  Daemon log not found"
fi

echo ""
echo "[4] Debug Log:"
if [ -f "$LATEST_DIAG/debug.log" ]; then
    if [ -s "$LATEST_DIAG/debug.log" ]; then
        echo "Debug log contents:"
        cat "$LATEST_DIAG/debug.log"
        echo ""
        echo "Parsing JSON entries:"
        python3 << PYEOF
import json
from pathlib import Path
import sys

log_file = Path("$LATEST_DIAG/debug.log")
if log_file.exists():
    events = []
    with log_file.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception as e:
                print(f"  Line {line_num} parse error: {e}")
                print(f"    Content: {line[:100]}")
    
    print(f"\nTotal valid events: {len(events)}")
    if events:
        print("\nAll events:")
        for e in events:
            print(f"  [{e.get('hypothesisId', '?')}] {e.get('location', 'unknown')}: {e.get('message', '')}")
            data = e.get('data', {})
            if data:
                print(f"      Data: {data}")
else:
    print("Log file not found")
PYEOF
    else
        echo "⚠️  Debug log is empty"
    fi
else
    echo "⚠️  Debug log not found"
fi

echo ""
echo "[5] Smart Poller State:"
if [ -f "$LATEST_DIAG/smart_poller_state.json" ]; then
    cat "$LATEST_DIAG/smart_poller_state.json" | python3 -m json.tool
else
    echo "⚠️  Smart poller state not found"
fi

echo ""
echo "[6] Summary of Issues:"
python3 << PYEOF
import json
from pathlib import Path
import sys

diag_dir = Path("$LATEST_DIAG")

issues = []
warnings = []

# Check cache
cache_file = diag_dir / "cache_analysis.json"
if cache_file.exists():
    cache_data = json.loads(cache_file.read_text())
    if not cache_data.get("cache_exists"):
        issues.append("❌ Cache file does not exist")
    else:
        if not cache_data.get("market_tide", {}).get("has_data"):
            warnings.append("⚠️  market_tide not in cache")
        if not cache_data.get("top_net_impact", {}).get("has_data"):
            warnings.append("⚠️  top_net_impact not in cache")
        
        sample = cache_data.get("sample_data", {})
        if sample:
            missing = []
            if not sample.get("has_greeks"):
                missing.append("greeks")
            if not sample.get("has_iv_rank"):
                missing.append("iv_rank")
            if not sample.get("has_oi_change"):
                missing.append("oi_change")
            if not sample.get("has_etf_flow"):
                missing.append("etf_flow")
            if not sample.get("has_ftd_pressure"):
                missing.append("ftd_pressure")
            if missing:
                warnings.append(f"⚠️  Missing endpoints in sample ticker: {', '.join(missing)}")

# Check log analysis
log_analysis = diag_dir / "log_analysis.json"
if log_analysis.exists():
    log_data = json.loads(log_analysis.read_text())
    endpoint_activity = log_data.get("endpoint_activity", {})
    if not endpoint_activity:
        issues.append("❌ No endpoint polling activity detected in logs")
    else:
        expected_endpoints = ["market_tide", "top_net_impact", "option_flow", "dark_pool", "greek_exposure", "greeks", "iv_rank", "oi_change", "etf_flow", "shorts_ftds", "max_pain"]
        missing_endpoints = [ep for ep in expected_endpoints if ep not in endpoint_activity]
        if missing_endpoints:
            warnings.append(f"⚠️  Endpoints not polled: {', '.join(missing_endpoints)}")
    
    if log_data.get("errors"):
        issues.append(f"❌ Found {len(log_data['errors'])} errors in logs")

# Check debug log
debug_log = diag_dir / "debug.log"
if debug_log.exists():
    if debug_log.stat().st_size < 50:
        warnings.append("⚠️  Debug log is very small - instrumentation may not be working")
else:
    issues.append("❌ Debug log file not created")

if issues:
    print("\nISSUES:")
    for issue in issues:
        print(f"  {issue}")

if warnings:
    print("\nWARNINGS:")
    for warning in warnings:
        print(f"  {warning}")

if not issues and not warnings:
    print("✅ No issues detected")
PYEOF
