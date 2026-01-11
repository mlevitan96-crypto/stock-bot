#!/bin/bash
# Auto-run UW test - this will be triggered automatically
# Add this to cron or run via post-merge hook

cd ~/stock-bot

# Check if test script exists
if [ -f "test_uw_endpoints_comprehensive.py" ] && [ -f "TRIGGER_UW_TEST.sh" ]; then
    echo "Running UW endpoint test automatically..."
    bash TRIGGER_UW_TEST.sh
fi

