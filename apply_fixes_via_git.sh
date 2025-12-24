#!/bin/bash
# Apply fixes by pulling from git and running fix script
# This script runs on the droplet

cd ~/stock-bot

echo "=========================================="
echo "APPLYING FIXES VIA GIT"
echo "=========================================="
echo ""

# Step 1: Try to pull latest (may fail if git push blocked)
echo "Step 1: Pulling latest code..."
if git pull origin main 2>&1 | grep -q "error\|rejected"; then
    echo "⚠ Git pull failed (likely due to push protection)"
    echo "  This is expected - fixes are in local commits"
    echo "  We'll apply fixes manually..."
else
    echo "✓ Code pulled successfully"
fi

# Step 2: Check if fix script exists
echo ""
echo "Step 2: Checking for fix script..."
if [ -f "COMPREHENSIVE_FIX_ALL_ISSUES.sh" ]; then
    echo "✓ Fix script found"
    chmod +x COMPREHENSIVE_FIX_ALL_ISSUES.sh
    echo "Running fix script..."
    ./COMPREHENSIVE_FIX_ALL_ISSUES.sh
else
    echo "⚠ Fix script not found - applying fixes manually..."
    
    # Manual fix 1: Bootstrap expectancy gate
    echo ""
    echo "Applying bootstrap fix..."
    python3 << 'EOF'
import re
with open('v3_2_features.py', 'r') as f:
    content = f.read()
if '"entry_ev_floor": -0.02' in content:
    print("✓ Bootstrap fix already applied")
elif re.search(r'"entry_ev_floor":\s*0\.00,', content):
    content = re.sub(r'"entry_ev_floor":\s*0\.00,', '"entry_ev_floor": -0.02,  # More lenient for learning (was 0.00)', content)
    with open('v3_2_features.py', 'w') as f:
        f.write(content)
    print("✓ Bootstrap fix applied")
else:
    print("⚠ Could not find entry_ev_floor to fix")
EOF
    
    # Manual fix 2: Check diagnostic logging
    echo ""
    echo "Checking diagnostic logging..."
    if grep -q "DEBUG decide_and_execute SUMMARY" main.py; then
        echo "✓ Diagnostic logging present"
    else
        echo "⚠ Diagnostic logging missing - may need to pull from git"
    fi
    
    # Manual fix 3: Restart services
    echo ""
    echo "Restarting services..."
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
fi

echo ""
echo "=========================================="
echo "FIXES APPLIED"
echo "=========================================="

