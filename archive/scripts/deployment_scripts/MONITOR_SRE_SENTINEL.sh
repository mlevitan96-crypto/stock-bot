#!/bin/bash
# Monitor SRE Sentinel Health Checks
# Better than tail -f for JSON files

echo "=========================================="
echo "SRE Sentinel Monitoring"
echo "=========================================="
echo ""

# Method 1: Watch the metrics file (refreshes every 2 seconds)
echo "Method 1: Watch metrics file (Ctrl+C to exit)"
echo "----------------------------------------"
watch -n 2 "cat state/sre_metrics.json 2>/dev/null | python3 -m json.tool || echo 'File not found yet'"
echo ""

# Method 2: Monitor with timestamp comparison
echo "Method 2: Monitor metrics with timestamp (better for changes)"
echo "----------------------------------------"
PREV_TIME=0
while true; do
    if [ -f "state/sre_metrics.json" ]; then
        CURRENT_TIME=$(python3 -c "import json, os; f='state/sre_metrics.json'; print(os.path.getmtime(f) if os.path.exists(f) else 0)" 2>/dev/null || echo "0")
        if [ "$CURRENT_TIME" != "$PREV_TIME" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Metrics updated:"
            python3 -c "
import json
from datetime import datetime
try:
    with open('state/sre_metrics.json') as f:
        m = json.load(f)
    print(f\"  Logic Heartbeat: {datetime.fromtimestamp(m.get('logic_heartbeat', 0)).strftime('%Y-%m-%d %H:%M:%S') if m.get('logic_heartbeat') else 'Never'}\")
    print(f\"  Mock Signal Success: {m.get('mock_signal_success_pct', 0):.1f}%\")
    print(f\"  Parser Health: {m.get('parser_health_index', 0):.1f}%\")
    print(f\"  Auto-Fix Count: {m.get('auto_fix_count', 0)}\")
    if m.get('last_mock_signal_score') is not None:
        print(f\"  Last Mock Signal Score: {m.get('last_mock_signal_score', 0):.2f}\")
except Exception as e:
    print(f\"  Error: {e}\")
"
            PREV_TIME=$CURRENT_TIME
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for metrics file to be created..."
    fi
    sleep 5
done
