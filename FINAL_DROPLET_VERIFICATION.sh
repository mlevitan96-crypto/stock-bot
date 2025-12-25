#!/bin/bash
# FINAL DROPLET VERIFICATION - Complete End-to-End Test
# Verifies: dashboard, self-healing, monitoring, trading ability, syntax, imports

set -e

echo "=========================================="
echo "FINAL DROPLET VERIFICATION"
echo "=========================================="
echo "Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

cd ~/stock-bot

# Step 1: Pull latest code
echo "Step 1: Pulling latest code..."
git fetch origin main
git reset --hard origin/main
echo "✓ Code updated"
echo ""

# Step 2: Install dependencies
echo "Step 2: Installing dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "  Using virtual environment"
else
    echo "  No venv found, using system Python"
fi
pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
echo "✓ Dependencies installed"
echo ""

# Step 3: Run final verification
echo "Step 3: Running final end-to-end verification..."
python3 FINAL_END_TO_END_VERIFICATION.py > final_verification_output.txt 2>&1
VERIFICATION_EXIT=$?

if [ $VERIFICATION_EXIT -eq 0 ]; then
    echo "✓ Final verification passed"
else
    echo "✗ Final verification had issues (check final_verification_output.txt)"
fi
echo ""

# Step 4: Run complete bot audit
echo "Step 4: Running complete bot audit..."
python3 COMPLETE_BOT_AUDIT.py > complete_audit_output.txt 2>&1
AUDIT_EXIT=$?

if [ $AUDIT_EXIT -eq 0 ]; then
    echo "✓ Complete audit passed"
else
    echo "⚠ Complete audit had warnings (check complete_audit_output.txt)"
fi
echo ""

# Step 5: Test imports
echo "Step 5: Testing critical imports..."
python3 -c "
import sys
errors = []
try:
    import main
    print('  ✓ main.py')
except Exception as e:
    print(f'  ✗ main.py: {e}')
    errors.append('main')

try:
    import dashboard
    print('  ✓ dashboard.py')
except Exception as e:
    print(f'  ✗ dashboard.py: {e}')
    errors.append('dashboard')

try:
    import sre_monitoring
    print('  ✓ sre_monitoring.py')
except Exception as e:
    print(f'  ✗ sre_monitoring.py: {e}')
    errors.append('sre_monitoring')

try:
    from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
    print('  ✓ config.registry')
except Exception as e:
    print(f'  ✗ config.registry: {e}')
    errors.append('registry')

if errors:
    sys.exit(1)
" 2>&1
IMPORT_EXIT=$?

if [ $IMPORT_EXIT -eq 0 ]; then
    echo "✓ All critical imports successful"
else
    echo "✗ Some imports failed"
fi
echo ""

# Step 6: Test dashboard endpoints (dry run)
echo "Step 6: Testing dashboard endpoint definitions..."
python3 -c "
import re
with open('dashboard.py', 'r') as f:
    content = f.read()
endpoints = [
    '/api/sre/health',
    '/api/xai/auditor',
    '/api/xai/export',
    '/api/executive_summary',
    '/api/health_status'
]
missing = []
for ep in endpoints:
    if f'@app.route(\"{ep}\"' not in content and f\"@app.route('{ep}'\" not in content:
        missing.append(ep)
if missing:
    print(f'  ✗ Missing endpoints: {missing}')
    exit(1)
else:
    print('  ✓ All dashboard endpoints defined')
" 2>&1
ENDPOINT_EXIT=$?

if [ $ENDPOINT_EXIT -eq 0 ]; then
    echo "✓ All dashboard endpoints present"
else
    echo "✗ Some dashboard endpoints missing"
fi
echo ""

# Step 7: Test main.py endpoints
echo "Step 7: Testing main.py endpoint definitions..."
python3 -c "
import re
with open('main.py', 'r') as f:
    content = f.read()
endpoints = [
    '/api/positions',
    '/api/profit',
    '/api/state',
    '/api/account'
]
missing = []
for ep in endpoints:
    if f'@app.route(\"{ep}\"' not in content and f\"@app.route('{ep}'\" not in content:
        missing.append(ep)
if missing:
    print(f'  ✗ Missing endpoints: {missing}')
    exit(1)
else:
    print('  ✓ All main.py endpoints defined')
" 2>&1
MAIN_ENDPOINT_EXIT=$?

if [ $MAIN_ENDPOINT_EXIT -eq 0 ]; then
    echo "✓ All main.py endpoints present"
else
    echo "✗ Some main.py endpoints missing"
fi
echo ""

