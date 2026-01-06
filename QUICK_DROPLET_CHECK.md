# Quick Droplet Verification - Trading Readiness

## Run This on Droplet (SSH)

Copy and paste these commands into your SSH session:

```bash
cd /root/stock-bot
git pull origin main
bash VERIFY_DROPLET_READY_FOR_TRADING.sh
```

This will check:
- ✅ Git sync status
- ✅ Service running (trading-bot.service)
- ✅ Processes running (main.py, uw_flow_daemon.py, dashboard.py)
- ✅ Recent fixes deployed (UW signal parser, gate events, SRE Sentinel)
- ✅ SRE metrics status
- ✅ UW cache status
- ✅ Dashboard & API health
- ✅ API keys configured
- ✅ Disk space

## Quick Status Check

```bash
cd /root/stock-bot

# Check service
systemctl status trading-bot.service --no-pager | head -10

# Check processes
ps aux | grep -E "main.py|uw_flow_daemon|dashboard" | grep -v grep

# Check recent commits
git log --oneline -5

# Check dashboard
curl -s http://localhost:5000/health | python3 -m json.tool | head -20

# Check SRE metrics (if exists)
cat state/sre_metrics.json 2>/dev/null | python3 -m json.tool || echo "Not created yet"
```

## If Issues Found

1. **Service not running:**
   ```bash
   systemctl restart trading-bot.service
   systemctl status trading-bot.service
   ```

2. **Code not up to date:**
   ```bash
   git pull origin main
   systemctl restart trading-bot.service
   ```

3. **Processes missing:**
   ```bash
   systemctl restart trading-bot.service
   sleep 5
   ps aux | grep -E "main.py|uw_flow_daemon|dashboard" | grep -v grep
   ```
