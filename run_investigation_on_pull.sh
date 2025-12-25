#!/bin/bash
# This script runs automatically when pulled from git
# It triggers an investigation immediately AND runs complete verification

cd ~/stock-bot

echo "=========================================="
echo "COMPLETE VERIFICATION (Triggered by Git Pull)"
echo "=========================================="
echo ""

# Step 0: Run final verification if script exists (comprehensive end-to-end check)
if [ -f "FINAL_DROPLET_VERIFICATION.sh" ]; then
    echo "Running final comprehensive verification..."
    chmod +x FINAL_DROPLET_VERIFICATION.sh
    bash FINAL_DROPLET_VERIFICATION.sh
    echo ""
fi

# Step 0b: Run structural intelligence deployment if script exists
if [ -f "FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh" ]; then
    echo "Running structural intelligence deployment verification..."
    chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
    bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
    echo ""
fi

# Step 1: Run complete verification (comprehensive)
echo "Step 1: Running complete verification..."
if [ -f "force_droplet_pull_and_verify.sh" ]; then
    # Use comprehensive verification script
    bash force_droplet_pull_and_verify.sh 2>&1
    VERIFY_EXIT=$?
    if [ $VERIFY_EXIT -eq 0 ]; then
        echo "✓ Complete verification passed"
    else
        echo "⚠ Complete verification had issues (check results files)"
    fi
elif [ -f "complete_droplet_verification.py" ]; then
    python3 complete_droplet_verification.py 2>&1
    VERIFY_EXIT=$?
    if [ $VERIFY_EXIT -eq 0 ]; then
        echo "✓ Complete verification passed"
    else
        echo "⚠ Complete verification had issues (check droplet_verification_results.json)"
    fi
else
    echo "⚠ Verification scripts not found - running fallback"
    if [ -f "deploy_and_verify_on_droplet.sh" ]; then
        bash deploy_and_verify_on_droplet.sh 2>&1
    fi
fi
echo ""

echo "=========================================="
echo "RUNNING INVESTIGATION (Triggered by Git Pull)"
echo "=========================================="
echo ""

# Check if UW test is requested OR if test script exists (auto-run)
if [ -f ".trigger_uw_test" ] || [ -f "test_uw_endpoints_comprehensive.py" ]; then
    echo "UW endpoint test detected - running test..."
    if [ -f "TRIGGER_UW_TEST.sh" ]; then
        bash TRIGGER_UW_TEST.sh
        rm -f .trigger_uw_test 2>/dev/null
    elif [ -f "test_uw_endpoints_comprehensive.py" ]; then
        # Run test directly
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        python3 test_uw_endpoints_comprehensive.py
        if [ -f "uw_endpoint_test_results.json" ]; then
            git add uw_endpoint_test_results.json 2>/dev/null
            git commit -m "UW endpoint test results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
            git push origin main 2>/dev/null || true
        fi
    fi
    echo ""
fi

# Run investigation (ALWAYS use comprehensive version first - it has the fixes)
# Use comprehensive version which works around registry issues
if [ -f "comprehensive_no_trades_diagnosis.py" ]; then
    echo "Running comprehensive diagnosis (has all fixes)..."
    python3 comprehensive_no_trades_diagnosis.py 2>&1
    INVEST_EXIT=$?
    if [ $INVEST_EXIT -ne 0 ]; then
        echo "WARNING: Comprehensive diagnosis failed, trying original..."
        python3 investigate_no_trades.py 2>&1
    fi
else
    echo "WARNING: comprehensive_no_trades_diagnosis.py not found, using original..."
    python3 investigate_no_trades.py 2>&1
fi

# Commit and push results
if [ -f "investigate_no_trades.json" ]; then
    touch .last_investigation_run
    git add investigate_no_trades.json .last_investigation_run 2>/dev/null
    git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
    echo "✓ Investigation results pushed to git"
else
    echo "⚠ Investigation file not created - check for errors above"
fi
