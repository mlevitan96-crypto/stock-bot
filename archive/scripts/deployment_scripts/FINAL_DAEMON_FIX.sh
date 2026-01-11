#!/bin/bash
# Final comprehensive fix - properly handles string insertion

cd ~/stock-bot

echo "=========================================="
echo "FINAL COMPREHENSIVE DAEMON FIX"
echo "=========================================="
echo ""

# Backup
echo "[1] Creating backup..."
BACKUP_FILE="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"
echo ""

# Apply fix using a Python script file to avoid heredoc issues
echo "[2] Creating temporary fix script..."
cat > /tmp/fix_daemon.py << 'PYSCRIPT'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check current state
has_safe_print = "def safe_print" in content
has_run_fix = "run() method called" in content

print(f"Current state:")
print(f"  safe_print defined: {has_safe_print}")
print(f"  run() fix applied: {has_run_fix}")

# Step 1: Add safe_print if missing
if not has_safe_print:
    print("\n[Step 1] Adding safe_print function...")
    # Find insertion point (after dotenv import)
    lines = content.split('\n')
    new_lines = []
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if "from dotenv import load_dotenv" in line and not inserted:
            new_lines.append('')
            new_lines.append('# Signal-safe print function to avoid reentrant call issues')
            new_lines.append('_print_lock = False')
            new_lines.append('def safe_print(*args, **kwargs):')
            new_lines.append('    """Print that\'s safe to call from signal handlers and avoids reentrant calls."""')
            new_lines.append('    global _print_lock')
            new_lines.append('    if _print_lock:')
            new_lines.append('        return  # Prevent reentrant calls')
            new_lines.append('    _print_lock = True')
            new_lines.append('    try:')
            new_lines.append('        msg = \' \'.join(str(a) for a in args) + \'\\n\'')
            new_lines.append('        os.write(1, msg.encode())  # stdout file descriptor is 1')
            new_lines.append('    except:')
            new_lines.append('        pass  # If print fails, just continue')
            new_lines.append('    finally:')
            new_lines.append('        _print_lock = False')
            new_lines.append('')
            inserted = True
    
    if inserted:
        content = '\n'.join(new_lines)
        print("✅ safe_print added")
    else:
        print("❌ Could not find insertion point")
        exit(1)
else:
    print("\n[Step 1] safe_print already exists - skipping")

# Step 2: Verify run() fix
if not has_run_fix:
    print("\n[Step 2] Adding run() method fix...")
    lines = content.split('\n')
    new_lines = []
    i = 0
    found_run = False
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        if line.strip() == "def run(self):" and not found_run:
            found_run = True
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                i += 1
            new_lines.append('        safe_print("[UW-DAEMON] run() method called")')
            new_lines.append('        safe_print(f"[UW-DAEMON] self.running = {self.running}")')
            new_lines.append('')
        
        i += 1
    
    if found_run:
        content = '\n'.join(new_lines)
        print("✅ run() method fix added")
    else:
        print("❌ Could not find run() method")
        exit(1)
else:
    print("\n[Step 2] run() fix already applied - skipping")

# Write fixed content
file_path.write_text(content)
print("\n✅ Comprehensive fix applied successfully")
PYSCRIPT

echo "[3] Running fix script..."
cd ~/stock-bot
python3 /tmp/fix_daemon.py

if [ $? -ne 0 ]; then
    echo "❌ Fix failed - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

echo ""

# Verify syntax
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

# Verify fixes
echo "[5] Verifying fixes..."
if grep -q "def safe_print" uw_flow_daemon.py && grep -q "run() method called" uw_flow_daemon.py; then
    echo "✅ Both fixes verified"
    echo ""
    echo "safe_print location:"
    grep -n "^def safe_print" uw_flow_daemon.py
    echo ""
    echo "run() method start:"
    grep -A 4 "^    def run(self):" uw_flow_daemon.py | head -6
else
    echo "❌ Verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIX APPLIED - TESTING NOW"
echo "=========================================="
echo ""

./TEST_DAEMON_STARTUP.sh
