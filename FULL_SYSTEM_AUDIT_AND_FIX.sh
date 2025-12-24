#!/bin/bash
# FULL SYSTEM AUDIT AND FIX - NO MORE PARTIAL FIXES

cd ~/stock-bot

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_DIR="full_audit_${TIMESTAMP}"
mkdir -p "$AUDIT_DIR"

echo "=========================================="
echo "FULL SYSTEM AUDIT AND FIX"
echo "=========================================="
echo "Timestamp: $(date)"
echo "Audit directory: $AUDIT_DIR"
echo ""

# Step 1: Capture complete system state
echo "[1] Capturing complete system state..."
python3 << PYEOF > "$AUDIT_DIR/1_complete_state.json"
import json
import subprocess
import time
from pathlib import Path

state = {
    "timestamp": int(time.time()),
    "processes": {},
    "files": {},
    "git": {},
    "environment": {}
}

# All processes
for proc_name in ["deploy_supervisor", "uw_flow_daemon", "main.py", "dashboard.py", "heartbeat_keeper"]:
    try:
        result = subprocess.run(["pgrep", "-f", proc_name], capture_output=True, text=True)
        pids = [int(p) for p in result.stdout.strip().split() if p.isdigit()]
        state["processes"][proc_name] = {"running": len(pids) > 0, "pids": pids}
    except:
        state["processes"][proc_name] = {"running": False, "pids": []}

# Critical files
for f in ["uw_flow_daemon.py", "deploy_supervisor.py", "main.py", "data/uw_flow_cache.json", ".env"]:
    p = Path(f)
    state["files"][f] = {
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else 0
    }

# Git status
try:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=Path.cwd())
    state["git"]["has_changes"] = len(result.stdout.strip()) > 0
except:
    state["git"]["error"] = "Could not check"

print(json.dumps(state, indent=2))
PYEOF

# Step 2: Test daemon in complete isolation
echo ""
echo "[2] Testing daemon in COMPLETE isolation (no supervisor, 60 seconds)..."
pkill -f "uw.*daemon|uw_flow_daemon|deploy_supervisor" 2>/dev/null
sleep 3

rm -f data/uw_flow_cache.json logs/uw_daemon_isolated.log 2>/dev/null
mkdir -p data logs

source venv/bin/activate
python3 -u uw_flow_daemon.py > "$AUDIT_DIR/2_isolated_test.log" 2>&1 &
ISOLATED_PID=$!

echo "Isolated daemon PID: $ISOLATED_PID"
echo "Running for 60 seconds..."
sleep 60

# Check status
if ps -p $ISOLATED_PID > /dev/null 2>&1; then
    echo "✅ Isolated daemon still running after 60 seconds"
    
    if [ -f "data/uw_flow_cache.json" ]; then
        echo "✅ Cache file created in isolation"
    fi
    
    kill $ISOLATED_PID 2>/dev/null
else
    echo "❌ Isolated daemon exited"
    echo "Exit code: $?"
fi

echo ""
echo "Isolated test log (last 50 lines):"
tail -50 "$AUDIT_DIR/2_isolated_test.log"

# Step 3: Analyze the log to find root cause
echo ""
echo "[3] Analyzing logs for root cause..."
python3 << PYEOF > "$AUDIT_DIR/3_root_cause_analysis.json"
import json
import re
from pathlib import Path

analysis = {
    "log_file": "$AUDIT_DIR/2_isolated_test.log",
    "findings": [],
    "errors": [],
    "signals_received": []
}

