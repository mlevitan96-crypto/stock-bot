#!/bin/bash
# Trigger UW test via status report script
# This will be called by the hourly status script

cd ~/stock-bot

# Check if test script exists and run it
if [ -f "test_uw_endpoints_comprehensive.py" ]; then
    echo "Running UW endpoint test..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python3 test_uw_endpoints_comprehensive.py
    
    if [ -f "uw_endpoint_test_results.json" ]; then
        git add uw_endpoint_test_results.json 2>/dev/null
        git commit -m "UW endpoint test - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
        git push origin main 2>/dev/null || true
        echo "UW test results pushed"
    fi
fi

