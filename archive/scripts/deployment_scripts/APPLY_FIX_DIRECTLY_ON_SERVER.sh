#!/bin/bash
# Apply fix directly on server - NO GIT PULL NEEDED

cd ~/stock-bot

echo "=========================================="
echo "APPLYING FIX DIRECTLY ON SERVER"
echo "=========================================="
echo ""

# Backup
BACKUP_FILE="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"

# Apply fix using Python
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
    print("✅ Added _loop_entered initialization")

# Fix 2: Signal handler ignores signals before loop
if "Signal.*received before loop entry - IGNORING" not in content:
    # Find signal handler
    signal_handler_start = content.find("def _signal_handler(self, signum, frame):")
    if signal_handler_start != -1:
        # Find the docstring end
        docstring_start = content.find('"""', signal_handler_start)
        docstring_end = content.find('"""', docstring_start + 3)
        if docstring_end != -1:
            # Find first line after docstring
            next_line = content.find('\n', docstring_end + 3)
            if next_line != -1:
                # Insert ignore logic
                ignore_logic = '''        # CRITICAL FIX: Ignore signals until main loop is entered
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        '''
                content = content[:next_line+1] + ignore_logic + content[next_line+1:]
                changes.append("Updated signal handler")
                print("✅ Updated signal handler to ignore signals before loop entry")

# Fix 3: Loop entry flag inside while loop
if "LOOP ENTERED" not in content:
    # Find while loop
    while_pattern = r'(while should_continue and self\.running:\s*)(# Set loop entry flag|safe_print\(f"\[UW-DAEMON\] Step 6:)'
    replacement = r'''\1# Set loop entry flag on FIRST iteration only
                if not self._loop_entered:
                    self._loop_entered = True
                    safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
                
                \2'''
    content = re.sub(while_pattern, replacement, content, flags=re.DOTALL)
    changes.append("Updated while loop")
    print("✅ Updated while loop to set flag on first iteration")

if changes:
    file_path.write_text(content)
    print(f"\n✅ Applied {len(changes)} fixes: {', '.join(changes)}")
else:
    print("\n✅ All fixes already applied")

PYFIX

# Verify syntax
echo ""
echo "[2] Verifying syntax..."
if python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

# Verify fixes
echo ""
echo "[3] Verifying fixes..."
if grep -q "_loop_entered = False" uw_flow_daemon.py && \
   grep -q "if not self._loop_entered:" uw_flow_daemon.py && \
   grep -q "LOOP ENTERED" uw_flow_daemon.py; then
    echo "✅ All fixes verified"
else
    echo "❌ Some fixes missing"
    grep -n "_loop_entered\|LOOP ENTERED" uw_flow_daemon.py | head -5
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED - READY TO TEST"
echo "=========================================="
echo ""
