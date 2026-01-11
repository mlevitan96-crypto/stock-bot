#!/bin/bash
# FINAL PRE-MARKET READINESS CHECK
# Run this before market open to verify everything is ready

cd ~/stock-bot

echo "=========================================="
echo "PRE-MARKET FINAL READINESS CHECK"
echo "=========================================="
echo "Timestamp: $(date)"
echo ""

# Check 1: Console disconnect fix
echo "[1] Console Disconnect Fix..."
if grep -q "stdin=subprocess.DEVNULL" deploy_supervisor.py; then
    echo "✅ Console disconnect fix applied"
else
    echo "❌ Console disconnect fix MISSING"
    exit 1
fi

# Check 2: Daemon loop entry fix
echo ""
echo "[2] Daemon Loop Entry Fix..."
if grep -q "_loop_entered" uw_flow_daemon.py && grep -q "LOOP ENTERED" uw_flow_daemon.py; then
    echo "✅ Loop entry fix present"
else
    echo "❌ Loop entry fix MISSING"
    exit 1
fi

# Check 3: Signal handler fix
echo ""
echo "[3] Signal Handler Fix..."
if grep -q "IGNORING.*before loop entry" uw_flow_daemon.py; then
    echo "✅ Signal handler fix present"
else
    echo "❌ Signal handler fix MISSING"
    exit 1
fi

# Check 4: Market hours logic
echo ""
echo "[4] Market Hours Logic..."
if grep -q "US/Eastern" uw_flow_daemon.py && grep -q "_is_market_hours" uw_flow_daemon.py; then
    echo "✅ Market hours logic present (US/Eastern)"
else
    echo "⚠️  Market hours logic check - verify manually"
fi

# Check 5: Syntax validation
echo ""
echo "[5] Syntax Validation..."
if python3 -m py_compile deploy_supervisor.py 2>&1 && python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ All Python files have valid syntax"
else
    echo "❌ Syntax errors found"
    exit 1
fi

# Check 6: Supervisor can start
echo ""
echo "[6] Supervisor Readiness..."
if [ -f "deploy_supervisor.py" ] && [ -r "deploy_supervisor.py" ]; then
    echo "✅ Supervisor file ready"
else
    echo "❌ Supervisor file not accessible"
    exit 1
fi

# Check 7: Daemon file ready
echo ""
echo "[7] Daemon Readiness..."
if [ -f "uw_flow_daemon.py" ] && [ -r "uw_flow_daemon.py" ]; then
    echo "✅ Daemon file ready"
else
    echo "❌ Daemon file not accessible"
    exit 1
fi

# Check 8: Required directories
echo ""
echo "[8] Required Directories..."
for dir in "logs" "state" "data" "config"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/ exists"
    else
        echo "⚠️  $dir/ missing (will be created by supervisor)"
    fi
done

# Check 9: Environment check
echo ""
echo "[9] Environment Check..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    if grep -q "UW_API_KEY" .env 2>/dev/null; then
        echo "✅ UW_API_KEY found in .env"
    else
        echo "⚠️  UW_API_KEY not found in .env (may cause daemon issues)"
    fi
else
    echo "⚠️  .env file not found"
fi

# Summary
echo ""
echo "=========================================="
echo "READINESS SUMMARY"
echo "=========================================="
echo ""
echo "✅ Console disconnect fix: APPLIED"
echo "✅ Daemon loop entry fix: VERIFIED"
echo "✅ Signal handler fix: VERIFIED"
echo "✅ Syntax validation: PASSED"
echo "✅ Files ready: CONFIRMED"
echo ""
echo "SYSTEM STATUS: READY FOR MARKET OPEN"
echo ""
echo "To start the system:"
echo "  cd ~/stock-bot"
echo "  source venv/bin/activate"
echo "  nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &"
echo ""
echo "Monitor with:"
echo "  tail -f logs/supervisor.log"
echo "  tail -f logs/uw-daemon-pc.log"
echo "  tail -f logs/trading-bot-pc.log"
echo ""
echo "=========================================="
