#!/bin/bash
# Verify dashboard improvements are working

cd ~/stock-bot

echo "=========================================="
echo "CHECKING DASHBOARD IMPROVEMENTS"
echo "=========================================="
echo ""

echo "1. Testing SRE endpoint structure..."
echo "----------------------------------------"
SRE_RESPONSE=$(curl -s http://localhost:5000/api/sre/health 2>/dev/null)

# Check for new fields
if echo "$SRE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Check for new fields we added
checks = []
checks.append(('signal_components_healthy' in data, 'signal_components_healthy'))
checks.append(('signal_components_total' in data, 'signal_components_total'))
checks.append(('uw_api_healthy_count' in data, 'uw_api_healthy_count'))
checks.append(('uw_api_total_count' in data, 'uw_api_total_count'))
checks.append(('comprehensive_learning' in data, 'comprehensive_learning'))

# Check signal_components structure
if 'signal_components' in data:
    signals = data['signal_components']
    if signals:
        first_signal = list(signals.values())[0]
        checks.append(('signals_generated_1h' in first_signal, 'signals[].signals_generated_1h'))
        checks.append(('found_in_symbols' in first_signal, 'signals[].found_in_symbols'))
        checks.append(('signal_type' in first_signal, 'signals[].signal_type'))
        checks.append(('data_freshness_sec' in first_signal, 'signals[].data_freshness_sec'))

for passed, name in checks:
    status = '✅' if passed else '❌'
    print(f'{status} {name}')
" 2>/dev/null); then
    echo "$SRE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Show summary
print(f\"Overall Health: {data.get('overall_health', 'unknown')}\")
print(f\"Signal Components: {data.get('signal_components_healthy', 0)}/{data.get('signal_components_total', 0)} healthy\")
print(f\"UW APIs: {data.get('uw_api_healthy_count', 0)}/{data.get('uw_api_total_count', 0)} healthy\")
print(f\"Learning Engine: {'running' if data.get('comprehensive_learning', {}).get('running') else 'idle'}\")
"
else
    echo "⚠️  Could not parse response"
fi
echo ""

echo "2. Checking signal component freshness..."
echo "----------------------------------------"
echo "$SRE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
signals = data.get('signal_components', {})
if signals:
    print('Signal Freshness:')
    for name, health in list(signals.items())[:5]:  # First 5 signals
        freshness = health.get('data_freshness_sec')
        status = health.get('status', 'unknown')
        if freshness is not None:
            if freshness < 300:
                freshness_str = f'{freshness:.0f}s (fresh ✅)'
            elif freshness < 600:
                freshness_str = f'{freshness:.0f}s (moderate ⚠️)'
            else:
                freshness_str = f'{freshness:.0f}s (stale ❌)'
        else:
            freshness_str = 'N/A'
        print(f'  {name}: {status} - Freshness: {freshness_str}')
else:
    print('  No signal components found')
" 2>/dev/null
echo ""

echo "3. Dashboard accessibility..."
echo "----------------------------------------"
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null)
if [ "$DASHBOARD_STATUS" = "200" ]; then
    echo "✅ Dashboard accessible (HTTP $DASHBOARD_STATUS)"
    IP=$(hostname -I | awk '{print $1}')
    echo "   Access at: http://$IP:5000"
else
    echo "❌ Dashboard not accessible (HTTP $DASHBOARD_STATUS)"
fi
echo ""

echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Open dashboard in browser: http://$(hostname -I | awk '{print $1}'):5000"
echo "2. Click 'SRE Monitoring' tab"
echo "3. Verify you see:"
echo "   ✅ Signal components with actual freshness times (not 0s)"
echo "   ✅ Learning Engine section at bottom"
echo "   ✅ Signal metadata (found_in_symbols, signal_type, etc.)"
echo "4. Hard refresh if needed: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo ""





