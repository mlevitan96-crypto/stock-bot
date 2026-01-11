#!/bin/bash
# COMPLETE FIX - NO SYNTAX ERRORS

cd ~/stock-bot

echo "=========================================="
echo "COMPLETE DAEMON FIX"
echo "=========================================="
echo ""

# Backup
BACKUP="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP"
echo "✅ Backup: $BACKUP"

# Apply fix using sed and Python (more reliable)
python3 << 'PYFIX'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
lines = file_path.read_text().split('\n')
new_lines = []
i = 0
changes = []

while i < len(lines):
    line = lines[i]
    
    # Fix 1: Add _loop_entered initialization after _shutting_down
    if "self._shutting_down = False" in line and "# Prevent reentrant" in line:
        new_lines.append(line)
        i += 1
        # Check if next line doesn't already have _loop_entered
        if i < len(lines) and "self._loop_entered" not in lines[i]:
            new_lines.append("        self._loop_entered = False  # Track if main loop has been entered")
            changes.append("Added _loop_entered")
        continue
    
    # Fix 2: Add signal ignore logic in signal handler
    if "def _signal_handler(self, signum, frame):" in line:
        new_lines.append(line)
        i += 1
        # Skip docstring
        if i < len(lines) and '"""' in lines[i]:
            new_lines.append(lines[i])
            i += 1
            # Find end of docstring
            while i < len(lines) and '"""' not in lines[i]:
                new_lines.append(lines[i])
                i += 1
            if i < len(lines):
                new_lines.append(lines[i])  # Closing """
                i += 1
        
        # Check if ignore logic already exists
        if i < len(lines) and "if not self._loop_entered:" not in lines[i]:
            new_lines.append("        # CRITICAL FIX: Ignore signals until main loop is entered")
            new_lines.append("        if not self._loop_entered:")
            new_lines.append('            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")')
            new_lines.append("            return  # Ignore signal until loop is entered")
            new_lines.append("")
            changes.append("Added signal ignore")
        continue
    
    # Fix 3: Add loop entry flag in while loop
    if "while should_continue and self.running:" in line:
        new_lines.append(line)
        i += 1
        # Check if loop entry flag setting already exists
        if i < len(lines) and "LOOP ENTERED" not in '\n'.join(lines[i:i+5]):
            new_lines.append("                # Set loop entry flag on FIRST iteration only")
            new_lines.append("                if not self._loop_entered:")
            new_lines.append("                    self._loop_entered = True")
            new_lines.append('                    safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")')
            new_lines.append("")
            changes.append("Added loop entry flag")
        continue
    
    new_lines.append(line)
    i += 1

if changes:
    file_path.write_text('\n'.join(new_lines))
    print(f"✅ Applied fixes: {', '.join(changes)}")
else:
    print("✅ All fixes already applied")

PYFIX

# Verify syntax
echo ""
echo "[2] Verifying syntax..."
if python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ Syntax OK"
else
    echo "❌ Syntax error - restoring backup"
    cp "$BACKUP" uw_flow_daemon.py
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
    echo "❌ Fixes missing"
    exit 1
fi

echo ""
echo "✅ FIX COMPLETE - Ready to restart"
echo ""
