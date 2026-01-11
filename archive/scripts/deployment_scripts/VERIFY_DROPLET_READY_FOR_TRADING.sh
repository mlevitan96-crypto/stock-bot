#!/bin/bash
# Comprehensive Droplet Verification - Ready for Trading Tomorrow
# Checks all critical systems and recent fixes

echo "=========================================="
echo "DROPLET VERIFICATION - TRADING READINESS"
echo "=========================================="
echo "Date: $(date)"
echo ""

cd /root/stock-bot || { echo "❌ ERROR: Cannot cd to /root/stock-bot"; exit 1; }

ERRORS=0
WARNINGS=0

# 1. Check Git Status
echo "1. Checking Git Status..."
echo "----------------------------------------"
git fetch origin main >/dev/null 2>&1
LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
REMOTE_COMMIT=$(git rev-parse origin/main 2>/dev/null || echo "unknown")

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo "⚠️  WARNING: Local commit ($LOCAL_COMMIT) differs from remote ($REMOTE_COMMIT)"
    echo "   Run: git pull origin main"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Git is up to date"
    echo "   Latest commit: $(git log -1 --oneline 2>/dev/null || echo 'unknown')"
fi
echo ""

# 2. Check Service Status
echo "2. Checking Service Status..."
echo "----------------------------------------"
if systemctl is-active --quiet trading-bot.service; then
    echo "✅ trading-bot.service is running"
    systemctl status trading-bot.service --no-pager -l | head -5
else
    echo "❌ ERROR: trading-bot.service is NOT running"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Check Processes
echo "3. Checking Critical Processes..."
echo "----------------------------------------"
PROCESSES=("main.py" "uw_flow_daemon.py" "dashboard.py" "deploy_supervisor.py")
for proc in "${PROCESSES[@]}"; do
    if pgrep -f "$proc" > /dev/null; then
        PID=$(pgrep -f "$proc" | head -1)
        echo "✅ $proc is running (PID: $PID)"
    else
        echo "❌ ERROR: $proc is NOT running"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 4. Check Recent Fixes (UW Signal Parser)
echo "4. Verifying Recent Fixes..."
echo "----------------------------------------"
if grep -q "signal_type.*BULLISH_SWEEP\|BEARISH_BLOCK" main.py 2>/dev/null; then
    echo "✅ UW signal parser fix confirmed (signal_type extraction present)"
else
    echo "⚠️  WARNING: UW signal parser fix not found in main.py"
    WARNINGS=$((WARNINGS + 1))
fi

if grep -q "gate_type.*gate_type=" main.py 2>/dev/null; then
    echo "✅ Gate event logging fix confirmed (gate_type parameter present)"
else
    echo "⚠️  WARNING: Gate event logging fix not found"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "sre_diagnostics.py" ]; then
    echo "✅ SRE diagnostics module exists"
else
    echo "⚠️  WARNING: sre_diagnostics.py not found"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "mock_signal_injection.py" ]; then
    echo "✅ Mock signal injection module exists"
else
    echo "⚠️  WARNING: mock_signal_injection.py not found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 5. Check SRE Sentinel Status
echo "5. Checking SRE Sentinel..."
echo "----------------------------------------"
if [ -f "state/sre_metrics.json" ]; then
    echo "✅ SRE metrics file exists"
    python3 -c "
import json, time
from datetime import datetime
try:
    with open('state/sre_metrics.json') as f:
        m = json.load(f)
    heartbeat = m.get('logic_heartbeat', 0)
    if heartbeat:
        age_min = int((time.time() - heartbeat) / 60)
        print(f\"  Logic Heartbeat: {age_min}m ago\")
        print(f\"  Mock Signal Success: {m.get('mock_signal_success_pct', 0):.1f}%\")
        print(f\"  Parser Health: {m.get('parser_health_index', 0):.1f}%\")
    else:
        print(\"  ⚠️  No heartbeat yet (mock signal hasn't run)\")
except Exception as e:
    print(f\"  ⚠️  Error reading metrics: {e}\")
" 2>/dev/null || echo "  ⚠️  Could not read metrics"
else
    echo "⚠️  WARNING: SRE metrics file doesn't exist yet (normal if mock signal hasn't run)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 6. Check UW Cache
echo "6. Checking UW Cache..."
echo "----------------------------------------"
if [ -f "data/uw_flow_cache.json" ]; then
    CACHE_SIZE=$(python3 -c "import json; c=json.load(open('data/uw_flow_cache.json')); print(len([k for k in c.keys() if not k.startswith('_')]))" 2>/dev/null || echo "0")
    if [ "$CACHE_SIZE" -gt "0" ]; then
        echo "✅ UW cache exists with $CACHE_SIZE symbols"
    else
        echo "⚠️  WARNING: UW cache exists but has no symbols"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  WARNING: UW cache file doesn't exist"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 7. Check Dashboard
echo "7. Checking Dashboard..."
echo "----------------------------------------"
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Dashboard is responding on port 5000"
else
    echo "❌ ERROR: Dashboard is NOT responding on port 5000"
    ERRORS=$((ERRORS + 1))
fi

if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ Main bot API is responding on port 8081"
else
    echo "⚠️  WARNING: Main bot API not responding on port 8081"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 8. Check Recent Logs for Errors
echo "8. Checking Recent Logs (last 50 lines)..."
echo "----------------------------------------"
RECENT_ERRORS=$(journalctl -u trading-bot.service -n 50 --no-pager 2>/dev/null | grep -iE "error|exception|traceback|failed" | tail -5)
if [ -n "$RECENT_ERRORS" ]; then
    echo "⚠️  Recent errors in logs:"
    echo "$RECENT_ERRORS" | head -3
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No recent errors in logs"
fi
echo ""

# 9. Check API Keys
echo "9. Checking API Configuration..."
echo "----------------------------------------"
if [ -f ".env" ]; then
    if grep -q "UW_API_KEY=" .env 2>/dev/null && ! grep -q "UW_API_KEY=$" .env 2>/dev/null; then
        echo "✅ UW_API_KEY is set"
    else
        echo "❌ ERROR: UW_API_KEY is NOT set in .env"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "ALPACA_KEY=" .env 2>/dev/null && ! grep -q "ALPACA_KEY=$" .env 2>/dev/null; then
        echo "✅ ALPACA_KEY is set"
    else
        echo "❌ ERROR: ALPACA_KEY is NOT set in .env"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ ERROR: .env file not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 10. Check Disk Space
echo "10. Checking Disk Space..."
echo "----------------------------------------"
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt "90" ]; then
    echo "✅ Disk space OK: ${DISK_USAGE}% used"
else
    echo "⚠️  WARNING: Disk space high: ${DISK_USAGE}% used"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - READY FOR TRADING"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  READY WITH WARNINGS - Review warnings above"
    exit 0
else
    echo "❌ ERRORS DETECTED - Fix errors before trading"
    exit 1
fi
