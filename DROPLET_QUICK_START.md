# Droplet Quick Start - After Git Pull

## You're Already on the Droplet - Here's What to Do Next

### 1. Run Tests (Verify Everything Works)

```bash
# Use python3 (not python)
python3 test_learning_system.py
```

**Expected Output:**
```
TEST SUMMARY: 6 passed, 0 failed
```

### 2. Check How Services Are Running

```bash
# Check if using systemd
sudo systemctl status stock-bot
# OR
sudo systemctl list-units | grep stock

# Check if using screen/tmux
screen -ls
# OR
tmux ls

# Check if running directly
ps aux | grep main.py
ps aux | grep python
```

### 3. Restart Services (Choose Based on Step 2)

#### Option A: If Using systemd
```bash
sudo systemctl restart stock-bot
sudo systemctl status stock-bot  # Verify it's running
```

#### Option B: If Using screen/tmux
```bash
# Find the session
screen -ls
# OR
tmux ls

# Attach and restart
screen -r <session_name>
# Then Ctrl+C to stop, then restart:
python3 main.py
# Then Ctrl+A, D to detach
```

#### Option C: If Running Directly (No Service Manager)
```bash
# Find the process
ps aux | grep main.py

# Kill it
kill <PID>

# Restart (in background or screen)
nohup python3 main.py > logs/bot.log 2>&1 &
# OR
screen -dmS stock-bot python3 main.py
```

#### Option D: If Using process-compose (Install if needed)
```bash
# Install process-compose if not installed
# Check: https://github.com/F1bonacc1/process-compose

# Then:
process-compose down
process-compose up -d
```

### 4. Verify Learning System is Active

```bash
# Check logs
tail -f logs/comprehensive_learning.log

# Check that learning orchestrator is imported
python3 -c "from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator; print('OK')"
```

### 5. Monitor After Restart

```bash
# Watch main log
tail -f logs/trading.log
# OR
tail -f logs/bot.log

# Check for errors
grep -i error logs/*.log | tail -20

# Verify learning cycle will run (after market close)
grep "comprehensive_learning" logs/*.log | tail -10
```

---

## Quick Verification Checklist

- [ ] Tests pass: `python3 test_learning_system.py`
- [ ] Services restarted successfully
- [ ] No errors in logs
- [ ] Trading continues normally
- [ ] Learning orchestrator can be imported

---

## If You Encounter Issues

### Import Errors:
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Install missing dependencies
pip3 install -r requirements.txt
```

### Permission Errors:
```bash
# Check file permissions
ls -la logs/
ls -la data/
ls -la state/

# Fix if needed
chmod 755 logs/ data/ state/
```

### Service Won't Start:
```bash
# Check for port conflicts
netstat -tulpn | grep 5000
netstat -tulpn | grep 8080

# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip3 list | grep -E "flask|alpaca|requests"
```

---

## Next Steps After Restart

1. **Monitor for 24 hours** - Ensure everything works
2. **Check learning cycle** - After market close, verify it runs
3. **Review recommendations** - Check `data/comprehensive_learning.jsonl`
4. **Watch for improvements** - Learning will optimize gradually

---

## Need Help?

Check these files:
- `DROPLET_DEPLOYMENT_GUIDE.md` - Full deployment guide
- `DEPLOYMENT_SUMMARY.md` - Quick reference
- `logs/comprehensive_learning.log` - Learning system logs
