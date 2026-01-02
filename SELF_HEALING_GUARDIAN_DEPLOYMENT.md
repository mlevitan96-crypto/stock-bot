# Self-Healing Guardian Deployment Guide

**Date:** 2026-01-02  
**Status:** ✅ DEPLOYED

---

## Overview

The Guardian Wrapper (`guardian_wrapper.sh`) provides a self-healing layer for cron jobs, automatically recovering from common failures detected during pre-market and post-market health checks.

---

## Features

### Automatic Recovery Actions

1. **UW Socket Failures**
   - Detects connection errors, timeouts, or socket failures
   - **Action:** Kills `uw_flow_daemon.py` and restarts it (via process-compose or supervisor)

2. **Alpaca SIP Delay**
   - Detects SIP feed errors or delays
   - **Action:** Logs critical alert and re-initializes Alpaca Client by restarting trading bot

3. **Stale Metadata Locks**
   - Always checked and cleared during recovery
   - **Action:** Removes all `.lock` files in `state/` directory to prevent process hanging

### Exit Code Handling

- **Exit Code 0 (Healthy):** No action needed
- **Exit Code 1 (Degraded):** Recovery actions triggered
- **Exit Code 2 (Unhealthy):** Recovery actions triggered + re-verification
- **Other Exit Codes:** Logged as unexpected errors

---

## Installation

### 1. Make Script Executable

```bash
cd ~/stock-bot
chmod +x guardian_wrapper.sh
```

### 2. Add to Crontab

```bash
# Pre-market health check (9:15 AM ET / 14:15 UTC, Mon-Fri)
(crontab -l 2>/dev/null; echo "15 14 * * 1-5 cd /root/stock-bot && bash guardian_wrapper.sh pre_market_health_check.py >> logs/pre_market.log 2>&1") | crontab -
```

### 3. Verify Crontab Entry

```bash
crontab -l | grep guardian_wrapper
```

---

## Usage

### Manual Execution

```bash
# Run health check through guardian
bash guardian_wrapper.sh pre_market_health_check.py

# Run other scripts through guardian
bash guardian_wrapper.sh friday_eow_audit.py
```

### Logs

Guardian logs are written to:
- **Main log:** `logs/guardian.log`
- **Script output:** `logs/guardian_<script_name>_output.log`
- **Retry attempts:** `logs/guardian_retry_<script_name>.log`
- **Critical alerts:** `logs/alpaca_sip_alert_<timestamp>.txt`

---

## Recovery Logic

### Detection Methods

1. **Exit Code Analysis:** Script exit codes determine recovery triggers
2. **Output Analysis:** For `pre_market_health_check.py`, analyzes output for specific failure patterns:
   - UW failures: `connection_error`, `timeout`, `UW.*fail`, `socket.*fail`
   - Alpaca delays: `SIP.*delay`, `sip_feed.*error`, `sip_feed.*no_data`

### Recovery Sequence

1. **Clear Stale Locks:** Always executed first (safe operation)
2. **UW Daemon Restart:** If UW failures detected
3. **Alpaca Re-init:** If SIP delay detected
4. **Wait for Stabilization:** 5 second wait after recovery actions
5. **Re-verification:** Re-run health check to confirm recovery

### Process Management

The guardian supports multiple process management systems:

1. **process-compose** (Preferred):
   ```bash
   process-compose restart uw-daemon
   process-compose restart trading-bot
   ```

2. **Supervisor/Systemd**:
   ```bash
   pkill -f uw_flow_daemon.py  # Supervisor will auto-restart
   pkill -f python.*main.py    # Supervisor will auto-restart
   ```

---

## Monitoring

### Check Guardian Activity

```bash
# View recent guardian activity
tail -50 logs/guardian.log

# Check for recovery events
grep -i "recovery\|restart\|clear" logs/guardian.log | tail -20

# Check critical alerts
ls -lth logs/alpaca_sip_alert_*.txt 2>/dev/null | head -5
```

### Verify Recovery Success

```bash
# Check if UW daemon is running after recovery
pgrep -f uw_flow_daemon.py

# Check process-compose status
process-compose status

# Verify no stale locks
find state/ -name "*.lock" 2>/dev/null
```

---

## Testing

### Manual Test

```bash
# Test guardian wrapper with health check
bash guardian_wrapper.sh pre_market_health_check.py

# Expected: If healthy, exits with 0. If degraded/unhealthy, performs recovery.
```

### Simulated Failure Test

```bash
# Create a test script that exits with code 2
cat > test_unhealthy.py << 'EOF'
#!/usr/bin/env python3
import sys
print("Simulating unhealthy state")
sys.exit(2)
EOF

chmod +x test_unhealthy.py

# Run through guardian
bash guardian_wrapper.sh test_unhealthy.py

# Check logs
tail -30 logs/guardian.log
```

---

## Troubleshooting

### Guardian Not Running

**Symptom:** Cron job not executing

**Check:**
```bash
# Verify crontab entry exists
crontab -l | grep guardian

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify script is executable
ls -la guardian_wrapper.sh
```

### Recovery Not Working

**Symptom:** Guardian runs but recovery doesn't trigger

**Check:**
```bash
# Verify exit codes are being caught
grep "exit code" logs/guardian.log | tail -10

# Check if recovery function is called
grep "Recovery triggered" logs/guardian.log

# Verify process management system
which process-compose
ps aux | grep deploy_supervisor
```

### Excessive Restarts

**Symptom:** Guardian keeps restarting services

**Solution:** Check underlying issue causing repeated failures:
```bash
# Check UW daemon logs
tail -50 logs/uw-daemon-pc.log

# Check main bot logs
tail -50 logs/trading-bot-pc.log

# Check system resources
free -h
df -h
```

---

## Integration with Existing Systems

### Compatible With

- ✅ `pre_market_health_check.py` (primary use case)
- ✅ `friday_eow_audit.py` (post-market audit)
- ✅ Any Python script that uses exit codes 0/1/2

### Process Management Compatibility

- ✅ process-compose (auto-restart on kill)
- ✅ deploy_supervisor.py (auto-restart on kill)
- ✅ systemd (via service restart)
- ✅ Manual process management (with manual restart logic)

---

## Security Considerations

1. **File Permissions:** Ensure `guardian_wrapper.sh` is only writable by root/owner
2. **Log Rotation:** Set up log rotation for `logs/guardian.log`
3. **Alert Monitoring:** Monitor `logs/alpaca_sip_alert_*.txt` for critical issues
4. **Process Limits:** Guardian will not restart processes indefinitely (supervisor handles that)

---

## Reference

- **Authoritative Source:** `MEMORY_BANK.md`
- **Related Files:**
  - `pre_market_health_check.py` - Health check script
  - `deploy_supervisor.py` - Process supervisor
  - `process-compose.yaml` - Process management config

---

## Next Steps

1. **Deploy to Droplet:** Pull latest code and make script executable
2. **Add Crontab Entry:** Schedule pre-market health check
3. **Monitor First Run:** Watch logs during first scheduled execution
4. **Tune Recovery:** Adjust recovery actions based on observed failures
