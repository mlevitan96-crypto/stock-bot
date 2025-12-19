# Droplet Diagnostic - Step by Step

## Current Situation Analysis

✅ **Good News:**
- You're in the right directory: `~/stock-bot`
- Git pull worked (you have the new files)
- Bot is running (PID 313404)
- Tests passed

⚠️ **Issues:**
- `python3` can't find `alpaca_trade_api` module
- Bot is running with `python` (not `python3`)
- Screen session seems disconnected
- Logs location unclear

---

## Step 1: Verify You're in the Right Place

```bash
# Confirm you're in stock-bot directory
pwd
# Should show: /root/stock-bot

# Verify git pull worked
ls -la | grep -E "comprehensive_learning|test_learning"
# Should show the new files

# Check git status
git status
# Should show you're on main branch
```

---

## Step 2: Check How Python is Set Up

```bash
# Check what 'python' points to
which python
python --version

# Check what 'python3' points to
which python3
python3 --version

# Check if there's a virtual environment
ls -la | grep venv
ls -la | grep .venv

# Check if bot is using a venv
ps aux | grep main.py | grep -E "venv|virtualenv"
```

---

## Step 3: Find Where Dependencies Are Installed

```bash
# Check if bot process is using a venv
ps aux | grep 313404
# Look for the full command path

# Check if there's a requirements.txt
cat requirements.txt | head -20

# Check where python modules are installed for the running process
# (This is tricky - we'll need to check the process environment)
```

---

## Step 4: Check Log Locations

```bash
# Find where logs actually are
find . -name "*.log" -type f 2>/dev/null | head -10
find . -name "trading.log" 2>/dev/null
find . -name "*.jsonl" -type f 2>/dev/null | head -10

# Check if logs directory exists
ls -la logs/ 2>/dev/null || echo "No logs directory"
ls -la data/ 2>/dev/null || echo "No data directory"
```

---

## Step 5: Understand How Bot is Running

The bot is running with `python main.py`. This suggests:
1. Either `python` is aliased to `python3`
2. Or there's a virtual environment activated
3. Or dependencies are installed for `python` but not `python3`

Let's check:

```bash
# See the full command the bot is running
ps aux | grep 313404 | grep -v grep

# Check if there's a startup script
ls -la *.sh
cat start.sh 2>/dev/null
cat systemd_start.sh 2>/dev/null

# Check environment variables of running process
# (This requires root, which you have)
cat /proc/313404/environ | tr '\0' '\n' | grep -E "PATH|VIRTUAL|PYTHON"
```

---

## Step 6: Fix the Issue

### Option A: If Using Virtual Environment

```bash
# Find and activate venv
find . -name "activate" -path "*/venv/bin/activate" 2>/dev/null
find . -name "activate" -path "*/.venv/bin/activate" 2>/dev/null

# If found, activate it
source venv/bin/activate
# OR
source .venv/bin/activate

# Then verify
python --version
python -c "import alpaca_trade_api; print('OK')"
```

### Option B: Install Dependencies for python3

```bash
# Install dependencies
pip3 install -r requirements.txt

# OR if using system python3
sudo pip3 install -r requirements.txt
```

### Option C: Use the Same Python as Running Process

```bash
# Find the exact python being used
readlink -f $(which python)
readlink -f $(which python3)

# If they're different, use the one that works
# (The running process uses 'python', so that one has dependencies)
```

---

## Step 7: Restart Properly

Once you understand the setup:

```bash
# Kill current process
kill 313404

# Wait
sleep 2

# Start with the correct python (whichever has dependencies)
# If using venv:
source venv/bin/activate
python main.py

# OR if python3 now has dependencies:
python3 main.py

# OR if 'python' works:
python main.py
```

---

## Quick Fix (If Bot is Working)

**If the bot is currently trading successfully**, you might not need to restart immediately. The learning system will:
- Work with the existing `python` setup
- Run after market close
- Use whatever Python environment is active

**You can verify learning is working by:**
```bash
# Check if learning orchestrator can be imported with current setup
python -c "from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator; print('OK')"
```

If that works, the learning system is already active and will run automatically!

---

## Recommended Next Steps

1. **First, verify the bot is working** - Check if it's trading
2. **Don't restart if it's working** - Learning will activate automatically
3. **Check after market close** - Verify learning cycle runs
4. **Fix python3 setup later** - Not urgent if bot is working