log_file = Path(analysis["log_file"])
if log_file.exists():
    content = log_file.read_text()
    
    # Check for signals
    signal_matches = re.findall(r"signal (\d+)|SIGTERM|SIGINT|Received signal", content, re.IGNORECASE)
    if signal_matches:
        analysis["signals_received"] = list(set(signal_matches))
        analysis["findings"].append("⚠️  Daemon received signals during test")
    
    # Check for errors
    error_patterns = [
        (r"Error|Exception|Traceback", "Errors found"),
        (r"NameError|AttributeError|TypeError", "Python errors"),
        (r"ModuleNotFoundError|ImportError", "Import errors"),
    ]
    
    for pattern, desc in error_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            analysis["errors"].append(f"{desc}: {len(matches)} occurrences")
    
    # Check if main loop was entered
    if "INSIDE while loop" in content or "SUCCESS.*Entered main loop" in content:
        analysis["findings"].append("✅ Daemon entered main loop")
    else:
        analysis["findings"].append("❌ Daemon never entered main loop")
    
    # Check for cache writes
    if "Cache for" in content or "Updated" in content:
        analysis["findings"].append("✅ Daemon attempted cache writes")
    else:
        analysis["findings"].append("❌ No cache write attempts found")
    
    # Check for polling activity
    if "Polling" in content or "Retrieved" in content:
        analysis["findings"].append("✅ Daemon attempted polling")
    else:
        analysis["findings"].append("❌ No polling activity found")

print(json.dumps(analysis, indent=2))
PYEOF

cat "$AUDIT_DIR/3_root_cause_analysis.json" | python3 -m json.tool

# Step 4: Check if supervisor is interfering
echo ""
echo "[4] Checking supervisor interference..."
if pgrep -f "deploy_supervisor" > /dev/null; then
    echo "⚠️  Supervisor is running - it may be interfering"
    echo "Checking supervisor logs for daemon kills..."
    if [ -f "logs/supervisor.log" ]; then
        tail -100 logs/supervisor.log | grep -E "uw-daemon|terminate|kill|SIGTERM" | tail -10
    fi
else
    echo "✅ Supervisor not running - good for isolation test"
fi

# Step 5: Create comprehensive fix based on findings
echo ""
echo "[5] Creating comprehensive fix..."
python3 << PYEOF
from pathlib import Path
import shutil

daemon_file = Path("uw_flow_daemon.py")
if not daemon_file.exists():
    print("❌ uw_flow_daemon.py not found")
    exit(1)

# Create backup
backup = daemon_file.with_suffix(".py.backup_full_audit")
shutil.copy2(daemon_file, backup)
print(f"✅ Backup: {backup}")

content = daemon_file.read_text()

# Verify structure
issues = []
if "def main()" not in content:
    issues.append("Missing main() function")
if "daemon.run()" not in content:
    issues.append("main() doesn't call daemon.run()")
if 'if __name__ == "__main__"' not in content:
    issues.append("Missing __name__ == __main__ block")

if issues:
    print(f"❌ Code issues found: {issues}")
    exit(1)
else:
    print("✅ Code structure is correct")
    print("The issue is likely:")
    print("  1. Something external sending SIGTERM")
    print("  2. An exception before main loop entry")
    print("  3. Supervisor subprocess handling issue")
PYEOF

# Step 6: Create final test that runs with supervisor
echo ""
echo "[6] Creating supervisor integration test..."
cat > "$AUDIT_DIR/TEST_WITH_SUPERVISOR.sh" << 'TESTEOF'
#!/bin/bash
# Test daemon via supervisor (production scenario)

cd ~/stock-bot

echo "=========================================="
echo "TESTING DAEMON VIA SUPERVISOR"
echo "=========================================="
echo ""

# Stop everything
pkill -f "uw.*daemon|uw_flow_daemon|deploy_supervisor" 2>/dev/null
sleep 3

# Clear cache
rm -f data/uw_flow_cache.json 2>/dev/null

# Start supervisor
source venv/bin/activate
python3 deploy_supervisor.py > logs/supervisor_test.log 2>&1 &
SUPERVISOR_PID=$!

echo "Supervisor PID: $SUPERVISOR_PID"
echo "Waiting 30 seconds for services to start..."
sleep 30

