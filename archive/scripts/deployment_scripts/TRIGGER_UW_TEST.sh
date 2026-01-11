#!/bin/bash
# Trigger UW API endpoint test and push results
# Run this on the droplet

cd ~/stock-bot

echo "=========================================="
echo "TESTING UW API ENDPOINTS"
echo "=========================================="
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the test
python3 test_uw_endpoints_comprehensive.py

# Commit and push results
if [ -f "uw_endpoint_test_results.json" ]; then
    git add uw_endpoint_test_results.json 2>/dev/null
    git commit -m "UW endpoint test results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
    echo ""
    echo "Results pushed to git"
fi

echo ""
echo "Test complete. Check uw_endpoint_test_results.json for details."

