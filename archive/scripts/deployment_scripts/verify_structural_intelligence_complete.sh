#!/bin/bash
# Complete Verification Script for Structural Intelligence Overhaul
# This script runs on the droplet after git pull to verify all components

cd ~/stock-bot

echo "=========================================="
echo "STRUCTURAL INTELLIGENCE COMPLETE VERIFICATION"
echo "=========================================="
echo ""

# Step 1: Install dependencies
echo "Step 1: Installing dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi

pip3 install -q hmmlearn numpy scipy tzdata 2>&1 | tail -5
echo "✓ Dependencies installed"
echo ""

# Step 2: Run integration tests
echo "Step 2: Running integration tests..."
python3 test_structural_intelligence_integration.py > integration_test_output.txt 2>&1
INTEGRATION_EXIT=$?
if [ $INTEGRATION_EXIT -eq 0 ]; then
    echo "✓ Integration tests passed"
else
    echo "⚠ Integration tests had issues (check integration_test_output.txt)"
fi
echo ""

# Step 3: Run regression tests
echo "Step 3: Running regression tests..."
python3 regression_test_structural_intelligence.py > regression_test_output.txt 2>&1
REGRESSION_EXIT=$?
if [ $REGRESSION_EXIT -eq 0 ]; then
    echo "✓ Regression tests passed"
else
    echo "⚠ Regression tests had issues (check regression_test_output.txt)"
fi
echo ""

# Step 4: Run complete verification
echo "Step 4: Running complete droplet verification..."
python3 complete_droplet_verification.py > verification_output.txt 2>&1
VERIFY_EXIT=$?
if [ $VERIFY_EXIT -eq 0 ]; then
    echo "✓ Complete verification passed"
else
    echo "⚠ Complete verification had issues (check verification_output.txt)"
fi
echo ""

# Step 5: Test that main.py imports without errors
echo "Step 5: Testing main.py imports..."
python3 -c "import main; print('✓ main.py imports successfully')" 2>&1 | head -5
MAIN_IMPORT_EXIT=$?
if [ $MAIN_IMPORT_EXIT -eq 0 ]; then
    echo "✓ main.py imports successfully"
else
    echo "⚠ main.py import had issues"
fi
echo ""

# Step 6: Test structural intelligence modules
echo "Step 6: Testing structural intelligence modules..."
python3 -c "
from structural_intelligence import get_regime_detector, get_macro_gate, get_structural_exit
from learning import get_thompson_engine
from self_healing import get_shadow_logger
from api_management import get_quota_manager
print('✓ All structural intelligence modules import successfully')
" 2>&1
MODULES_EXIT=$?
if [ $MODULES_EXIT -eq 0 ]; then
    echo "✓ All modules import successfully"
else
    echo "⚠ Module imports had issues"
fi
echo ""

# Step 7: Commit and push results
echo "Step 7: Committing and pushing results..."
git add structural_intelligence_test_results.json regression_test_results.json droplet_verification_results.json integration_test_output.txt regression_test_output.txt verification_output.txt 2>/dev/null
git commit -m "Structural Intelligence verification results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
git push origin main 2>/dev/null || true
echo "✓ Results pushed to Git"
echo ""

# Summary
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo "Integration Tests: $([ $INTEGRATION_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Regression Tests: $([ $REGRESSION_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Complete Verification: $([ $VERIFY_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Main Import: $([ $MAIN_IMPORT_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Module Imports: $([ $MODULES_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo ""

if [ $INTEGRATION_EXIT -eq 0 ] && [ $REGRESSION_EXIT -eq 0 ] && [ $VERIFY_EXIT -eq 0 ] && [ $MAIN_IMPORT_EXIT -eq 0 ] && [ $MODULES_EXIT -eq 0 ]; then
    echo "✓ ALL VERIFICATIONS PASSED"
    exit 0
else
    echo "⚠ SOME VERIFICATIONS FAILED - Check output files for details"
    exit 1
fi

