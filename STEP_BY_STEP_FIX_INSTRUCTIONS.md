# Step-by-Step Instructions to Fix Daemon Loop Issue

## Problem
The daemon is not entering the main loop. The code has been fixed locally but can't be pushed to GitHub due to secret scanning protection.

## Solution
We need to manually update the `uw_flow_daemon.py` file on your server with the critical fixes.

---

## STEP 1: Check Current State on Server

Run this on your droplet:

```bash
cd ~/stock-bot

# Check if the fix is already there
grep -n "run() method called" uw_flow_daemon.py

# If you see a line number, the fix is already applied - skip to STEP 3
# If you see nothing, continue to STEP 2
```

---

## STEP 2: Apply the Fix Manually

If the fix is NOT found, run this on your droplet:

```bash
cd ~/stock-bot

# Backup the current file
cp uw_flow_daemon.py uw_flow_daemon.py.backup

# Apply the fix using Python
python3 << 'PYEOF'
from pathlib import Path

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text()

# Check if already fixed
if "run() method called" in content:
    print("✅ Fix already applied")
    exit(0)

# Find the run() method definition
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # Look for: "    def run(self):"
    if line.strip() == "def run(self):":
        # Add the next line (docstring)
        if i + 1 < len(lines):
            new_lines.append(lines[i + 1])
            i += 1
        
        # Add our fix lines
        new_lines.append('        safe_print("[UW-DAEMON] run() method called")')
        new_lines.append('        safe_print(f"[UW-DAEMON] self.running = {self.running}")')
        new_lines.append('')
        i += 1
        continue
    
    i += 1

# Write the fixed content
file_path.write_text('\n'.join(new_lines))
print("✅ Fix applied successfully")
PYEOF

# Verify the fix
grep -A 2 "def run(self):" uw_flow_daemon.py | head -5
```

---

## STEP 3: Test the Fix

Run the test script:

```bash
cd ~/stock-bot
./TEST_DAEMON_STARTUP.sh
```

**What to look for:**
- You should see: `[UW-DAEMON] run() method called`
- You should see: `[UW-DAEMON] Step 1: Variables initialized`
- You should see: `[UW-DAEMON] Step 5.5: Final check passed, entering while loop NOW`
- You should see: `[UW-DAEMON] ✅ SUCCESS: Entered main loop! Cycle 1`

---

## STEP 4: If Still Not Working

If you still don't see "run() method called", the file structure might be different. Run this diagnostic:

```bash
cd ~/stock-bot

# Show the run() method
sed -n '/^    def run(self):/,/^        safe_print/p' uw_flow_daemon.py | head -10

# Check Python syntax
python3 -m py_compile uw_flow_daemon.py && echo "✅ Syntax OK" || echo "❌ Syntax error"
```

Share the output and I'll provide a more targeted fix.

---

## STEP 5: Once Working - Verify Full Functionality

Once you see the daemon entering the loop, run a longer test:

```bash
cd ~/stock-bot

# Stop existing
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear logs
rm -f logs/uw_daemon.log .cursor/debug.log 2>/dev/null
mkdir -p .cursor logs

# Start daemon for 30 seconds
source venv/bin/activate
timeout 30 python3 uw_flow_daemon.py > logs/uw_daemon_test.log 2>&1 || true

# Check results
echo "=== Checking if loop was entered ==="
grep -E "SUCCESS.*Entered main loop|Step 6.*INSIDE while loop|Cycle.*Polling" logs/uw_daemon_test.log | head -10

echo ""
echo "=== Checking for polling activity ==="
grep -i "Polling" logs/uw_daemon_test.log | head -5
```

---

## Expected Results

After applying the fix, you should see:
1. ✅ `[UW-DAEMON] run() method called` - Confirms run() is being called
2. ✅ `[UW-DAEMON] Step 1-5` messages - Shows progress through initialization
3. ✅ `[UW-DAEMON] ✅ SUCCESS: Entered main loop! Cycle 1` - Confirms loop entry
4. ✅ `[UW-DAEMON] Polling market_tide...` - Shows actual polling happening

If you see all of these, the daemon is working correctly!

---

## Troubleshooting

**If you see "run() method called" but not "Step 1":**
- There's an exception between those lines
- Check for error messages in the log

**If you see "Step 5" but not "Step 5.5":**
- The `self.running` flag became False
- Check signal handler logs

**If you see "Step 5.5" but not "Step 6":**
- The while loop condition is failing
- This shouldn't happen - share the output

---

## Next Steps After Fix

Once the daemon is entering the loop:
1. Run it for a longer period (2+ minutes) to verify polling
2. Check that endpoints are being polled
3. Verify cache is being populated
4. Remove the verbose "Step X" logging (or keep it for now)
