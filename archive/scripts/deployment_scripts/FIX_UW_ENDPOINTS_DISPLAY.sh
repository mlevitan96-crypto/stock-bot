#!/bin/bash
# Fix UW API Endpoints Display on Dashboard
# Ensures the UW API Endpoints section is visible and shows all endpoints

set -e
cd ~/stock-bot

echo "=========================================="
echo "FIXING UW API ENDPOINTS DISPLAY"
echo "=========================================="
echo ""

# 1. Pull latest code
echo "[1] Pulling latest code..."
git pull origin main
echo "✅ Code updated"
echo ""

# 2. Verify changes
echo "[2] Verifying changes..."
if grep -q '"endpoint": h.endpoint' sre_monitoring.py; then
    echo "✅ sre_monitoring.py includes endpoint field"
else
    echo "❌ sre_monitoring.py missing endpoint field"
fi

if grep -q 'console.log.*UW API Endpoints' dashboard.py; then
    echo "✅ dashboard.py includes debug logging"
else
    echo "❌ dashboard.py missing debug logging"
fi

if grep -q 'health.endpoint || name' dashboard.py; then
    echo "✅ dashboard.py displays endpoint URLs"
else
    echo "❌ dashboard.py missing endpoint display"
fi
echo ""

# 3. Restart dashboard
echo "[3] Restarting dashboard..."
source venv/bin/activate
pkill -f "python.*dashboard.py" 2>/dev/null || true
sleep 2
nohup python dashboard.py > logs/dashboard.log 2>&1 &
sleep 3

if pgrep -f "python.*dashboard.py" > /dev/null; then
    echo "✅ Dashboard restarted"
else
    echo "❌ Dashboard failed to start"
    tail -20 logs/dashboard.log
    exit 1
fi
echo ""

# 4. Test SRE endpoint
echo "[4] Testing SRE endpoint..."
sleep 2
SRE_RESPONSE=$(curl -s http://localhost:5000/api/sre/health 2>/dev/null)

if echo "$SRE_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅' if 'uw_api_endpoints' in d else '❌')" 2>/dev/null; then
    UW_COUNT=$(echo "$SRE_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('uw_api_endpoints', {})))" 2>/dev/null)
    echo "✅ SRE endpoint working"
    echo "✅ UW endpoints in response: $UW_COUNT endpoints"
    
    # Check if endpoints have endpoint field
    HAS_ENDPOINT_FIELD=$(echo "$SRE_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); eps=d.get('uw_api_endpoints', {}); print('✅' if eps and any('endpoint' in h for h in eps.values()) else '❌')" 2>/dev/null)
    echo "$HAS_ENDPOINT_FIELD Endpoint URLs included in response"
    
    # Show sample endpoint
    echo ""
    echo "Sample endpoint data:"
    echo "$SRE_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); eps=d.get('uw_api_endpoints', {}); print(json.dumps(list(eps.items())[0] if eps else {}, indent=2))" 2>/dev/null | head -15
else
    echo "❌ SRE endpoint not working"
    echo "Response: $SRE_RESPONSE" | head -5
fi
echo ""

# 5. Summary
echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open dashboard: http://$(hostname -I | awk '{print $1}'):5000/sre"
echo "2. Scroll down to '🌐 UW API Endpoints Health' section"
echo "3. You should see all $UW_COUNT endpoints with:"
echo "   - Endpoint URL"
echo "   - Status (healthy/degraded/etc)"
echo "   - Error rate"
echo "   - Last success time"
echo ""
echo "If you don't see the section:"
echo "  - Open browser console (F12)"
echo "  - Check for JavaScript errors"
echo "  - Look for 'UW API Endpoints:' log message"
echo ""
