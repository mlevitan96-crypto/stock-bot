#!/bin/bash
# Fix SRE dashboard and bot startup issues

echo "=========================================="
echo "FIXING SRE DASHBOARD AND BOT"
echo "=========================================="
echo ""

# 1. Install missing dependencies
echo "1. Installing missing Python packages..."
echo "----------------------------------------"
pip3 install alpaca-trade-api 2>&1 | tail -5
echo ""

# 2. Test SRE monitoring directly
echo "2. Testing SRE monitoring module..."
echo "----------------------------------------"
python3 -c "
try:
    from sre_monitoring import get_sre_health
    health = get_sre_health()
    print('✅ SRE monitoring works!')
    print(f'   Overall health: {health.get(\"overall_health\", \"unknown\")}')
    print(f'   Signal components: {len(health.get(\"signal_components\", {}))}')
    print(f'   API endpoints: {len(health.get(\"uw_api_endpoints\", {}))}')
except Exception as e:
    print(f'❌ SRE monitoring error: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

# 3. Test dashboard SRE endpoint
echo "3. Testing dashboard SRE endpoint..."
echo "----------------------------------------"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from dashboard import api_sre_health
    from flask import Flask
    app = Flask(__name__)
    app.add_url_rule('/api/sre/health', 'api_sre_health', api_sre_health, methods=['GET'])
    
    with app.test_client() as client:
        resp = client.get('/api/sre/health')
        if resp.status_code == 200:
            data = resp.get_json()
            print('✅ Dashboard SRE endpoint works!')
            print(f'   Status: {resp.status_code}')
            print(f'   Overall health: {data.get(\"overall_health\", \"unknown\")}')
        else:
            print(f'❌ Dashboard SRE endpoint returned {resp.status_code}')
            print(f'   Response: {resp.get_data(as_text=True)[:200]}')
except Exception as e:
    print(f'❌ Dashboard SRE endpoint error: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

# 4. Check if dashboard is running
echo "4. Checking dashboard status..."
echo "----------------------------------------"
DASHBOARD_PID=$(ps aux | grep "python.*dashboard.py" | grep -v grep | awk '{print $2}')
if [ -z "$DASHBOARD_PID" ]; then
    echo "⚠️  Dashboard is not running"
    echo "   Start it with: python3 dashboard.py"
else
    echo "✅ Dashboard is running (PID: $DASHBOARD_PID)"
    echo "   Access at: http://localhost:5000"
fi
echo ""

# 5. Check if main bot can start
echo "5. Testing main bot imports..."
echo "----------------------------------------"
python3 -c "
try:
    import alpaca_trade_api as tradeapi
    print('✅ alpaca_trade_api imported successfully')
except ImportError as e:
    print(f'❌ Missing alpaca_trade_api: {e}')
    print('   Run: pip3 install alpaca-trade-api')
"
echo ""

# 6. Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. If alpaca_trade_api was missing, restart the bot:"
echo "     screen -dmS trading python3 main.py"
echo ""
echo "  2. If dashboard isn't running, start it:"
echo "     screen -dmS dashboard python3 dashboard.py"
echo ""
echo "  3. Access dashboard at: http://your-droplet-ip:5000"
echo "     - Click 'SRE Monitoring' tab"
echo "     - Check browser console (F12) for errors"
echo ""
