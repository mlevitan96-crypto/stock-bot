# Dashboard Fixes - Deployment Instructions

**Date:** 2026-01-12  
**Status:** ✅ Code pushed to GitHub  
**Commit:** `6d7b3c2` - "Fix dashboard blocking operations and file reading issues"

---

## Quick Deployment (SSH into Droplet)

```bash
# 1. SSH into your droplet
ssh root@104.236.102.57

# 2. Navigate to project directory
cd /root/stock-bot

# 3. Pull latest code
git pull origin main

# 4. Verify the commit
git log -1 --oneline
# Should show: 6d7b3c2 Fix dashboard blocking operations...

# 5. Restart dashboard (choose one method):

# Option A: Kill dashboard process (supervisor will auto-restart)
pkill -f "python.*dashboard.py"
sleep 5
ps aux | grep dashboard | grep -v grep

# Option B: Restart via systemd (if using systemd)
systemctl restart trading-bot.service
systemctl status trading-bot.service

# Option C: Restart supervisor (if using supervisor)
pkill -f deploy_supervisor
sleep 2
source venv/bin/activate
python3 deploy_supervisor.py &

# 6. Verify dashboard is responding
curl http://localhost:5000/health
# Should return: {"status":"healthy",...}

# 7. Test the fixed endpoint
curl http://localhost:5000/api/health_status | python3 -m json.tool
```

---

## What Was Fixed

### 1. **Blocking File Read Operations** ✅
- **Problem:** Dashboard was reading entire log files into memory using `readlines()`
- **Fix:** Now reads only last ~50KB (last 500 lines) efficiently
- **Impact:** Dashboard no longer hangs on large log files

### 2. **Large File Processing** ✅
- **Problem:** XAI Auditor reading entire attribution files (10,000+ lines)
- **Fix:** Added 10,000 line limit and optimized reading for large files
- **Impact:** Fast response times even with large log files

### 3. **Error Handling** ✅
- **Status:** All 17 endpoints verified to return valid JSON on errors
- **Impact:** Dashboard never crashes, always returns valid responses

---

## Verification Steps

After deployment, verify the fixes:

```bash
# 1. Check dashboard is running
ps aux | grep dashboard | grep -v grep

# 2. Test health endpoint
curl http://localhost:5000/health

# 3. Test positions endpoint (should be fast even with large logs)
time curl http://localhost:5000/api/positions

# 4. Test XAI auditor (should handle large files)
time curl http://localhost:5000/api/xai/auditor

# 5. Check dashboard logs for errors
tail -50 logs/dashboard*.log
```

---

## Expected Results

✅ **Dashboard responds quickly** (even with large log files)  
✅ **No memory issues** (efficient file reading)  
✅ **All endpoints return valid JSON** (proper error handling)  
✅ **Dashboard accessible at http://104.236.102.57:5000/**

---

## If Dashboard Still Not Accessible

1. **Check if dashboard is running:**
   ```bash
   ps aux | grep dashboard | grep -v grep
   ```

2. **Check if port 5000 is listening:**
   ```bash
   netstat -tlnp | grep 5000
   # OR
   ss -tlnp | grep 5000
   ```

3. **Check firewall:**
   ```bash
   ufw status
   # If port 5000 is blocked, allow it:
   ufw allow 5000/tcp
   ```

4. **Check dashboard logs:**
   ```bash
   tail -100 logs/dashboard*.log
   # Look for errors or import issues
   ```

5. **Manually start dashboard (for testing):**
   ```bash
   cd /root/stock-bot
   source venv/bin/activate
   python3 dashboard.py
   # Check for any import errors or startup issues
   ```

---

## Troubleshooting

### Dashboard won't start
- Check Python dependencies: `pip3 install flask alpaca-trade-api`
- Check for import errors: `python3 -c "import dashboard"`
- Check logs: `tail -50 logs/dashboard*.log`

### Dashboard starts but not accessible externally
- Check firewall: `ufw status`
- Check if binding to 0.0.0.0: `grep "0.0.0.0" dashboard.py`
- Check nginx/proxy config if using reverse proxy

### Dashboard hangs on requests
- Check if old code is still running: `ps aux | grep dashboard`
- Kill old process: `pkill -f dashboard.py`
- Restart: Follow deployment steps above

---

**Deployment Status:** ✅ Code ready on GitHub  
**Next Step:** SSH into droplet and run deployment commands above
