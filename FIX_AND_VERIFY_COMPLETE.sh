#!/bin/bash
# Complete fix and verification script

cd ~/stock-bot

echo "=========================================="
echo "COMPLETE FIX AND VERIFICATION"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo "[1] Pulling latest code..."
git pull origin main

# Step 2: Apply fix directly if needed
echo ""
echo "[2] Verifying and applying fixes..."
python3 << 'PYFIX'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()
changes = []

# Fix 1: Ensure _loop_entered is initialized
if "self._loop_entered = False" not in content:
    pattern = r'(self\._shutting_down = False\s*# Prevent reentrant signal handler calls)'
    replacement = r'\1\n        self._loop_entered = False  # Track if main loop has been entered'
    content = re.sub(pattern, replacement, content)
    changes.append("Added _loop_entered initialization")

# Fix 2: Signal handler ignores signals before loop
if "if not self._loop_entered:" not in content or "IGNORING.*before loop entry" not in content:
    signal_start = content.find("def _signal_handler(self, signum, frame):")
    if signal_start != -1:
        docstring_end = content.find('"""', signal_start + 50)
        if docstring_end != -1:
            insert_pos = content.find('\n', docstring_end + 3)
            if insert_pos != -1:
                ignore_logic = '''        # CRITICAL FIX: Ignore signals until main loop is entered
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        '''
                content = content[:insert_pos+1] + ignore_logic + content[insert_pos+1:]
                changes.append("Updated signal handler")

# Fix 3: Loop entry flag inside while loop
if "LOOP ENTERED" not in content:
    while_pattern = r'(while should_continue and self\.running:\s*)(safe_print\(f"\[UW-DAEMON\] Step 6:)'
    replacement = r'''\1# Set loop entry flag on FIRST iteration only
            if not self._loop_entered:
                self._loop_entered = True
                safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
            
            \2'''
    content = re.sub(while_pattern, replacement, content, flags=re.DOTALL)
    changes.append("Updated while loop")

# Fix 4: Market hours check in _poll_ticker
if "Market closed - skipping API call" not in content:
    poll_pattern = r'(# Poll option flow\s*if self\.poller\.should_poll\("option_flow"\):)'
    replacement = r'''# Poll option flow (only during market hours)
            if self.poller.should_poll("option_flow"):
                # Double-check market hours before making API call
                if not self.poller._is_market_hours():
                    safe_print(f"[UW-DAEMON] Market closed - skipping API call for {ticker}")
                    return'''
    content = re.sub(poll_pattern, replacement, content)
    changes.append("Added market hours check in _poll_ticker")

# Fix 5: Better market hours logging
if "Market is CLOSED" not in content:
    market_pattern = r'(return market_open <= hour_min < market_close)'
    replacement = r'''is_open = market_open <= hour_min < market_close
            # Log market status for debugging
            if not is_open:
                safe_print(f"[UW-DAEMON] Market is CLOSED (ET time: {now_et.strftime('%H:%M')}) - skipping API calls")
            return is_open'''
    content = re.sub(market_pattern, replacement, content)
    changes.append("Added market hours logging")

if changes:
    file_path.write_text(content)
    print(f"✅ Applied fixes: {', '.join(changes)}")
else:
    print("✅ All fixes already applied")
PYFIX

# Step 3: Verify syntax
echo ""
echo "[3] Verifying Python syntax..."
if python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error"
    exit 1
fi

# Step 4: Test daemon
echo ""
echo "[4] Testing daemon (60 seconds)..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

rm -f data/uw_flow_cache.json logs/uw_daemon_complete_test.log 2>/dev/null
mkdir -p data logs

source venv/bin/activate
python3 -u uw_flow_daemon.py > logs/uw_daemon_complete_test.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 60 seconds..."
sleep 60

# Step 5: Check results
echo ""
echo "=========================================="
echo "RESULTS"
echo "=========================================="
echo ""

if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "✅ Daemon still running"
else
    echo "❌ Daemon exited"
fi

# Check for loop entry
if grep -q "LOOP ENTERED" logs/uw_daemon_complete_test.log; then
    echo "✅ Loop entry message found"
else
    echo "⚠️  Loop entry message not found"
fi

# Check for market hours awareness
if grep -q "Market is CLOSED\|Market closed - skipping" logs/uw_daemon_complete_test.log; then
    echo "✅ Market hours check working"
    grep "Market.*CLOSED\|Market closed" logs/uw_daemon_complete_test.log | head -3
else
    echo "⚠️  No market hours messages (may be market hours)"
fi

# Check for polling activity
POLL_COUNT=$(grep -c "Polling\|Retrieved.*flow trades" logs/uw_daemon_complete_test.log 2>/dev/null || echo "0")
if [ "$POLL_COUNT" -gt 0 ]; then
    echo "✅ Polling activity: $POLL_COUNT occurrences"
else
    echo "⚠️  No polling activity (expected if market closed)"
fi

# Check for API calls when market closed
if grep -q "Market closed - skipping API call" logs/uw_daemon_complete_test.log; then
    echo "✅ Correctly skipping API calls when market closed"
fi

kill $DAEMON_PID 2>/dev/null

echo ""
echo "Full log: logs/uw_daemon_complete_test.log"
echo ""
