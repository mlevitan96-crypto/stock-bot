#!/bin/bash
# Fix git issue, verify analysis, and start missing services

set +e
cd ~/stock-bot

echo "=========================================="
echo "FIX GIT & START SERVICES"
echo "=========================================="
echo ""

# STEP 1: Fix git (pull first, then push)
echo "[STEP 1] Fixing git..."
git pull origin main --no-rebase 2>&1 | head -20
if [ $? -eq 0 ]; then
    echo "✅ Git pull successful"
    git push origin main 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Git push successful"
    else
        echo "⚠️  Git push failed, but continuing..."
    fi
else
    echo "⚠️  Git pull had issues, trying rebase..."
    git pull origin main --rebase 2>&1 | head -20
    if [ $? -eq 0 ]; then
        git push origin main 2>&1
    fi
fi
echo ""

# STEP 2: Check what the analysis actually found
echo "[STEP 2] Checking analysis results..."
FIX_DIR=$(ls -td comprehensive_fix_* | head -1)
if [ -n "$FIX_DIR" ] && [ -f "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" ]; then
    echo "Analysis file exists: $FIX_DIR/COMPREHENSIVE_ANALYSIS.json"
    echo ""
    echo "Actual analysis data:"
    cat "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" | python3 -m json.tool 2>/dev/null | head -50
    echo ""
    
    # Check if there was an error
    if grep -q '"error"' "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json"; then
        echo "⚠️  Analysis had an error - checking details..."
        cat "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('error', 'No error message'))" 2>/dev/null
    fi
else
    echo "⚠️  Analysis file not found"
fi
echo ""

# STEP 3: Check actual signal components logged
echo "[STEP 3] Checking signal components in attribution.jsonl..."
if [ -f "logs/attribution.jsonl" ]; then
    echo "Last 3 entries with components:"
    tail -20 logs/attribution.jsonl | python3 << 'PYEOF'
import sys, json
count = 0
for line in sys.stdin:
    if not line.strip():
        continue
    try:
        entry = json.loads(line)
        if entry.get("type") == "attribution":
            context = entry.get("context", {})
            components = context.get("components", {})
            if components:
                count += 1
                if count <= 3:
                    print(f"\nEntry {count}:")
                    print(f"  Symbol: {entry.get('symbol', 'N/A')}")
                    print(f"  Components ({len(components)}): {', '.join(list(components.keys())[:10])}")
    except:
        pass
PYEOF
else
    echo "⚠️  attribution.jsonl not found"
fi
echo ""

# STEP 4: Check what processes are actually running
echo "[STEP 4] Checking running processes..."
echo "UW-related processes:"
ps aux | grep -E "uw|daemon|enrichment" | grep -v grep | head -10
echo ""

# STEP 5: Check if services need to be started
echo "[STEP 5] Service status check..."
UW_DAEMON_RUNNING=$(pgrep -f "uw.*daemon|uw_flow_daemon|uw_integration" | wc -l)
ENRICHMENT_RUNNING=$(pgrep -f "cache_enrichment" | wc -l)

echo "UW Daemon processes: $UW_DAEMON_RUNNING"
echo "Enrichment processes: $ENRICHMENT_RUNNING"
echo ""

if [ "$UW_DAEMON_RUNNING" -eq 0 ]; then
    echo "⚠️  UW daemon NOT running"
    echo "   To start: python3 uw_flow_daemon.py (or uw_integration_full.py)"
    echo "   Or check: python3 -c \"from uw_integration_full import *; print('Module OK')\""
fi

if [ "$ENRICHMENT_RUNNING" -eq 0 ]; then
    echo "⚠️  Enrichment service NOT running"
    echo "   To start: python3 cache_enrichment_service.py"
fi

# STEP 6: Start missing services if needed
echo "[STEP 6] Starting missing services..."
if [ "$UW_DAEMON_RUNNING" -eq 0 ]; then
    echo "Starting UW daemon..."
    cd ~/stock-bot
    source venv/bin/activate 2>/dev/null || true
    nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
    sleep 2
    if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
        echo "✅ UW daemon started (PID: $(pgrep -f 'uw.*daemon|uw_flow_daemon'))"
    else
        echo "⚠️  UW daemon may have failed to start - check logs/uw_daemon.log"
    fi
fi

if [ "$ENRICHMENT_RUNNING" -eq 0 ]; then
    echo "Starting enrichment service (continuous mode)..."
    cd ~/stock-bot
    source venv/bin/activate 2>/dev/null || true
    nohup python3 cache_enrichment_service.py --continuous > logs/enrichment.log 2>&1 &
    sleep 2
    if pgrep -f "cache_enrichment" > /dev/null; then
        echo "✅ Enrichment service started (PID: $(pgrep -f cache_enrichment))"
    else
        echo "⚠️  Enrichment service may have failed to start - check logs/enrichment.log"
        echo "   First 20 lines of log:"
        tail -20 logs/enrichment.log 2>/dev/null | head -20
    fi
fi

echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo "1. Wait 2-3 minutes for services to populate cache"
echo "2. Re-run diagnostics: ./COMPREHENSIVE_FIX_ALL_SIGNALS.sh"
echo "3. Check service logs:"
echo "   - tail -f logs/uw_daemon.log"
echo "   - tail -f logs/enrichment.log"
echo ""
