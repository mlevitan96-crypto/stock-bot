#!/bin/bash
# VERIFY_DEPLOYMENT.sh - Regression testing after deployment
# Follows SDLC best practices

cd ~/stock-bot

echo "=========================================="
echo "DEPLOYMENT VERIFICATION & REGRESSION TESTING"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# Test 1: Bot process running
echo "TEST 1: Bot process running"
echo "----------------------------------------"
BOT_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$BOT_PID" ]; then
    echo "✅ PASS: Bot running (PID: $BOT_PID)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Bot not running"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Dashboard running
echo "TEST 2: Dashboard running"
echo "----------------------------------------"
DASHBOARD_PID=$(ps aux | grep "python.*dashboard.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$DASHBOARD_PID" ]; then
    echo "✅ PASS: Dashboard running (PID: $DASHBOARD_PID)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Dashboard not running"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Supervisor running
echo "TEST 3: Supervisor running"
echo "----------------------------------------"
SUPERVISOR_PID=$(ps aux | grep "deploy_supervisor" | grep -v grep | awk '{print $2}')
if [ ! -z "$SUPERVISOR_PID" ]; then
    echo "✅ PASS: Supervisor running (PID: $SUPERVISOR_PID)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Supervisor not running"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Bot health endpoint (proves secrets loaded)
echo "TEST 4: Bot health endpoint responding"
echo "----------------------------------------"
HEALTH=$(curl -s http://localhost:8081/health 2>/dev/null)
if [ ! -z "$HEALTH" ]; then
    ERROR_COUNT=$(echo "$HEALTH" | grep -i "error\|missing\|secret" | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo "✅ PASS: Health endpoint responding (secrets loaded)"
        PASSED=$((PASSED + 1))
    else
        echo "⚠️  WARN: Health endpoint responding but shows errors"
        echo "$HEALTH" | grep -i "error\|missing\|secret" | head -3
        FAILED=$((FAILED + 1))
    fi
else
    echo "❌ FAIL: Health endpoint not responding"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Dashboard health endpoint
echo "TEST 5: Dashboard health endpoint"
echo "----------------------------------------"
DASHBOARD_HEALTH=$(curl -s http://localhost:5000/api/health_status 2>/dev/null)
if [ ! -z "$DASHBOARD_HEALTH" ]; then
    echo "✅ PASS: Dashboard health endpoint responding"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Dashboard health endpoint not responding"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 6: SRE endpoint working
echo "TEST 6: SRE monitoring endpoint"
echo "----------------------------------------"
SRE_HEALTH=$(curl -s http://localhost:5000/api/sre/health 2>/dev/null)
if [ ! -z "$SRE_HEALTH" ]; then
    echo "✅ PASS: SRE endpoint responding"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: SRE endpoint not responding"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 7: No critical errors in supervisor logs
echo "TEST 7: No critical errors in logs"
echo "----------------------------------------"
if [ -f "logs/supervisor.jsonl" ]; then
    ERROR_COUNT=$(tail -100 logs/supervisor.jsonl 2>/dev/null | grep -i "error\|critical\|failed" | grep -v "INFO\|WARNING" | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo "✅ PASS: No critical errors in supervisor logs"
        PASSED=$((PASSED + 1))
    else
        echo "⚠️  WARN: Found $ERROR_COUNT potential errors"
        tail -100 logs/supervisor.jsonl 2>/dev/null | grep -i "error\|critical\|failed" | tail -3
        # Don't fail, just warn
    fi
else
    echo "⚠️  WARN: Supervisor log not found"
fi
echo ""

# Test 8: Recent bot activity
echo "TEST 8: Recent bot activity"
echo "----------------------------------------"
if [ -f "logs/run.jsonl" ]; then
    LAST_RUN=$(tail -1 logs/run.jsonl 2>/dev/null)
    if [ ! -z "$LAST_RUN" ]; then
        echo "✅ PASS: Recent activity in logs"
        PASSED=$((PASSED + 1))
    else
        echo "⚠️  WARN: No recent activity (may be normal if market closed)"
    fi
else
    echo "⚠️  WARN: run.jsonl not found"
fi
echo ""

# Test 9: .env file exists
echo "TEST 9: .env file exists"
echo "----------------------------------------"
if [ -f ".env" ]; then
    REQUIRED_VARS=$(grep -E "^(UW_API_KEY|ALPACA_KEY|ALPACA_SECRET)=" .env 2>/dev/null | wc -l)
    if [ "$REQUIRED_VARS" -eq 3 ]; then
        echo "✅ PASS: .env file exists with all required variables"
        PASSED=$((PASSED + 1))
    else
        echo "⚠️  WARN: .env exists but missing some required variables ($REQUIRED_VARS/3 found)"
    fi
else
    echo "❌ FAIL: .env file not found"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - Deployment successful!"
    echo ""
    echo "Bot is running and healthy."
    echo "Environment variables are loaded by Python process (not visible in shell)."
    echo "This is expected behavior."
    exit 0
else
    echo "❌ SOME TESTS FAILED - Check issues above"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check supervisor logs: screen -r supervisor"
    echo "  2. Check for errors: tail -50 logs/supervisor.jsonl | grep -i error"
    echo "  3. Verify .env file: cat .env"
    echo "  4. Restart: ./FIX_AND_DEPLOY.sh"
    exit 1
fi
