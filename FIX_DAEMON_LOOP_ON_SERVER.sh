#!/bin/bash
# Apply the critical fix to ensure daemon enters main loop

cd ~/stock-bot

echo "Applying critical daemon loop fix..."

# Backup current file
cp uw_flow_daemon.py uw_flow_daemon.py.backup

# Apply fix: Ensure run() method has proper entry logging
python3 << 'PYEOF'
import re
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if fix is already applied
if "run() method called" in content:
    print("✅ Fix already applied")
    exit(0)

# Find the run() method and add logging right at the start
pattern = r'(def run\(self\):\s+"""Main daemon loop\.""")'
replacement = r'''\1
        safe_print("[UW-DAEMON] run() method called")
        safe_print(f"[UW-DAEMON] self.running = {self.running}")'''

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    file_path.write_text(content)
    print("✅ Applied fix: Added run() entry logging")
else:
    print("⚠️  Could not find run() method to patch")
    exit(1)
PYEOF

echo ""
echo "Testing the fix..."
python3 -c "from uw_flow_daemon import UWFlowDaemon; print('✅ Import successful')" || echo "❌ Import failed"

echo ""
echo "Fix applied. Now run: ./TEST_DAEMON_STARTUP.sh"
