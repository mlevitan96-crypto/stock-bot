#!/bin/bash
# Quick check of SRE Sentinel status

echo "=========================================="
echo "SRE Sentinel Status Check"
echo "=========================================="
echo ""

# Check if metrics file exists
if [ -f "state/sre_metrics.json" ]; then
    echo "✅ Metrics file exists"
    echo ""
    echo "Current Metrics:"
    python3 -c "
import json
from datetime import datetime
from pathlib import Path

try:
    with open('state/sre_metrics.json') as f:
        m = json.load(f)
    
    heartbeat = m.get('logic_heartbeat', 0)
    if heartbeat:
        heartbeat_dt = datetime.fromtimestamp(heartbeat)
        age_sec = (datetime.now().timestamp() - heartbeat)
        age_min = int(age_sec / 60)
        print(f\"  Logic Heartbeat: {heartbeat_dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_min}m ago)\")
    else:
        print(f\"  Logic Heartbeat: Never\")
    
    success_pct = m.get('mock_signal_success_pct', 100.0)
    health_color = '🟢' if success_pct >= 95 else '🟡' if success_pct >= 80 else '🔴'
    print(f\"  Mock Signal Success: {health_color} {success_pct:.1f}%\")
    
    parser_health = m.get('parser_health_index', 100.0)
    health_color = '🟢' if parser_health >= 95 else '🟡' if parser_health >= 80 else '🔴'
    print(f\"  Parser Health Index: {health_color} {parser_health:.1f}%\")
    
    print(f\"  Auto-Fix Count: {m.get('auto_fix_count', 0)}\")
    
    last_score = m.get('last_mock_signal_score')
    if last_score is not None:
        score_status = '✅' if last_score >= 4.0 else '❌'
        print(f\"  Last Mock Signal Score: {score_status} {last_score:.2f}\")
        if m.get('last_mock_signal_time'):
            print(f\"  Last Mock Signal Time: {m.get('last_mock_signal_time')}\")
    
except Exception as e:
    print(f\"  ❌ Error reading metrics: {e}\")
"
else
    echo "⚠️  Metrics file does not exist yet"
    echo "   This is normal if mock signal injection hasn't run yet (runs every 15 min)"
fi

echo ""
echo "Recent RCA Fixes:"
if [ -f "state/sre_rca_fixes.jsonl" ]; then
    tail -5 state/sre_rca_fixes.jsonl | python3 -c "
import sys, json
from datetime import datetime

for line in sys.stdin:
    try:
        fix = json.loads(line.strip())
        time_str = fix.get('time', '') or datetime.fromtimestamp(fix.get('timestamp', 0)).isoformat()
        status = fix.get('overall_status', 'UNKNOWN')
        trigger = fix.get('trigger', 'unknown')
        fixes_applied = fix.get('fixes_applied', [])
        print(f\"  [{time_str[:19]}] {status} (trigger: {trigger})\")
        if fixes_applied:
            print(f\"    Fixes: {', '.join(fixes_applied)}\")
    except:
        pass
" || echo "  (file exists but no valid entries)"
else
    echo "  No RCA fixes logged yet"
fi

echo ""
echo "Mock Signal Injection Logs (from main.py output):"
echo "  (Check supervisor logs for [MOCK-SIGNAL] entries)"
echo "  Run: journalctl -u trading-bot.service -f | grep MOCK-SIGNAL"
