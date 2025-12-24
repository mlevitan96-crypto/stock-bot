#!/bin/bash
# Deploy Audit Fixes to Droplet
# This script handles the case where GitHub push is blocked due to secrets in old commits

cd ~/stock-bot

echo "=========================================="
echo "DEPLOYING AUDIT FIXES"
echo "=========================================="
echo ""

# Option 1: Try to pull (if fixes were pushed)
echo "[1] Attempting to pull latest changes..."
if git pull origin main 2>&1 | grep -q "Already up to date"; then
    echo "  [INFO] Already up to date - fixes may not be pushed yet"
    echo ""
    echo "  [INFO] GitHub push protection is blocking due to secrets in old commits"
    echo "  [INFO] Current fixes are committed locally but not pushed"
    echo ""
    echo "  [INFO] You have two options:"
    echo "    1. Allow the secret via GitHub unblock URL (recommended)"
    echo "    2. Apply fixes manually (see below)"
    echo ""
    
    # Check if fixes are already applied locally
    echo "[2] Checking if fixes are already applied..."
    if grep -q "StateFiles.ADAPTIVE_GATE_STATE" signals/uw_adaptive.py 2>/dev/null; then
        echo "  [OK] Hardcoded path fix: Already applied"
    else
        echo "  [WARN] Hardcoded path fix: Not applied"
    fi
    
    if grep -q "APIConfig.UW_BASE_URL" uw_flow_daemon.py 2>/dev/null; then
        echo "  [OK] API endpoint fix: Already applied"
    else
        echo "  [WARN] API endpoint fix: Not applied"
    fi
    
    if grep -q "def get_insider" uw_flow_daemon.py 2>/dev/null; then
        echo "  [OK] Missing endpoint polling: Already applied"
    else
        echo "  [WARN] Missing endpoint polling: Not applied"
    fi
    
    echo ""
    echo "[3] If fixes are not applied, you can:"
    echo "  - Wait for GitHub push to be unblocked, then pull"
    echo "  - Or apply fixes manually using the code in AUDIT_FIXES_COMPLETE.md"
    echo ""
    exit 0
fi

# If pull succeeded, verify fixes
echo "[2] Verifying fixes..."
python3 -m py_compile signals/uw_adaptive.py uw_flow_daemon.py main.py 2>&1
if [ $? -eq 0 ]; then
    echo "  [OK] Syntax check passed"
else
    echo "  [ERROR] Syntax errors found"
    exit 1
fi

echo ""
echo "[3] Fixes deployed successfully!"
echo "  Next: Restart supervisor to apply changes"
