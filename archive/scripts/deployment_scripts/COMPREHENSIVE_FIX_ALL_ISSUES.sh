#!/bin/bash
# Comprehensive fix for all issues: UW endpoints, bootstrap, diagnostics
# Run this on the droplet to fix everything at once

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE FIX - ALL ISSUES"
echo "=========================================="
echo ""

# Fix 1: Bootstrap Expectancy Gate (more lenient)
echo "Fix 1: Making bootstrap expectancy gate more lenient..."
python3 << 'EOF'
import re

with open('v3_2_features.py', 'r') as f:
    content = f.read()

# Replace bootstrap entry_ev_floor from 0.00 to -0.02
pattern = r'"entry_ev_floor":\s*0\.00,'
replacement = '"entry_ev_floor": -0.02,  # More lenient for learning (was 0.00)'

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    with open('v3_2_features.py', 'w') as f:
        f.write(content)
    print("✓ Expectancy gate updated: 0.00 -> -0.02")
elif '-0.02' in content or '-0.05' in content:
    print("✓ Expectancy gate already lenient")
else:
    print("⚠ Could not find entry_ev_floor to update")
EOF

# Fix 2: Verify diagnostic logging exists
echo ""
echo "Fix 2: Verifying diagnostic logging..."
if grep -q "DEBUG decide_and_execute SUMMARY" main.py; then
    echo "✓ Diagnostic logging already in place"
else
    echo "⚠ Diagnostic logging missing - will be added by git pull"
fi

# Fix 3: Check and restart UW daemon
echo ""
echo "Fix 3: Checking UW daemon..."
if pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "✓ UW daemon is running"
else
    echo "⚠ UW daemon not running - restarting..."
    source venv/bin/activate
    screen -dmS uw_daemon python uw_flow_daemon.py
    sleep 3
    if pgrep -f "uw_flow_daemon" > /dev/null; then
        echo "✓ UW daemon restarted"
    else
        echo "❌ Failed to start UW daemon"
    fi
fi

# Fix 4: Check cache freshness
echo ""
echo "Fix 4: Checking UW cache freshness..."
if [ -f "data/uw_flow_cache.json" ]; then
    cache_age=$(($(date +%s) - $(stat -c %Y data/uw_flow_cache.json)))
    cache_age_min=$((cache_age / 60))
    if [ $cache_age -lt 600 ]; then
        echo "✓ Cache is fresh (${cache_age_min} min old)"
    elif [ $cache_age -lt 1800 ]; then
        echo "⚠ Cache is moderately stale (${cache_age_min} min old)"
    else
        echo "❌ Cache is very stale (${cache_age_min} min old) - UW daemon may not be updating"
    fi
else
    echo "❌ Cache file does not exist - UW daemon may not have started"
fi

# Fix 5: Check UW API key
echo ""
echo "Fix 5: Checking UW API key..."
if [ -n "$UW_API_KEY" ]; then
    echo "✓ UW_API_KEY is set"
else
    echo "❌ UW_API_KEY not set - check .env file"
fi

# Fix 6: Restart main supervisor
echo ""
echo "Fix 6: Restarting main supervisor..."
pkill -f deploy_supervisor
sleep 3
source venv/bin/activate
screen -dmS supervisor python deploy_supervisor.py
sleep 5

if pgrep -f deploy_supervisor > /dev/null; then
    echo "✓ Supervisor restarted"
else
    echo "❌ Failed to restart supervisor"
fi

echo ""
echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs: screen -r supervisor"
echo "2. Check dashboard for UW endpoint status"
echo "3. Look for 'DEBUG decide_and_execute SUMMARY' in logs"
echo "4. Check cache freshness: ls -lh data/uw_flow_cache.json"

