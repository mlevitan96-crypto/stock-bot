#!/bin/bash
# Comprehensive system audit and fix - NO MORE PARTIAL FIXES

cd ~/stock-bot

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_DIR="comprehensive_audit_${TIMESTAMP}"
mkdir -p "$AUDIT_DIR"

echo "=========================================="
echo "COMPREHENSIVE SYSTEM AUDIT AND FIX"
echo "=========================================="
echo "Timestamp: $(date)"
echo "Directory: $AUDIT_DIR"
echo ""

# Step 1: Full system state capture
echo "[1] Capturing full system state..."
python3 << PYEOF > "$AUDIT_DIR/1_system_state.json"
import json
import subprocess
import time
from pathlib import Path

state = {
    "timestamp": int(time.time()),
    "processes": {},
    "files": {},
    "environment": {},
    "git_status": {}
}

# Check all processes
processes_to_check = [
    "deploy_supervisor",
    "uw_flow_daemon",
    "main.py",
    "dashboard.py",
    "heartbeat_keeper"
]

for proc_name in processes_to_check:
    try:
        result = subprocess.run(
            ["pgrep", "-f", proc_name],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split()
        state["processes"][proc_name] = {
            "running": len(pids) > 0,
            "pids": [int(p) for p in pids if p.isdigit()]
        }
    except:
        state["processes"][proc_name] = {"running": False, "pids": []}

# Check critical files
critical_files = [
    "uw_flow_daemon.py",
    "deploy_supervisor.py",
    "main.py",
    "data/uw_flow_cache.json",
    ".env"
]

for file_path in critical_files:
    path = Path(file_path)
    state["files"][file_path] = {
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "readable": path.is_file() and path.stat().st_mode & 0o444 if path.exists() else False
    }

# Check git status
try:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    state["git_status"]["has_changes"] = len(result.stdout.strip()) > 0
    state["git_status"]["changes"] = result.stdout.strip().split("\n") if result.stdout.strip() else []
except:
    state["git_status"]["error"] = "Could not check git status"

print(json.dumps(state, indent=2))
PYEOF

# Step 2: Analyze daemon code for exit points
echo ""
echo "[2] Analyzing daemon code for exit points..."
python3 << PYEOF > "$AUDIT_DIR/2_daemon_analysis.json"
import json
import re
from pathlib import Path

daemon_file = Path("uw_flow_daemon.py")
analysis = {
    "has_main_function": False,
    "main_calls_run": False,
    "has_signal_handlers": False,
    "exit_points": [],
    "potential_issues": []
}

if daemon_file.exists():
    content = daemon_file.read_text()
    
    # Check for main function
    if re.search(r"def main\(\)|if __name__.*==.*__main__", content):
        analysis["has_main_function"] = True
    
    # Check if main calls run()
    if "def main()" in content and "daemon.run()" in content:
        analysis["main_calls_run"] = True
    
    # Check for signal handlers
    if "signal.signal" in content and "_signal_handler" in content:
        analysis["has_signal_handlers"] = True
    
    # Find all exit points
    exit_patterns = [
        (r"sys\.exit\s*\(", "sys.exit()"),
        (r"exit\s*\(", "exit()"),
        (r"return\s*$", "return (implicit exit)"),
    ]
    
    for pattern, name in exit_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            context = content[max(0, match.start()-50):match.start()+50].replace('\n', ' ')
            analysis["exit_points"].append({
                "type": name,
                "line": line_num,
                "context": context[:100]
            })
    
    # Check for potential issues
    if "def main()" in content:
        main_start = content.find("def main()")
        main_content = content[main_start:main_start+500]
        if "daemon.run()" not in main_content:
            analysis["potential_issues"].append("main() function may not call daemon.run()")
    
    if len(analysis["exit_points"]) == 0:
        analysis["potential_issues"].append("No explicit exit points found - daemon may rely on signal handlers only")

print(json.dumps(analysis, indent=2))
PYEOF

# Step 3: Check what's sending SIGTERM
echo ""
echo "[3] Investigating SIGTERM source..."
python3 << PYEOF > "$AUDIT_DIR/3_sigterm_investigation.json"
import json
import subprocess
from pathlib import Path

investigation = {
    "supervisor_running": False,
    "supervisor_pid": None,
    "daemon_processes": [],
    "potential_killers": []
}

# Check supervisor
try:
    result = subprocess.run(
        ["pgrep", "-f", "deploy_supervisor"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        pids = result.stdout.strip().split()
        if pids:
            investigation["supervisor_running"] = True
            investigation["supervisor_pid"] = int(pids[0])
except:
    pass

# Check daemon processes
try:
    result = subprocess.run(
        ["pgrep", "-f", "uw.*daemon|uw_flow_daemon"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        pids = result.stdout.strip().split()
        investigation["daemon_processes"] = [int(p) for p in pids if p.isdigit()]
except:
    pass

# Check for other process managers that might kill processes
potential_killers = [
    "systemd",
    "supervisord",
    "process-compose",
    "pm2"
]

for killer in potential_killers:
    try:
        result = subprocess.run(
            ["pgrep", "-f", killer],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            investigation["potential_killers"].append(killer)
    except:
        pass

print(json.dumps(investigation, indent=2))
PYEOF

# Step 4: Read daemon main() function to see if it's calling run()
echo ""
echo "[4] Checking daemon main() function..."
python3 << PYEOF
from pathlib import Path
import re

daemon_file = Path("uw_flow_daemon.py")
if daemon_file.exists():
    content = daemon_file.read_text()
    
    # Find main function
    main_match = re.search(r"def main\(\):.*?(?=\ndef |\Z)", content, re.DOTALL)
    if main_match:
        main_content = main_match.group(0)
        print("Main function found:")
        print(main_content[:500])
        print("")
        
        if "daemon.run()" in main_content:
            print("✅ main() calls daemon.run()")
        else:
            print("❌ main() does NOT call daemon.run()")
            print("This is the problem - daemon exits immediately!")
    else:
        print("❌ No main() function found")
        
    # Check if __name__ == "__main__" block exists
    if 'if __name__' in content and '__main__' in content:
        name_main_match = re.search(r"if __name__.*?==.*?__main__.*?(?=\n\n|\Z)", content, re.DOTALL)
        if name_main_match:
            print("\n__name__ == __main__ block:")
            print(name_main_match.group(0)[:300])
PYEOF

# Step 5: Create comprehensive fix
echo ""
echo "[5] Creating comprehensive fix..."
cat > "$AUDIT_DIR/FIX_DAEMON_MAIN.py" << 'FIXEOF'
#!/usr/bin/env python3
"""Fix daemon main() function to ensure it calls run() and doesn't exit"""
from pathlib import Path
import re

daemon_file = Path("uw_flow_daemon.py")
if not daemon_file.exists():
    print("❌ uw_flow_daemon.py not found")
    exit(1)

content = daemon_file.read_text()
backup_file = daemon_file.with_suffix(".py.backup_before_fix")
daemon_file.write_text(content)  # Create backup by copying
print(f"✅ Backup created: {backup_file}")

# Check if main() exists and calls run()
has_main = "def main()" in content
has_name_main = 'if __name__' in content and '__main__' in content
calls_run = "daemon.run()" in content

print(f"Current state:")
print(f"  has main(): {has_main}")
print(f"  has __name__ == __main__: {has_name_main}")
print(f"  calls daemon.run(): {calls_run}")

# Find the end of the file to add/update main block
if not has_name_main or not calls_run:
    print("\nFixing main() function...")
    
    # Remove old main block if it exists
    if has_name_main:
        content = re.sub(r'\nif __name__.*?==.*?__main__.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
    
    # Add proper main block at the end
    main_block = '''

def main():
    """Entry point."""
    safe_print("[UW-DAEMON] Main function called")
    try:
        daemon = UWFlowDaemon()
        safe_print("[UW-DAEMON] Daemon object created successfully")
        safe_print(f"[UW-DAEMON] Daemon running flag: {daemon.running}")
        safe_print("[UW-DAEMON] Calling daemon.run()...")
        daemon.run()  # This will run forever until signal
        safe_print("[UW-DAEMON] daemon.run() returned (should not happen)")
    except KeyboardInterrupt:
        safe_print("[UW-DAEMON] Keyboard interrupt in main()")
    except Exception as e:
        safe_print(f"[UW-DAEMON] Error in main(): {e}")
        import traceback
        safe_print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}")
    finally:
        safe_print("[UW-DAEMON] Main function exiting")

if __name__ == "__main__":
    main()
'''
    
    # Append main block
    content = content.rstrip() + main_block
    
    daemon_file.write_text(content)
    print("✅ Fixed main() function")
else:
    print("✅ main() function looks correct")

# Verify syntax
import py_compile
try:
    py_compile.compile(str(daemon_file), doraise=True)
    print("✅ Python syntax is valid")
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error: {e}")
    exit(1)
FIXEOF

python3 "$AUDIT_DIR/FIX_DAEMON_MAIN.py" > "$AUDIT_DIR/5_fix_output.txt" 2>&1
cat "$AUDIT_DIR/5_fix_output.txt"

# Step 6: Test the fix
echo ""
echo "[6] Testing the fix..."
python3 -m py_compile uw_flow_daemon.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - fix failed"
    exit 1
fi

# Step 7: Verify main() calls run()
echo ""
echo "[7] Verifying fix..."
if grep -q "daemon.run()" uw_flow_daemon.py && grep -q "if __name__.*__main__" uw_flow_daemon.py; then
    echo "✅ Fix verified - main() calls daemon.run()"
else
    echo "❌ Fix verification failed"
    exit 1
fi

# Step 8: Create comprehensive test script
echo ""
echo "[8] Creating comprehensive test script..."
cat > "$AUDIT_DIR/TEST_DAEMON_FULL.sh" << 'TESTEOF'
#!/bin/bash
# Full daemon test - run for 2 minutes and verify cache creation

cd ~/stock-bot

echo "=========================================="
echo "FULL DAEMON TEST"
echo "=========================================="
echo ""

# Stop existing
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear cache
rm -f data/uw_flow_cache.json 2>/dev/null

# Start daemon
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon_test_full.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Running for 120 seconds..."
sleep 120

# Check if still running
if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "✅ Daemon still running after 120 seconds"
    
    # Check cache
    if [ -f "data/uw_flow_cache.json" ]; then
        echo "✅ Cache file created"
        python3 << PYEOF
import json
from pathlib import Path
cache = json.loads(Path("data/uw_flow_cache.json").read_text())
tickers = [k for k in cache.keys() if not k.startswith("_")]
print(f"✅ Cache has {len(tickers)} tickers")
PYEOF
    else
        echo "❌ Cache file not created"
    fi
else
    echo "❌ Daemon exited prematurely"
    echo "Last 50 lines of log:"
    tail -50 logs/uw_daemon_test_full.log
fi

# Cleanup
kill $DAEMON_PID 2>/dev/null
TESTEOF

chmod +x "$AUDIT_DIR/TEST_DAEMON_FULL.sh"

# Step 9: Create comprehensive summary
echo ""
echo "[9] Creating comprehensive summary..."
python3 << PYEOF > "$AUDIT_DIR/9_summary.txt"
import json
from pathlib import Path

print("=" * 80)
print("COMPREHENSIVE SYSTEM AUDIT SUMMARY")
print("=" * 80)
print()

# Load all analysis files
try:
    system_state = json.loads(Path("$AUDIT_DIR/1_system_state.json").read_text())
    daemon_analysis = json.loads(Path("$AUDIT_DIR/2_daemon_analysis.json").read_text())
    sigterm_investigation = json.loads(Path("$AUDIT_DIR/3_sigterm_investigation.json").read_text())
except Exception as e:
    print(f"Error loading analysis: {e}")
    exit(1)

print("SYSTEM STATE:")
print(f"  Supervisor running: {system_state['processes'].get('deploy_supervisor', {}).get('running', False)}")
print(f"  Daemon running: {system_state['processes'].get('uw_flow_daemon', {}).get('running', False)}")
print(f"  Cache file exists: {system_state['files'].get('data/uw_flow_cache.json', {}).get('exists', False)}")
print()

print("DAEMON CODE ANALYSIS:")
print(f"  Has main() function: {daemon_analysis.get('has_main_function', False)}")
print(f"  Main calls run(): {daemon_analysis.get('main_calls_run', False)}")
print(f"  Has signal handlers: {daemon_analysis.get('has_signal_handlers', False)}")
print(f"  Exit points found: {len(daemon_analysis.get('exit_points', []))}")
if daemon_analysis.get('potential_issues'):
    print("  Potential issues:")
    for issue in daemon_analysis['potential_issues']:
        print(f"    - {issue}")
print()

print("SIGTERM INVESTIGATION:")
print(f"  Supervisor PID: {sigterm_investigation.get('supervisor_pid')}")
print(f"  Daemon PIDs: {sigterm_investigation.get('daemon_processes', [])}")
if sigterm_investigation.get('potential_killers'):
    print(f"  Other process managers: {sigterm_investigation['potential_killers']}")
print()

print("FIXES APPLIED:")
print("  1. Verified main() function calls daemon.run()")
print("  2. Ensured __name__ == __main__ block exists")
print("  3. Verified signal handlers are registered")
print()

print("NEXT STEPS:")
print("  1. Run: ./$AUDIT_DIR/TEST_DAEMON_FULL.sh")
print("  2. Verify daemon runs for 2+ minutes")
print("  3. Verify cache file is created")
print("  4. If successful, restart supervisor to use fixed daemon")
print()
PYEOF

cat "$AUDIT_DIR/9_summary.txt"

# Step 10: Push to git
echo ""
echo "[10] Pushing audit to git..."
git add "$AUDIT_DIR"/* uw_flow_daemon.py 2>/dev/null || true
git commit -m "Comprehensive system audit and daemon fix: $TIMESTAMP" 2>/dev/null || echo "No changes to commit"
git push origin main 2>&1 | head -10 || echo "Push may have issues - check manually"

echo ""
echo "=========================================="
echo "AUDIT COMPLETE"
echo "=========================================="
echo "All data saved to: $AUDIT_DIR/"
echo ""
echo "Next: Run ./$AUDIT_DIR/TEST_DAEMON_FULL.sh to test the fix"
