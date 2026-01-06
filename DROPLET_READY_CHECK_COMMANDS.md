# Droplet Trading Readiness Check - Ready for Tomorrow

## Quick Verification (Run on Droplet)

**SSH into your droplet and run:**

```bash
cd /root/stock-bot
git pull origin main
bash VERIFY_DROPLET_READY_FOR_TRADING.sh
```

## Manual Quick Checks

If you want to check things individually:

```bash
cd /root/stock-bot

# 1. Git Status
git log --oneline -1
git status

# 2. Service Status  
systemctl status trading-bot.service --no-pager | head -10

# 3. Processes Running
ps aux | grep -E "main.py|uw_flow_daemon.py|dashboard.py|deploy_supervisor" | grep -v grep

# 4. Dashboard Health
curl -s http://localhost:5000/health | python3 -m json.tool | head -20

# 5. Bot API Health
curl -s http://localhost:8081/health | python3 -m json.tool | head -20

# 6. Recent Fixes Present
grep -c "signal_type.*BULLISH_SWEEP" main.py && echo "UW parser fix: OK" || echo "UW parser fix: MISSING"
grep -c "gate_type=" main.py && echo "Gate logging fix: OK" || echo "Gate logging fix: MISSING"

# 7. SRE Sentinel Files
ls -la sre_diagnostics.py mock_signal_injection.py 2>/dev/null && echo "SRE Sentinel: OK" || echo "SRE Sentinel: FILES MISSING"

# 8. UW Cache
python3 -c "import json; c=json.load(open('data/uw_flow_cache.json')); print(f'UW Cache: {len([k for k in c.keys() if not k.startswith(\"_\")])} symbols')" 2>/dev/null || echo "UW Cache: FILE MISSING"

# 9. API Keys
grep -q "UW_API_KEY=" .env && grep -q "ALPACA_KEY=" .env && echo "API Keys: CONFIGURED" || echo "API Keys: MISSING"
```

## Critical Checks Summary

**Must be OK for trading:**
1. ✅ Service running (`systemctl status trading-bot.service`)
2. ✅ Processes running (main.py, uw_flow_daemon.py, dashboard.py)
3. ✅ API keys configured (.env file)
4. ✅ Code up to date (`git pull origin main`)
5. ✅ Recent fixes deployed (UW parser, gate events, SRE Sentinel)

**Nice to have:**
- SRE metrics file (created after first mock signal run - 15 min after restart)
- UW cache populated (depends on API and daemon)

## If Issues Found

**Service not running:**
```bash
systemctl restart trading-bot.service
systemctl status trading-bot.service
```

**Code not synced:**
```bash
git pull origin main
systemctl restart trading-bot.service
```

**Processes missing:**
```bash
systemctl restart trading-bot.service
sleep 5
ps aux | grep -E "main.py|uw_flow_daemon|dashboard" | grep -v grep
```
