#!/bin/bash
# Direct fix for no trades issue - applies changes on droplet
# Run this on the droplet to fix the issue immediately

cd ~/stock-bot

echo "=========================================="
echo "FIXING NO TRADES ISSUE"
echo "=========================================="
echo ""

# Fix 1: Make bootstrap expectancy gate more lenient
echo "Fix 1: Making bootstrap expectancy gate more lenient..."
python3 << 'EOF'
import re

# Read and fix v3_2_features.py
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
else:
    # Check if already fixed
    if '-0.02' in content or '-0.05' in content:
        print("✓ Expectancy gate already lenient")
    else:
        print("⚠ Could not find entry_ev_floor to update")
EOF

# Fix 2: Add diagnostic logging to main.py
echo ""
echo "Fix 2: Adding diagnostic logging..."
python3 << 'EOF'
with open('main.py', 'r') as f:
    content = f.read()

# Check if diagnostic logging already exists
if 'DEBUG decide_and_execute SUMMARY' in content:
    print("✓ Diagnostic logging already in place")
else:
    # Find the return statement in decide_and_execute and add summary before it
    # Look for: return orders (at the end of decide_and_execute)
    pattern = r'(                log_attribution\(trade_id=f"open_\{symbol\}_\{now_iso\(\)\}", symbol=symbol, pnl_usd=0\.0, context=context\)\s*\n\s*# RISK MANAGEMENT)'
    replacement = r'''                log_attribution(trade_id=f"open_{symbol}_{now_iso()}", symbol=symbol, pnl_usd=0.0, context=context)
        
        # DIAGNOSTIC: Log summary of execution
        print(f"DEBUG decide_and_execute SUMMARY: {len(clusters_sorted)} clusters processed, {new_positions_this_cycle} positions opened this cycle, {len(orders)} orders returned", flush=True)
        if len(orders) == 0 and len(clusters_sorted) > 0:
            print(f"DEBUG WARNING: {len(clusters_sorted)} clusters processed but 0 orders returned - check gate logs above for block reasons", flush=True)
        
        # RISK MANAGEMENT'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        with open('main.py', 'w') as f:
            f.write(content)
        print("✓ Diagnostic logging added")
    else:
        print("⚠ Could not find insertion point for diagnostic logging")
EOF

echo ""
echo "=========================================="
echo "RESTARTING SERVICES"
echo "=========================================="
pkill -f deploy_supervisor
sleep 3
source venv/bin/activate
screen -dmS supervisor python deploy_supervisor.py
sleep 5

if pgrep -f deploy_supervisor > /dev/null; then
    echo "✅ Services restarted"
    echo ""
    echo "Monitor with: screen -r supervisor"
    echo "Look for: 'DEBUG decide_and_execute SUMMARY' in logs"
else
    echo "❌ Failed to restart services"
fi

echo ""
echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="

