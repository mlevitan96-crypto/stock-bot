# Droplet Pull Instructions - Monday Ready

**Date:** 2026-01-02  
**Status:** ✅ All code pushed to GitHub

---

## Quick Deployment Command

On your droplet, run:

```bash
cd ~/stock-bot && git pull origin main && echo "Code updated successfully"
```

---

## Full Deployment Process

```bash
# 1. SSH into droplet
ssh user@droplet_ip

# 2. Navigate to project directory
cd ~/stock-bot  # or /root/stock-bot

# 3. Pull latest code
git fetch origin main
git reset --hard origin/main

# 4. Verify latest commit
git log -1 --oneline
# Should show latest commit

# 5. Make guardian wrapper executable
chmod +x guardian_wrapper.sh

# 6. Restart services
# Option A: If using supervisor
pkill -f deploy_supervisor
sleep 2
source venv/bin/activate  # if using venv
python deploy_supervisor.py

# Option B: If using systemd
sudo systemctl restart stock-bot

# Option C: If using process-compose
process-compose down
process-compose up -d
```

---

## Setup Self-Healing Cron Jobs

After deployment, set up the pre-market health check with guardian wrapper:

```bash
# Add to crontab (Run at 9:15 AM ET / 14:15 UTC, Mon-Fri)
(crontab -l 2>/dev/null; echo "15 14 * * 1-5 cd /root/stock-bot && bash guardian_wrapper.sh pre_market_health_check.py >> logs/pre_market.log 2>&1") | crontab -

# Verify crontab entry
crontab -l | grep guardian_wrapper
```

The guardian wrapper will automatically:
- Run the health check
- Detect failures (exit codes 1 or 2)
- Restart UW daemon if connection fails
- Re-initialize Alpaca client if SIP delay detected
- Clear stale lock files
- Re-verify connectivity after recovery

---

## Verification

After pulling, verify the update:

```bash
# Check latest commit
git log -1 --oneline

# Verify API resilience is available
python3 -c "from api_resilience import ExponentialBackoff; print('OK')"

# Verify pre-market health check script exists
ls -la pre_market_health_check.py

# Verify guardian wrapper exists and is executable
ls -la guardian_wrapper.sh

# Test guardian wrapper manually
bash guardian_wrapper.sh pre_market_health_check.py

# Check guardian logs
tail -20 logs/guardian.log
```

---

## Latest Commits

**Latest:** Guardian wrapper for self-healing cron jobs  
**Previous:** `e98de51` - Monday deployment readiness summary

---

## What's Included

- ✅ 100% Institutional Integration Complete
- ✅ API Resilience (exponential backoff, signal queuing)
- ✅ Trade Persistence (full metadata)
- ✅ Portfolio Concentration Gate
- ✅ Correlation ID Pipeline
- ✅ Pre-Market Health Check Script
- ✅ Self-Healing Guardian Wrapper for Cron Jobs

All changes are in GitHub and ready to pull.
