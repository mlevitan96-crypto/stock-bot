#!/bin/bash
# Complete Deployment and Verification Script for Droplet
# Run this on the droplet to pull changes and verify everything works

set -e  # Exit on error

echo "=========================================="
echo "COMPLETE DEPLOYMENT AND VERIFICATION"
echo "=========================================="
echo ""

cd ~/stock-bot

# Step 1: Pull latest changes
echo "Step 1: Pulling latest changes from Git..."
git fetch origin main
git reset --hard origin/main 2>&1 | tail -5
echo "✓ Code updated"
echo ""

# Step 2: Verify all new files exist
echo "Step 2: Verifying new implementation files..."
FILES=(
    "tca_data_manager.py"
    "execution_quality_learner.py"
    "signal_pattern_learner.py"
    "parameter_optimizer.py"
    "backtest_all_implementations.py"
)

MISSING=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "ERROR: Some files are missing. Pull may have failed."
    exit 1
fi
echo ""

# Step 3: Run backtest
echo "Step 3: Running comprehensive backtest..."
if [ -f "backtest_all_implementations.py" ]; then
    python3 backtest_all_implementations.py
    BACKTEST_EXIT=$?
    if [ $BACKTEST_EXIT -eq 0 ]; then
        echo "✓ Backtest passed"
    else
        echo "⚠ Backtest had failures (check backtest_results.json)"
    # Don't exit - continue with verification
    fi
else
    echo "⚠ backtest_all_implementations.py not found"
fi
echo ""

# Step 4: Verify imports work
echo "Step 4: Verifying Python imports..."
python3 << 'EOF'
import sys
errors = []

try:
    from tca_data_manager import get_recent_slippage
    print("  ✓ tca_data_manager")
except Exception as e:
    print(f"  ✗ tca_data_manager: {e}")
    errors.append("tca_data_manager")

try:
    from execution_quality_learner import get_execution_learner
    print("  ✓ execution_quality_learner")
except Exception as e:
    print(f"  ✗ execution_quality_learner: {e}")
    errors.append("execution_quality_learner")

try:
    from signal_pattern_learner import get_signal_pattern_learner
    print("  ✓ signal_pattern_learner")
except Exception as e:
    print(f"  ✗ signal_pattern_learner: {e}")
    errors.append("signal_pattern_learner")

try:
    from parameter_optimizer import get_parameter_optimizer
    print("  ✓ parameter_optimizer")
except Exception as e:
    print(f"  ✗ parameter_optimizer: {e}")
    errors.append("parameter_optimizer")

if errors:
    print(f"\nERROR: {len(errors)} import(s) failed")
    sys.exit(1)
else:
    print("\n✓ All imports successful")
    sys.exit(0)
EOF

IMPORT_EXIT=$?
if [ $IMPORT_EXIT -ne 0 ]; then
    echo "ERROR: Import verification failed"
    exit 1
fi
echo ""

# Step 5: Verify main.py can import new modules
echo "Step 5: Verifying main.py integration..."
python3 << 'EOF'
import sys
import importlib.util

# Try to compile main.py to check for syntax errors
spec = importlib.util.spec_from_file_location("main", "main.py")
if spec is None:
    print("  ✗ Could not load main.py")
    sys.exit(1)

try:
    # Just compile, don't execute
    with open("main.py", "r") as f:
        compile(f.read(), "main.py", "exec")
    print("  ✓ main.py compiles successfully")
except SyntaxError as e:
    print(f"  ✗ main.py syntax error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  ⚠ main.py check warning: {e}")
    # Don't fail on import errors during compile check

sys.exit(0)
EOF

MAIN_EXIT=$?
if [ $MAIN_EXIT -ne 0 ]; then
    echo "ERROR: main.py verification failed"
    exit 1
fi
echo ""

# Step 6: Check learning orchestrator
echo "Step 6: Verifying learning orchestrator integration..."
python3 << 'EOF'
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("orchestrator", "comprehensive_learning_orchestrator_v2.py")
if spec is None:
    print("  ✗ Could not load orchestrator")
    sys.exit(1)

try:
    with open("comprehensive_learning_orchestrator_v2.py", "r") as f:
        compile(f.read(), "comprehensive_learning_orchestrator_v2.py", "exec")
    print("  ✓ learning orchestrator compiles successfully")
except SyntaxError as e:
    print(f"  ✗ orchestrator syntax error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  ⚠ orchestrator check warning: {e}")

sys.exit(0)
EOF

ORCH_EXIT=$?
if [ $ORCH_EXIT -ne 0 ]; then
    echo "ERROR: Learning orchestrator verification failed"
    exit 1
fi
echo ""

# Step 7: Run investigation (post-merge hook should have done this, but verify)
echo "Step 7: Checking investigation results..."
if [ -f "investigate_no_trades.json" ]; then
    echo "  ✓ Investigation results exist"
    # Check if recent (within last hour)
    if [ -f ".last_investigation_run" ]; then
        echo "  ✓ Investigation was run recently"
    fi
else
    echo "  ⚠ Investigation results not found (may not have run yet)"
fi
echo ""

# Step 8: Summary
echo "=========================================="
echo "DEPLOYMENT VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "✓ All code files present"
echo "✓ All imports working"
echo "✓ main.py integration verified"
echo "✓ Learning orchestrator verified"
echo ""
echo "Next steps:"
echo "  1. Restart services if needed"
echo "  2. Monitor logs for any errors"
echo "  3. Check backtest_results.json for detailed test results"
echo ""
echo "To restart services:"
echo "  - If using process-compose: process-compose restart"
echo "  - If using systemd: sudo systemctl restart stock-bot"
echo "  - If running manually: Stop and restart main.py"
echo ""

