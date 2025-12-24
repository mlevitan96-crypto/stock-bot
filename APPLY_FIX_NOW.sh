#!/bin/bash
# Simple script to apply the daemon loop fix on the server

cd ~/stock-bot

echo "=========================================="
echo "APPLYING DAEMON LOOP FIX"
echo "=========================================="
echo ""

# Step 1: Check if fix is already applied
echo "[1] Checking if fix is already applied..."
if grep -q "run() method called" uw_flow_daemon.py; then
    echo "✅ Fix already applied - skipping"
    echo ""
    echo "Proceeding to test..."
    ./TEST_DAEMON_STARTUP.sh
    exit 0
fi

echo "⚠️  Fix not found - applying now..."
echo ""

# Step 2: Backup current file
echo "[2] Creating backup..."
cp uw_flow_daemon.py uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Step 3: Apply the fix
echo "[3] Applying fix..."
python3 << 'PYEOF'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if already fixed
if "run() method called" in content:
    print("✅ Fix already applied")
    exit(0)

# Find and replace the run() method start
# Look for: "    def run(self):\n        \"\"\"Main daemon loop.\"\"\""
old_pattern = '    def run(self):\n        """Main daemon loop."""'
new_pattern = '''    def run(self):
        """Main daemon loop."""
        safe_print("[UW-DAEMON] run() method called")
        safe_print(f"[UW-DAEMON] self.running = {self.running}")'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    file_path.write_text(content)
    print("✅ Fix applied successfully")
else:
    # Try alternative pattern (with different spacing)
    import re
    pattern = r'(    def run\(self\):\s+"""Main daemon loop\.""")'
    replacement = r'''\1
        safe_print("[UW-DAEMON] run() method called")
        safe_print(f"[UW-DAEMON] self.running = {self.running}")'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        file_path.write_text(content)
        print("✅ Fix applied successfully (alternative method)")
    else:
        print("❌ Could not find run() method to patch")
        print("   Please check the file manually")
        exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ Fix failed - check error above"
    exit 1
fi

echo ""

# Step 4: Verify syntax
echo "[4] Verifying Python syntax..."
python3 -m py_compile uw_flow_daemon.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp uw_flow_daemon.py.backup.* uw_flow_daemon.py 2>/dev/null
    exit 1
fi

echo ""

# Step 5: Verify fix is present
echo "[5] Verifying fix is present..."
if grep -q "run() method called" uw_flow_daemon.py; then
    echo "✅ Fix verified - 'run() method called' found in file"
    echo ""
    echo "Showing the updated run() method start:"
    grep -A 3 "def run(self):" uw_flow_daemon.py | head -5
else
    echo "❌ Fix not found after application - something went wrong"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Next step: Run the test script"
echo "  ./TEST_DAEMON_STARTUP.sh"
echo ""
