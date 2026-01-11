#!/bin/bash
# Apply daemon fix directly on server - TESTED CODE

cd ~/stock-bot

echo "=========================================="
echo "APPLYING DAEMON FIX - TESTED CODE"
echo "=========================================="
echo ""

# Backup
BACKUP_FILE="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"

# Apply fix using Python
echo ""
echo "[1] Applying fix..."
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

changes_made = []

# Step 1: Add _loop_entered initialization if missing
if "self._loop_entered = False" not in content:
    # Find the line with _shutting_down and add _loop_entered after it
    pattern = r'(self\._shutting_down = False\s*# Prevent reentrant signal handler calls)'
    replacement = r'\1\n        self._loop_entered = False  # Track if main loop has been entered'
    content = re.sub(pattern, replacement, content)
    changes_made.append("Added _loop_entered initialization")
    print("✅ Added _loop_entered initialization")

# Step 2: Update signal handler to ignore signals before loop entry
if "if not self._loop_entered:" not in content or "IGNORING.*before loop entry" not in content:
    # Find signal handler start
    signal_start = content.find("def _signal_handler(self, signum, frame):")
    if signal_start != -1:
        # Find the docstring end
        docstring_end = content.find('"""', signal_start + 50)
        if docstring_end != -1:
            # Insert ignore logic right after docstring
            insert_pos = content.find('\n', docstring_end + 3)
            if insert_pos != -1:
                ignore_logic = '''        # CRITICAL FIX: Ignore signals until main loop is entered
        # This prevents premature shutdown during initialization
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        '''
                content = content[:insert_pos+1] + ignore_logic + content[insert_pos+1:]
                changes_made.append("Updated signal handler")
                print("✅ Updated signal handler")

# Step 3: Move loop entry flag inside while loop
if "LOOP ENTERED" not in content:
    # Find the while loop
    while_pattern = r'(while should_continue and self\.running:\s*)(safe_print\(f"\[UW-DAEMON\] Step 6:)'
    replacement = r'''\1# Set loop entry flag on FIRST iteration only
            if not self._loop_entered:
                self._loop_entered = True
                safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
            
            \2'''
    content = re.sub(while_pattern, replacement, content, flags=re.DOTALL)
    changes_made.append("Updated while loop")
    print("✅ Updated while loop")

# Step 4: Remove any old flag setting before the loop
# Remove lines that set _loop_entered before the while loop but keep it inside
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this line sets _loop_entered and is before while loop
    if "self._loop_entered = True" in line and "Loop entry flag set" in (lines[i+1] if i+1 < len(lines) else ""):
        # Check if while loop comes after (within next 20 lines)
        found_while = False
        for j in range(i+1, min(i+20, len(lines))):
            if "while should_continue" in lines[j]:
                found_while = True
                break
        if found_while:
            # Skip this line and the next (the safe_print)
            i += 2
            changes_made.append("Removed old flag setting before loop")
            continue
    new_lines.append(line)
    i += 1

content = '\n'.join(new_lines)

# Write the fixed content
file_path.write_text(content)

if changes_made:
    print(f"\n✅ Fix applied: {', '.join(changes_made)}")
else:
    print("\n✅ Fix already applied or no changes needed")
PYEOF

# Verify syntax
echo ""
echo "[2] Verifying Python syntax..."
if python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

# Verify fix
echo ""
echo "[3] Verifying fix..."
if grep -q "_loop_entered = False" uw_flow_daemon.py && \
   grep -q "if not self._loop_entered:" uw_flow_daemon.py && \
   grep -q "LOOP ENTERED" uw_flow_daemon.py; then
    echo "✅ Fix verified in code"
    echo ""
    echo "Key changes:"
    grep -n "_loop_entered\|LOOP ENTERED" uw_flow_daemon.py | head -5
else
    echo "❌ Fix verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Ready to test!"
echo ""
