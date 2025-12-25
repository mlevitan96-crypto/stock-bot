#!/bin/bash
# Auto-run final verification - This will be executed automatically on git pull
# No manual intervention needed

cd ~/stock-bot

# This script is called automatically by the post-merge hook
# It runs comprehensive verification immediately

echo "=========================================="
echo "AUTO-RUNNING FINAL VERIFICATION"
echo "=========================================="
echo "Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Run final verification
if [ -f "FINAL_DROPLET_VERIFICATION.sh" ]; then
    chmod +x FINAL_DROPLET_VERIFICATION.sh
    bash FINAL_DROPLET_VERIFICATION.sh
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✓✓✓ FINAL VERIFICATION COMPLETE - ALL TESTS PASSED ✓✓✓"
    else
        echo ""
        echo "⚠⚠⚠ FINAL VERIFICATION HAD ISSUES - CHECK RESULTS ABOVE ⚠⚠⚠"
    fi
else
    echo "ERROR: FINAL_DROPLET_VERIFICATION.sh not found"
    exit 1
fi

