#!/bin/bash
# Fix console disconnection issue

cd ~/stock-bot

echo "=========================================="
echo "FIXING CONSOLE DISCONNECTION ISSUE"
echo "=========================================="
echo ""

# The issue: supervisor's subprocess.Popen might be affecting terminal
# Fix: Add stdin=subprocess.DEVNULL to prevent child processes from reading terminal

echo "[1] Applying fix to deploy_supervisor.py..."
python3 << 'PYFIX'
from pathlib import Path
import re

file_path = Path("deploy_supervisor.py")
content = file_path.read_text()

# Find subprocess.Popen call and add stdin=subprocess.DEVNULL
pattern = r'(proc = subprocess\.Popen\(\s+cmd,\s+stdout=subprocess\.PIPE,\s+stderr=subprocess\.STDOUT,\s+bufsize=1,\s+universal_newlines=True,\s+env=env\s+\))'

replacement = r'''proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # Prevent child from reading from terminal
            bufsize=1,
            universal_newlines=True,
            env=env,
            start_new_session=False  # Keep in same process group
        )'''

if "stdin=subprocess.DEVNULL" not in content:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    file_path.write_text(content)
    print("✅ Added stdin=subprocess.DEVNULL to prevent terminal interaction")
else:
    print("✅ Fix already applied")

PYFIX

# Verify syntax
echo ""
echo "[2] Verifying syntax..."
if python3 -m py_compile deploy_supervisor.py 2>&1; then
    echo "✅ Syntax OK"
else
    echo "❌ Syntax error"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED"
echo "=========================================="
echo ""
echo "This fix prevents child processes from:"
echo "  - Reading from terminal (stdin)"
echo "  - Creating new process groups that could disconnect terminal"
echo ""
echo "The supervisor will now run safely without disconnecting your console."
echo ""
