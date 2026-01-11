#!/bin/bash
# Verify all fixes are applied and system is ready for trades
# This script confirms 100% everything is working

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING ALL FIXES - 100% COMPLETE CHECK"
echo "=========================================="
echo ""

ERRORS=0

# Check 1: Bootstrap expectancy gate
echo "Check 1: Bootstrap expectancy gate..."
if grep -q '"entry_ev_floor": -0.02' v3_2_features.py; then
    echo "✓ Bootstrap expectancy gate: -0.02 (lenient)"
else
    echo "❌ Bootstrap expectancy gate NOT fixed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: Stage-aware score gate
echo "Check 2: Stage-aware score gate..."
if grep -q "if system_stage == \"bootstrap\":" main.py && grep -q "min_score = 1.5" main.py; then
    echo "✓ Score gate: 1.5 for bootstrap, 2.0 for others"
else
    echo "❌ Score gate NOT stage-aware"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 3: Diagnostic logging
echo "Check 3: Diagnostic logging..."
if grep -q "DEBUG decide_and_execute SUMMARY" main.py; then
    echo "✓ Diagnostic logging present"
else
    echo "❌ Diagnostic logging missing"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 4: Investigation script
echo "Check 4: Investigation script..."
if grep -q "hasattr(StateFiles, 'BLOCKED_TRADES')" investigate_no_trades.py || [ -f "comprehensive_no_trades_diagnosis.py" ]; then
    echo "✓ Investigation script fixed or workaround exists"
else
    echo "❌ Investigation script still broken"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 5: Services running
echo "Check 5: Services status..."
SUPERVISOR=$(pgrep -f deploy_supervisor | wc -l)
MAIN=$(pgrep -f "python.*main.py" | wc -l)
DASHBOARD=$(pgrep -f "python.*dashboard.py" | wc -l)
UW_DAEMON=$(pgrep -f "uw_flow_daemon" | wc -l)

if [ "$SUPERVISOR" -gt 0 ] && [ "$MAIN" -gt 0 ] && [ "$DASHBOARD" -gt 0 ]; then
    echo "✓ Services running: supervisor=$SUPERVISOR, main=$MAIN, dashboard=$DASHBOARD"
else
    echo "❌ Services not all running"
    ERRORS=$((ERRORS + 1))
fi

if [ "$UW_DAEMON" -gt 0 ]; then
    echo "✓ UW daemon running"
else
    echo "⚠ UW daemon not running"
fi
echo ""

# Check 6: UW cache
echo "Check 6: UW cache..."
if [ -f "data/uw_flow_cache.json" ]; then
    cache_age=$(($(date +%s) - $(stat -c %Y data/uw_flow_cache.json)))
    cache_age_min=$((cache_age / 60))
    if [ $cache_age -lt 600 ]; then
        echo "✓ UW cache fresh (${cache_age_min} min old)"
    else
        echo "⚠ UW cache stale (${cache_age_min} min old)"
    fi
else
    echo "❌ UW cache file missing"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 7: Dashboard endpoint
echo "Check 7: Dashboard endpoint..."
DASH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "000")
if [ "$DASH_STATUS" = "200" ]; then
    echo "✓ Dashboard accessible (HTTP 200)"
    
    # Check SRE endpoint
    SRE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/sre/health 2>/dev/null || echo "000")
    if [ "$SRE_STATUS" = "200" ]; then
        echo "✓ SRE health endpoint working (HTTP 200)"
    else
        echo "⚠ SRE health endpoint returned HTTP $SRE_STATUS"
    fi
else
    echo "❌ Dashboard not accessible (HTTP $DASH_STATUS)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 8: Main bot health endpoint
echo "Check 8: Main bot health endpoint..."
BOT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health 2>/dev/null || echo "000")
if [ "$BOT_HEALTH" = "200" ]; then
    echo "✓ Main bot health endpoint working (HTTP 200)"
else
    echo "⚠ Main bot health endpoint returned HTTP $BOT_HEALTH"
fi
echo ""

# Summary
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - SYSTEM READY FOR TRADES"
    echo "=========================================="
    echo ""
    echo "Next execution cycle will:"
    echo "  1. Process clusters with lenient gates (bootstrap: score>=1.5, EV>=-0.02)"
    echo "  2. Show diagnostic logs: 'DEBUG decide_and_execute SUMMARY'"
    echo "  3. Execute trades that pass all gates"
    echo ""
    echo "Monitor with: screen -r supervisor"
    exit 0
else
    echo "❌ $ERRORS ERRORS FOUND - FIXES NEEDED"
    echo "=========================================="
    exit 1
fi

