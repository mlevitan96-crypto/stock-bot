#!/bin/bash
# Comprehensive fix for daemon - adds safe_print and all fixes

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE DAEMON FIX"
echo "=========================================="
echo ""

# Backup
echo "[1] Creating backup..."
BACKUP_FILE="uw_flow_daemon.py.backup.$(date +%Y%m%d_%H%M%S)"
cp uw_flow_daemon.py "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"
echo ""

# Apply comprehensive fix
echo "[2] Applying comprehensive fix..."
python3 << 'PYEOF'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if safe_print exists
has_safe_print = "def safe_print" in content
has_run_fix = "run() method called" in content

print(f"Current state:")
print(f"  safe_print defined: {has_safe_print}")
print(f"  run() fix applied: {has_run_fix}")

# Step 1: Add safe_print if missing
if not has_safe_print:
    print("\n[Step 1] Adding safe_print function...")
    # Find where to insert (after imports, before debug_log)
    import_pattern = "from dotenv import load_dotenv"
    safe_print_def = '''# Signal-safe print function to avoid reentrant call issues
_print_lock = False
def safe_print(*args, **kwargs):
    """Print that's safe to call from signal handlers and avoids reentrant calls."""
    global _print_lock
    if _print_lock:
        return  # Prevent reentrant calls
    _print_lock = True
    try:
        msg = ' '.join(str(a) for a in args) + '\n'
        os.write(1, msg.encode())  # stdout file descriptor is 1
    except:
        pass  # If print fails, just continue
    finally:
        _print_lock = False

'''
    
    if import_pattern in content:
        # Insert after dotenv import
        lines = content.split('\n')
        new_lines = []
        inserted = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if import_pattern in line and not inserted:
                # Add safe_print after this line
                new_lines.append('')
                new_lines.extend(safe_print_def.strip().split('\n'))
                inserted = True
        content = '\n'.join(new_lines)
        print("✅ safe_print added")
    else:
        print("⚠️  Could not find insertion point for safe_print")
else:
    print("\n[Step 1] safe_print already exists - skipping")

# Step 2: Add run() method fix if missing
if not has_run_fix:
    print("\n[Step 2] Adding run() method fix...")
    # Find run() method and add logging
    lines = content.split('\n')
    new_lines = []
    i = 0
    found_run = False
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Look for def run(self):
        if line.strip() == "def run(self):" and not found_run:
            found_run = True
            # Add next line (docstring) if it exists
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                new_lines.append(lines[i + 1])
                i += 1
            
            # Add our fix
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

# Write the fixed content
file_path.write_text(content)
print("\n✅ Comprehensive fix applied successfully")
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ Fix failed - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

echo ""

# Verify syntax
echo "[3] Verifying Python syntax..."
python3 -m py_compile uw_flow_daemon.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax error - restoring backup"
    cp "$BACKUP_FILE" uw_flow_daemon.py
    exit 1
fi

echo ""

# Verify both fixes
echo "[4] Verifying fixes..."
if grep -q "def safe_print" uw_flow_daemon.py && grep -q "run() method called" uw_flow_daemon.py; then
    echo "✅ Both fixes verified:"
    echo "   - safe_print function exists"
    echo "   - run() method fix applied"
    echo ""
    echo "Showing safe_print definition:"
    grep -A 10 "^def safe_print" uw_flow_daemon.py | head -12
    echo ""
    echo "Showing run() method start:"
    grep -A 4 "^    def run(self):" uw_flow_daemon.py | head -6
else
    echo "❌ Verification failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "COMPREHENSIVE FIX APPLIED"
echo "=========================================="
echo ""
echo "Testing now..."
echo ""

./TEST_DAEMON_STARTUP.sh
