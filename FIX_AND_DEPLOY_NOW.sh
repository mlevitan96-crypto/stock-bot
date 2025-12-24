#!/bin/bash
# FIX AND DEPLOY NOW - READY FOR MARKET OPEN

cd ~/stock-bot

echo "=========================================="
echo "FIXING AND DEPLOYING NOW"
echo "=========================================="
echo ""

# Step 1: Pull latest
echo "[1] Pulling latest code..."
git pull origin main

# Step 2: Apply fix directly (in case it's not in git)
echo ""
echo "[2] Applying fix directly..."
python3 << 'PYFIX'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if _loop_entered is initialized
if "self._loop_entered = False" not in content:
    # Find where to add it
    pattern = r'(self\._shutting_down = False\s*# Prevent reentrant signal handler calls)'
    replacement = r'\1\n        self._loop_entered = False  # Track if main loop has been entered'
    content = re.sub(pattern, replacement, content)
    print("✅ Added _loop_entered initialization")

# Check if signal handler ignores signals
if "Signal.*received before loop entry - IGNORING" not in content:
    # Find signal handler
    handler_start = content.find("def _signal_handler(self, signum, frame):")
    if handler_start != -1:
        docstring_end = content.find('"""', handler_start + 50)
        if docstring_end != -1:
            next_line = content.find('\n', docstring_end + 3)
            if next_line != -1:
                ignore_logic = '''        # CRITICAL FIX: Ignore signals until main loop is entered
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        '''
                content = content[:next_line+1] + ignore_logic + content[next_line+1:]
                print("✅ Added signal ignore logic")

# Check if loop entry flag is set inside loop
if "LOOP ENTERED" not in content:
    # Find while loop
    while_match = re.search(r'(while should_continue and self\.running:\s*)(# Set loop entry flag|safe_print\(f"\[UW-DAEMON\] Step 6:)', content, re.DOTALL)
    if while_match:
        replacement = while_match.group(1) + '''# Set loop entry flag on FIRST iteration only
                if not self._loop_entered:
                    self._loop_entered = True
                    safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
                
                ''' + while_match.group(2)
        content = content[:while_match.start()] + replacement + content[while_match.end():]
        print("✅ Added loop entry flag setting")

file_path.write_text(content)
print("✅ Fix applied")
PYFIX

# Step 3: Verify syntax
echo ""
echo "[3] Verifying syntax..."
if ! python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "❌ Syntax error!"
    exit 1
fi
echo "✅ Syntax OK"

# Step 4: Verify fixes
echo ""
echo "[4] Verifying fixes..."
if grep -q "_loop_entered = False" uw_flow_daemon.py && \
   grep -q "if not self._loop_entered:" uw_flow_daemon.py && \
   grep -q "LOOP ENTERED" uw_flow_daemon.py; then
    echo "✅ All fixes verified"
else
    echo "❌ Fixes not found"
    exit 1
fi

# Step 5: Stop and restart
echo ""
echo "[5] Restarting services..."
pkill -f "deploy_supervisor|uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 3

source venv/bin/activate
nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &
SUPERVISOR_PID=$!

echo "Supervisor PID: $SUPERVISOR_PID"
echo "Waiting 15 seconds..."
sleep 15

# Step 6: Verify it's working
echo ""
echo "[6] Verifying daemon..."
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "✅ Daemon process running"
    
    if [ -f "logs/uw_daemon.log" ]; then
        if grep -q "LOOP ENTERED\|IGNORING.*before loop entry" logs/uw_daemon.log; then
            echo "✅ Fix working - daemon entered loop or ignored premature signals"
            tail -15 logs/uw_daemon.log
        elif grep -q "Polling\|Retrieved" logs/uw_daemon.log; then
            echo "✅ Daemon is working (polling activity detected)"
        else
            echo "⚠️  Daemon running but no activity yet"
            tail -10 logs/uw_daemon.log
        fi
    fi
else
    echo "❌ Daemon not running"
    if [ -f "logs/supervisor.log" ]; then
        echo "Supervisor log:"
        tail -20 logs/supervisor.log
    fi
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
