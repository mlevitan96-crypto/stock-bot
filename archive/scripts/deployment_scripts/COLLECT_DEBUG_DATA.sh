#!/bin/bash
# Collect debug data from daemon run

cd ~/stock-bot

echo "Collecting debug data..."

# Check if daemon is running
echo "[1] Daemon process check:"
pgrep -f "uw.*daemon|uw_flow_daemon" && echo "✅ Running" || echo "❌ NOT running"
echo ""

# Check daemon logs
echo "[2] Recent daemon logs (last 50 lines):"
if [ -f "logs/uw_daemon.log" ]; then
    tail -50 logs/uw_daemon.log
else
    echo "⚠️  No daemon log file found"
fi
echo ""

# Check debug log
echo "[3] Debug instrumentation log:"
if [ -f ".cursor/debug.log" ]; then
    echo "Debug log found:"
    cat .cursor/debug.log
else
    echo "⚠️  No debug log found (daemon may not have started)"
fi
echo ""

# Check for Python errors
echo "[4] Checking for Python syntax/import errors:"
python3 -m py_compile uw_flow_daemon.py 2>&1 && echo "✅ No syntax errors" || echo "❌ Syntax errors found"
echo ""

# Check if imports work
echo "[5] Testing imports:"
python3 << 'PYEOF'
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    from config.registry import CacheFiles, Directories, StateFiles
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
PYEOF
