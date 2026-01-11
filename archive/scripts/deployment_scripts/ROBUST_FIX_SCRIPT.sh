#!/bin/bash
# ROBUST FIX - Line-by-line approach to avoid syntax errors

cd ~/stock-bot

echo "=========================================="
echo "ROBUST DAEMON FIX"
echo "=========================================="
echo ""

# Backup
BACKUP="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP"
echo "✅ Backup: $BACKUP"

# Apply fix using Python with careful line-by-line processing
python3 << 'PYFIX'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()
lines = content.split('\n')
new_lines = []
i = 0
fixes_applied = []

while i < len(lines):
    line = lines[i]
    
    # Fix 1: Add _loop_entered after _shutting_down
    if "self._shutting_down = False" in line and "# Prevent reentrant" in line:
        new_lines.append(line)
        i += 1
        # Check next few lines for _loop_entered
        found = False
        for j in range(i, min(i+3, len(lines))):
            if "_loop_entered" in lines[j]:
                found = True
                break
        if not found:
            new_lines.append("        self._loop_entered = False  # Track if main loop has been entered")
            fixes_applied.append("_loop_entered initialization")
        continue
    
    # Fix 2: Add signal ignore in signal handler
    if "def _signal_handler(self, signum, frame):" in line:
        new_lines.append(line)
        i += 1
        # Add docstring
        if i < len(lines):
            new_lines.append(lines[i])  # Docstring line
            i += 1
        # Skip rest of docstring
        while i < len(lines) and '"""' not in lines[i]:
            new_lines.append(lines[i])
            i += 1
        if i < len(lines):
            new_lines.append(lines[i])  # Closing """
            i += 1
        
        # Check if ignore logic exists in next 10 lines
        found = False
        for j in range(i, min(i+10, len(lines))):
            if "if not self._loop_entered:" in lines[j] and "IGNORING" in '\n'.join(lines[j:j+3]):
                found = True
                break
        
        if not found:
            new_lines.append("        # CRITICAL FIX: Ignore signals until main loop is entered")
            new_lines.append("        if not self._loop_entered:")
            new_lines.append('            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")')
            new_lines.append("            return  # Ignore signal until loop is entered")
            new_lines.append("")
            fixes_applied.append("signal ignore logic")
        continue
    
    # Fix 3: Add loop entry flag in while loop
    if "while should_continue and self.running:" in line:
        new_lines.append(line)
        i += 1
        # Check next 10 lines for LOOP ENTERED
        found = False
        for j in range(i, min(i+10, len(lines))):
            if "LOOP ENTERED" in lines[j]:
                found = True
                break
        
        if not found:
            new_lines.append("                # Set loop entry flag on FIRST iteration only")
            new_lines.append("                if not self._loop_entered:")
            new_lines.append("                    self._loop_entered = True")
            new_lines.append('                    safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")')
            new_lines.append("")
            fixes_applied.append("loop entry flag")
        continue
    
    new_lines.append(line)
    i += 1

if fixes_applied:
    file_path.write_text('\n'.join(new_lines))
    print(f"✅ Applied fixes: {', '.join(fixes_applied)}")
else:
    print("✅ All fixes already applied")

PYFIX

# Verify syntax
echo ""
echo "[2] Verifying syntax..."
if python3 -m py_compile uw_flow_daemon.py 2>&1; then
    echo "✅ Syntax OK"
else
    echo "❌ Syntax error!"
    python3 -m py_compile uw_flow_daemon.py 2>&1
    echo "Restoring backup..."
    cp "$BACKUP" uw_flow_daemon.py
    exit 1
fi

# Verify fixes
echo ""
echo "[3] Verifying fixes..."
HAS_LOOP_ENTRY=$(grep -c "_loop_entered = False" uw_flow_daemon.py || echo "0")
HAS_SIGNAL_IGNORE=$(grep -c "if not self._loop_entered:" uw_flow_daemon.py || echo "0")
HAS_LOOP_MSG=$(grep -c "LOOP ENTERED" uw_flow_daemon.py || echo "0")

if [ "$HAS_LOOP_ENTRY" -gt 0 ] && [ "$HAS_SIGNAL_IGNORE" -gt 0 ] && [ "$HAS_LOOP_MSG" -gt 0 ]; then
    echo "✅ All fixes verified:"
    echo "   - _loop_entered initialized: ✅"
    echo "   - Signal ignore logic: ✅"
    echo "   - Loop entry message: ✅"
else
    echo "❌ Some fixes missing:"
    echo "   - _loop_entered: $HAS_LOOP_ENTRY"
    echo "   - Signal ignore: $HAS_SIGNAL_IGNORE"
    echo "   - Loop message: $HAS_LOOP_MSG"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE - READY TO RESTART"
echo "=========================================="
echo ""