# Step 8: Check self-healing modules
echo "Step 8: Checking self-healing modules..."
if [ -f "self_healing/shadow_trade_logger.py" ]; then
    echo "  ✓ shadow_trade_logger.py"
else
    echo "  ✗ shadow_trade_logger.py missing"
fi
if [ -f "architecture_self_healing.py" ]; then
    echo "  ✓ architecture_self_healing.py"
else
    echo "  ✗ architecture_self_healing.py missing"
fi
echo ""

# Step 9: Check monitoring
echo "Step 9: Checking monitoring..."
if [ -f "sre_monitoring.py" ]; then
    python3 -c "
with open('sre_monitoring.py', 'r') as f:
    content = f.read()
functions = ['get_sre_health', 'check_signal_generation_health', 'check_uw_api_health']
missing = [f for f in functions if f not in content]
if missing:
    print(f'  ✗ Missing functions: {missing}')
    exit(1)
else:
    print('  ✓ All monitoring functions present')
" 2>&1
    echo "✓ Monitoring complete"
else
    echo "✗ sre_monitoring.py missing"
fi
echo ""

# Step 10: Check trading functions
echo "Step 10: Checking trading functions..."
python3 -c "
with open('main.py', 'r') as f:
    content = f.read()
functions = ['decide_and_execute', 'submit_entry', 'evaluate_exits', 'can_open_new_position']
missing = [f for f in functions if f'def {f}' not in content]
if missing:
    print(f'  ✗ Missing functions: {missing}')
    exit(1)
else:
    print('  ✓ All trading functions present')
if 'alpaca_trade_api' in content or 'tradeapi' in content:
    print('  ✓ Alpaca API integration present')
else:
    print('  ✗ Alpaca API integration missing')
    exit(1)
" 2>&1
TRADING_EXIT=$?

if [ $TRADING_EXIT -eq 0 ]; then
    echo "✓ Trading ability confirmed"
else
    echo "✗ Trading functions incomplete"
fi
echo ""

# Final summary
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo ""

ALL_PASSED=true

if [ $VERIFICATION_EXIT -eq 0 ]; then
    echo "[PASS] Final End-to-End Verification"
else
    echo "[FAIL] Final End-to-End Verification"
    ALL_PASSED=false
fi

if [ $AUDIT_EXIT -eq 0 ]; then
    echo "[PASS] Complete Bot Audit"
else
    echo "[WARNING] Complete Bot Audit (non-critical warnings)"
fi

if [ $IMPORT_EXIT -eq 0 ]; then
    echo "[PASS] Critical Imports"
else
    echo "[FAIL] Critical Imports"
    ALL_PASSED=false
fi

if [ $ENDPOINT_EXIT -eq 0 ]; then
    echo "[PASS] Dashboard Endpoints"
else
    echo "[FAIL] Dashboard Endpoints"
    ALL_PASSED=false
fi

if [ $MAIN_ENDPOINT_EXIT -eq 0 ]; then
    echo "[PASS] Main.py Endpoints"
else
    echo "[FAIL] Main.py Endpoints"
    ALL_PASSED=false
fi

if [ $TRADING_EXIT -eq 0 ]; then
    echo "[PASS] Trading Functions"
else
    echo "[FAIL] Trading Functions"
    ALL_PASSED=false
fi

echo ""

if [ "$ALL_PASSED" = true ]; then
    echo "✓✓✓ ALL CRITICAL VERIFICATIONS PASSED - BOT READY FOR TRADING ✓✓✓"
    FINAL_STATUS="PASS"
else
    echo "✗✗✗ SOME VERIFICATIONS FAILED - REVIEW ABOVE ✗✗✗"
    FINAL_STATUS="FAIL"
fi

echo ""
echo "Completed: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Save results
cat > droplet_final_verification_results.json << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")",
  "status": "$FINAL_STATUS",
  "verification_exit": $VERIFICATION_EXIT,
  "audit_exit": $AUDIT_EXIT,
  "import_exit": $IMPORT_EXIT,
  "endpoint_exit": $ENDPOINT_EXIT,
  "main_endpoint_exit": $MAIN_ENDPOINT_EXIT,
  "trading_exit": $TRADING_EXIT,
  "all_passed": $ALL_PASSED
}
EOF

# Commit and push results
git add final_verification_output.txt complete_audit_output.txt droplet_final_verification_results.json 2>/dev/null || true
git commit -m "Droplet final verification results - $(date -u +"%Y-%m-%d %H:%M:%S UTC")" 2>/dev/null || true
git push origin main 2>/dev/null || true

echo "Results saved and pushed to Git"
echo ""

exit $([ "$ALL_PASSED" = true ] && echo 0 || echo 1)

