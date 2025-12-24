#!/bin/bash
# Debug the analysis script to see what's going wrong

cd ~/stock-bot

FIX_DIR=$(ls -td comprehensive_fix_* | head -1)

if [ -z "$FIX_DIR" ]; then
    echo "❌ No fix directory found"
    exit 1
fi

echo "Debugging analysis for: $FIX_DIR"
echo ""

# Check if intermediate files exist
echo "[1] Checking intermediate files..."
for file in "signal_components_logged.json" "enrichment_service_status.json" "uw_daemon_status.json"; do
    if [ -f "$FIX_DIR/$file" ]; then
        echo "✅ $file exists"
        echo "   First 10 lines:"
        head -10 "$FIX_DIR/$file" | python3 -m json.tool 2>/dev/null || head -10 "$FIX_DIR/$file"
        echo ""
    else
        echo "❌ $file MISSING"
        echo ""
    fi
done

# Check the analysis file
echo "[2] Checking COMPREHENSIVE_ANALYSIS.json..."
if [ -f "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" ]; then
    echo "✅ Analysis file exists"
    echo ""
    echo "Full contents:"
    cat "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" | python3 -m json.tool 2>&1
    echo ""
    
    # Check for errors
    if grep -q '"error"' "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json"; then
        echo "⚠️  ERROR FOUND:"
        cat "$FIX_DIR/COMPREHENSIVE_ANALYSIS.json" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Error:', d.get('error', 'No error'))
    if 'traceback' in d:
        print('Traceback:', d['traceback'][:1000])
except:
    print('Could not parse JSON')
" 2>/dev/null
    fi
else
    echo "❌ Analysis file MISSING"
fi

echo ""
echo "[3] Checking actual service status..."
echo "UW daemon:"
pgrep -f "uw.*daemon|uw_flow_daemon" && echo "  ✅ Running (PID: $(pgrep -f 'uw.*daemon|uw_flow_daemon'))" || echo "  ❌ NOT running"

echo "Enrichment:"
pgrep -f "cache_enrichment" && echo "  ✅ Running (PID: $(pgrep -f cache_enrichment))" || echo "  ❌ NOT running"

echo ""
echo "[4] Checking attribution.jsonl..."
if [ -f "logs/attribution.jsonl" ]; then
    echo "✅ File exists"
    echo "Total lines: $(wc -l < logs/attribution.jsonl)"
    echo ""
    echo "Last 5 entries with 'components':"
    tail -100 logs/attribution.jsonl | python3 << 'PYEOF'
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
                if count <= 5:
                    print(f"  Entry {count}: {entry.get('symbol', 'N/A')} - {len(components)} components: {', '.join(list(components.keys())[:8])}")
    except Exception as e:
        pass
if count == 0:
    print("  ⚠️  No entries with components found in last 100 lines")
PYEOF
else
    echo "❌ File not found"
fi