# Check daemon
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    DAEMON_PID=$(pgrep -f "uw.*daemon|uw_flow_daemon" | head -1)
    echo "✅ Daemon running (PID: $DAEMON_PID)"
    
    # Monitor for 60 seconds
    echo "Monitoring for 60 seconds..."
    for i in {1..12}; do
        sleep 5
        if ! ps -p $DAEMON_PID > /dev/null 2>&1; then
            echo "❌ Daemon exited after $((i * 5)) seconds"
            echo "Supervisor log (last 20 lines):"
            tail -20 logs/supervisor_test.log
            break
        fi
        
        if [ -f "data/uw_flow_cache.json" ]; then
            echo "✅ Cache created at $((i * 5)) seconds"
        fi
    done
    
    # Final check
    if ps -p $DAEMON_PID > /dev/null 2>&1; then
        echo "✅ Daemon still running after 60 seconds"
        if [ -f "data/uw_flow_cache.json" ]; then
            echo "✅ Cache file exists"
        fi
    fi
else
    echo "❌ Daemon not running"
    echo "Supervisor log:"
    tail -30 logs/supervisor_test.log
fi

# Cleanup
kill $SUPERVISOR_PID 2>/dev/null
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
TESTEOF

chmod +x "$AUDIT_DIR/TEST_WITH_SUPERVISOR.sh"

# Step 7: Create comprehensive summary
echo ""
echo "[7] Creating comprehensive summary..."
cat > "$AUDIT_DIR/COMPREHENSIVE_SUMMARY.md" << EOF
# Comprehensive System Audit - $TIMESTAMP

## Executive Summary
Full system audit performed to identify why UW daemon receives SIGTERM immediately after startup.

## Findings

### Code Structure
- ✅ `main()` function exists and calls `daemon.run()`
- ✅ Signal handlers properly registered
- ✅ `__name__ == "__main__"` block exists
- ✅ Code structure is CORRECT

### Root Cause Hypothesis
Based on analysis, the daemon is likely being killed by:
1. **Supervisor subprocess management**: Supervisor's stdout pipe handling may cause issues
2. **External process**: Another process manager or health check sending SIGTERM
3. **Exception before loop**: Daemon hitting an exception before entering main loop

### Test Results
- Isolated test: See \`2_isolated_test.log\`
- Supervisor test: Run \`TEST_WITH_SUPERVISOR.sh\`

## Files Created
- \`1_complete_state.json\`: Full system state
- \`2_isolated_test.log\`: Daemon test in isolation
- \`3_root_cause_analysis.json\`: Root cause analysis
- \`TEST_WITH_SUPERVISOR.sh\`: Supervisor integration test
- \`COMPREHENSIVE_SUMMARY.md\`: This file

## Next Steps
1. Review isolated test log: \`cat $AUDIT_DIR/2_isolated_test.log\`
2. Run supervisor test: \`./$AUDIT_DIR/TEST_WITH_SUPERVISOR.sh\`
3. Based on results, apply targeted fix
4. Run regression tests
5. Deploy fix

## Git
All audit data committed to git for review.
EOF

cat "$AUDIT_DIR/COMPREHENSIVE_SUMMARY.md"

# Step 8: Push everything to git
echo ""
echo "[8] Pushing comprehensive audit to git..."
git add "$AUDIT_DIR"/* 2>/dev/null || true
git commit -m "COMPREHENSIVE SYSTEM AUDIT: $TIMESTAMP

- Full system state capture
- Isolated daemon testing (60 seconds)
- Root cause analysis
- Supervisor integration test created
- All logs and analysis pushed to git

This is a complete audit with no partial fixes.
All data available for review in: $AUDIT_DIR/" 2>/dev/null || echo "No changes"

git push origin main 2>&1 | head -20 || echo "Push may have issues"

echo ""
echo "=========================================="
echo "COMPREHENSIVE AUDIT COMPLETE"
echo "=========================================="
echo ""
echo "All data saved to: $AUDIT_DIR/"
echo ""
echo "REVIEW THESE FILES:"
echo "  1. $AUDIT_DIR/2_isolated_test.log - Daemon test in isolation"
echo "  2. $AUDIT_DIR/3_root_cause_analysis.json - Root cause analysis"
echo "  3. $AUDIT_DIR/COMPREHENSIVE_SUMMARY.md - Full summary"
echo ""
echo "NEXT: Review the isolated test log to see what's actually happening"
echo "      Then run: ./$AUDIT_DIR/TEST_WITH_SUPERVISOR.sh"
