#!/bin/bash
# Apply the daemon fix directly on the server

cd ~/stock-bot

echo "=========================================="
echo "APPLYING DAEMON FIX DIRECTLY"
echo "=========================================="
echo ""

# Backup
echo "[1] Creating backup..."
cp uw_flow_daemon.py uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# Apply fix using Python
echo ""
echo "[2] Applying fix..."
python3 << 'PYFIX'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if fix is already applied
if "_loop_entered = True" in content and "LOOP ENTERED" in content:
    print("✅ Fix already applied")
    exit(0)

# Step 1: Ensure _loop_entered is initialized in __init__
if "self._loop_entered = False" not in content:
    # Find __init__ method and add the flag
    init_pattern = r'(def __init__\(self\):.*?self\._shutting_down = False)'
    replacement = r'\1\n        self._loop_entered = False  # Track if main loop has been entered'
    content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)
    print("✅ Added _loop_entered initialization")

# Step 2: Update signal handler to ignore signals before loop entry
if "if not self._loop_entered:" not in content:
    # Find signal handler and add ignore logic at the start
    signal_handler_pattern = r'(def _signal_handler\(self, signum, frame\):.*?"""Handle shutdown signals\."""\s*)'
    ignore_logic = '''    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        # CRITICAL FIX: Ignore signals until main loop is entered
        # This prevents premature shutdown during initialization
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        '''
    # Replace the signal handler
    content = re.sub(
        r'def _signal_handler\(self, signum, frame\):.*?"""Handle shutdown signals\."""',
        ignore_logic.strip(),
        content,
        flags=re.DOTALL
    )
    print("✅ Updated signal handler")

# Step 3: Move loop entry flag inside the while loop
# Find the while loop and add flag setting on first iteration
while_pattern = r'(while should_continue and self\.running:\s*)(safe_print\(f"\[UW-DAEMON\] Step 6: INSIDE while loop!)'
replacement = r'''\1# Set loop entry flag on FIRST iteration only
            if not self._loop_entered:
                self._loop_entered = True
                safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
            
            \2'''
content = re.sub(while_pattern, replacement, content, flags=re.DOTALL)
print("✅ Updated while loop to set flag on first iteration")

# Step 4: Remove any old flag setting before the loop
# Remove lines that set _loop_entered before the while loop
lines = content.split('\n')
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    # Skip lines that set _loop_entered before the while loop
    if "self._loop_entered = True" in line and "Loop entry flag set" in lines[i+1] if i+1 < len(lines) else False:
        # Check if this is before the while loop (not inside it)
        # Look ahead to see if while loop comes after
        found_while = False
        for j in range(i+1, min(i+10, len(lines))):
            if "while should_continue" in lines[j]:
                found_while = True
                break
        if found_while:
            skip_next = True  # Skip this line and the next (the safe_print)
            continue
    new_lines.append(line)

content = '\n'.join(new_lines)

# Write the fixed content
file_path.write_text(content)
print("✅ Fix applied successfully")
PYFIX

# Verify syntax
echo ""
echo "[3] Verifying Python syntax..."
python3 -m py_compile uw_flow_daemon.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp uw_flow_daemon.py.backup.* uw_flow_daemon.py 2>/dev/null
    exit 1
fi

# Verify fix
echo ""
echo "[4] Verifying fix..."
if grep -q "_loop_entered = True" uw_flow_daemon.py && grep -q "LOOP ENTERED" uw_flow_daemon.py; then
    echo "✅ Fix verified in code"
else
    echo "❌ Fix verification failed"
    echo "Checking what's in the file..."
    grep -n "_loop_entered\|LOOP ENTERED" uw_flow_daemon.py | head -5
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Next: Run the test script to verify it works"
echo ""
