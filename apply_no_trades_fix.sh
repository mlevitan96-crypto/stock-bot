#!/bin/bash
# Apply no trades fix directly on droplet
# This applies the fixes without needing to push through git

cd ~/stock-bot

echo "Applying no trades fix..."
echo ""

# Fix 1: Make bootstrap expectancy gate more lenient
echo "Fix 1: Updating expectancy gate..."
python3 << 'PYTHON_FIX'
import re

# Read v3_2_features.py
with open('v3_2_features.py', 'r') as f:
    content = f.read()

# Replace bootstrap entry_ev_floor
old = '"entry_ev_floor": 0.00,'
new = '"entry_ev_floor": -0.02,  # More lenient for learning (was 0.00)'

if old in content:
    content = content.replace(old, new)
    with open('v3_2_features.py', 'w') as f:
        f.write(content)
    print("✓ Expectancy gate updated")
else:
    print("ℹ Expectancy gate already updated or different")
PYTHON_FIX

# Fix 2: Add diagnostic logging (already in main.py from earlier fixes)
echo ""
echo "Fix 2: Diagnostic logging should already be in place"
echo ""

echo ""
echo "✅ Fixes applied. Restarting services..."
pkill -f deploy_supervisor
sleep 3
source venv/bin/activate
screen -dmS supervisor python deploy_supervisor.py
sleep 5

echo ""
echo "✅ Services restarted. Monitor with: screen -r supervisor"
echo "Look for: 'DEBUG decide_and_execute SUMMARY' in logs"

