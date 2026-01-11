#!/bin/bash
# Complete script to fix daemon loop issue

cd ~/stock-bot

echo "=========================================="
echo "APPLYING DAEMON LOOP FIX"
echo "=========================================="
echo ""

# Step 1: Check if fix is already applied
echo "[1] Checking if fix is already applied..."
if grep -q "run() method called" uw_flow_daemon.py 2>/dev/null; then
    echo "✅ Fix already applied"
    echo ""
    echo "Running test..."
    ./TEST_DAEMON_STARTUP.sh
    exit 0
fi

echo "⚠️  Fix not found - applying now..."
echo ""

# Step 2: Backup
echo "[2] Creating backup..."
BACKUP_FILE="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"
echo ""

# Step 3: Apply fix
echo "[3] Applying fix..."
python3 << 'PYEOF'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if already fixed
if "run() method called" in content:
    print("✅ Fix already applied")
    exit(0)

# Method 1: Direct string replacement
old1 = '    def run(self):\n        """Main daemon loop."""'
new1 = '''    def run(self):
        """Main daemon loop."""
        safe_print("[UW-DAEMON] run() method called")
        safe_print(f"[UW-DAEMON] self.running = {self.running}")'''

if old1 in content:
    content = content.replace(old1, new1)
    file_path.write_text(content)
    print("✅ Fix applied (method 1)")
    exit(0)

# Method 2: Regex replacement
import re
pattern = r'(    def run\(self\):\s+"""Main daemon loop\.""")'
replacement = r'''\1
        safe_print("[UW-DAEMON] run() method called")
        safe_print(f"[UW-DAEMON] self.running = {self.running}")'''

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    file_path.write_text(content)
    print("✅ Fix applied (method 2)")
    exit(0)

# Method 3: Line-by-line insertion
lines = content.split('\n')
new_lines = []
i = 0
found = False

while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # Look for def run(self):
    if line.strip() == "def run(self):" and not found:
        found = True
        # Add next line (docstring) if it exists
        if i + 1 < len(lines) and '"""' in lines[i + 1]:
            new_lines.append(lines[i + 1])
            i += 1
        
        # Add our fix
        new_lines.append('        safe_print("[UW-DAEMON] run() method called")')
        new_lines.append('        safe_print(f"[UW-DAEMON] self.running = {self.running}")')
        new_lines.append('')
    
    i += 1

if found:
    file_path.write_text('\n'.join(new_lines))
    print("✅ Fix applied (method 3)")
    exit(0)
else:
    print("❌ Could not find run() method")
    print("   Showing first 20 lines of file:")
    print('\n'.join(lines[:20]))
    exit(1)
PYEOF

FIX_RESULT=$?

if [ $FIX_RESULT -ne 0 ]; then
    echo "❌ Fix failed - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

echo ""

# Step 4: Verify syntax
echo "[4] Verifying Python syntax..."
python3 -m py_compile uw_flow_daemon.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

echo ""

# Step 5: Verify fix
echo "[5] Verifying fix is present..."
if grep -q "run() method called" uw_flow_daemon.py; then
    echo "✅ Fix verified"
    echo ""
    echo "Updated run() method start:"
    grep -A 4 "^    def run(self):" uw_flow_daemon.py | head -6
else
    echo "❌ Fix not found after application"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Now testing..."
echo ""

./TEST_DAEMON_STARTUP.sh
