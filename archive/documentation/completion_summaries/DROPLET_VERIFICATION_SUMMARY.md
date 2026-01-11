# Droplet Verification Summary - Trading Readiness

**Date:** 2026-01-05  
**Status:** Verification scripts created and deployed

## What Was Created

1. **`VERIFY_DROPLET_READY_FOR_TRADING.sh`** - Comprehensive bash verification script
   - Checks Git sync, services, processes, fixes, SRE metrics, cache, dashboard, API keys, disk space
   - Provides clear pass/fail summary

2. **`DROPLET_READY_CHECK_COMMANDS.md`** - Quick reference guide with manual commands

3. **`QUICK_DROPLET_CHECK.md`** - Alternative verification methods

## How to Run Verification

### Option 1: Automated Script (Recommended)

**SSH into droplet and run:**
```bash
cd /root/stock-bot
git pull origin main
bash VERIFY_DROPLET_READY_FOR_TRADING.sh
```

### Option 2: Manual Checks

See `DROPLET_READY_CHECK_COMMANDS.md` for step-by-step manual verification commands.

## What Gets Checked

1. **Git Sync** - Code is up to date with remote
2. **Service Status** - trading-bot.service is running
3. **Processes** - main.py, uw_flow_daemon.py, dashboard.py, deploy_supervisor.py
4. **Recent Fixes** - UW signal parser, gate events, SRE Sentinel modules
5. **SRE Metrics** - Mock signal injection status (if run)
6. **UW Cache** - Cache file exists and has symbols
7. **Dashboard** - Responding on port 5000
8. **Bot API** - Responding on port 8081
9. **API Keys** - UW_API_KEY and ALPACA_KEY configured
10. **Disk Space** - Sufficient free space

## Expected Results

**All Critical Checks Should Pass:**
- ✅ Git up to date
- ✅ Service running
- ✅ All processes running
- ✅ Recent fixes deployed
- ✅ API keys configured
- ✅ Dashboard and API responding

**Warnings (May Be Normal):**
- SRE metrics file not created yet (created after first mock signal - 15 min after restart)
- UW cache empty (if API hasn't returned data yet)

## Next Steps

1. **SSH into droplet**
2. **Run verification script:**
   ```bash
   cd /root/stock-bot
   git pull origin main
   bash VERIFY_DROPLET_READY_FOR_TRADING.sh
   ```
3. **Review output** - Should see "ALL CHECKS PASSED - READY FOR TRADING"
4. **If errors found** - Fix them using the troubleshooting commands in the script output

## Files Location on Droplet

- Verification script: `/root/stock-bot/VERIFY_DROPLET_READY_FOR_TRADING.sh`
- Quick check guide: `/root/stock-bot/DROPLET_READY_CHECK_COMMANDS.md`
- Code: `/root/stock-bot/`

---

**Status:** ✅ Verification scripts created and ready to use on droplet.
