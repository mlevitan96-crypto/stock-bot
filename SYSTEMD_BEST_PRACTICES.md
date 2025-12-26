# Systemd Best Practices for Trading Bot

## Overview

**Systemd is the REQUIRED and STANDARD way to run the trading bot in production.**

This document outlines best practices, configuration, and operational procedures for managing the bot under systemd.

## Why Systemd?

### Benefits
- ✅ **Auto-restart on failure** - Service automatically restarts if process crashes
- ✅ **Auto-start on boot** - Bot starts automatically after server reboot
- ✅ **Process management** - Systemd manages lifecycle, logging, and resource limits
- ✅ **Production standard** - Industry best practice for Linux service management
- ✅ **Monitoring** - Built-in status, logs, and health checks via `systemctl`
- ✅ **Reliability** - More stable than manual process management
- ✅ **Logging** - Centralized logs via `journalctl`
- ✅ **Resource limits** - Can set CPU, memory, and file descriptor limits

## Service Configuration

### Service File Location
`/etc/systemd/system/trading-bot.service`

### Service File Contents
```ini
[Unit]
Description=Algorithmic Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/stock-bot
EnvironmentFile=/root/stock-bot/.env
ExecStart=/root/stock-bot/systemd_start.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Start Script Location
`/root/stock-bot/systemd_start.sh`

### Start Script Contents
```bash
#!/bin/bash
cd /root/stock-bot
source venv/bin/activate
/root/stock-bot/venv/bin/python deploy_supervisor.py
```

**CRITICAL:** Path must be `/root/stock-bot` (hyphen), NOT `/root/stock_bot` (underscore)

## Standard Operations

### Check Service Status
```bash
systemctl status trading-bot.service
```

### Start Service
```bash
systemctl start trading-bot.service
```

### Stop Service
```bash
systemctl stop trading-bot.service
```

### Restart Service
```bash
systemctl restart trading-bot.service
```

### Enable on Boot
```bash
systemctl enable trading-bot.service
```

### Disable on Boot
```bash
systemctl disable trading-bot.service
```

### View Logs (Real-time)
```bash
journalctl -u trading-bot.service -f
```

### View Recent Logs
```bash
journalctl -u trading-bot.service -n 100 --no-pager
```

### View Logs Since Today
```bash
journalctl -u trading-bot.service --since today
```

### Reload After Service File Changes
```bash
systemctl daemon-reload
systemctl restart trading-bot.service
```

## Verification

### Check if Service is Active
```bash
systemctl is-active trading-bot.service
# Should return: active
```

### Check if Service is Enabled
```bash
systemctl is-enabled trading-bot.service
# Should return: enabled
```

### Verify Process Tree
```bash
# Check deploy_supervisor is running
ps aux | grep deploy_supervisor | grep -v grep

# Check process parent (should be systemd or systemd_start.sh)
ps -eo pid,ppid,comm,args | grep deploy_supervisor | grep -v grep

# Check all bot processes
ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard' | grep -v grep
```

### Expected Process Hierarchy
```
systemd (PID 1)
  └── systemd_start.sh (PID X)
      └── deploy_supervisor.py (PID Y)
          ├── main.py (PID Z)
          ├── uw_flow_daemon.py (PID A)
          └── dashboard.py (PID B)
```

## Troubleshooting

### Service Failing to Start

**Check service status:**
```bash
systemctl status trading-bot.service
```

**Check logs for errors:**
```bash
journalctl -u trading-bot.service -n 50 --no-pager
```

**Common Issues:**

1. **Path Error (Exit Code 127)**
   - **Symptom:** `cd: /root/stock_bot: No such file or directory`
   - **Fix:** Verify start script uses `/root/stock-bot` (hyphen), not `/root/stock_bot` (underscore)

2. **Permission Error**
   - **Symptom:** `Permission denied`
   - **Fix:** Ensure start script is executable: `chmod +x /root/stock-bot/systemd_start.sh`

3. **Python Not Found**
   - **Symptom:** `/root/stock-bot/venv/bin/python: No such file or directory`
   - **Fix:** Verify virtual environment exists: `ls -la /root/stock-bot/venv/bin/python`

4. **Environment File Missing**
   - **Symptom:** Service starts but processes fail
   - **Fix:** Verify `.env` file exists: `ls -la /root/stock-bot/.env`

### Service Running But Processes Not Starting

**Check deploy_supervisor logs:**
```bash
tail -f /root/stock-bot/logs/supervisor.log
```

**Verify virtual environment:**
```bash
/root/stock-bot/venv/bin/python --version
```

**Check dependencies:**
```bash
/root/stock-bot/venv/bin/pip list | grep -E 'alpaca|flask|requests'
```

### Service Restarting Continuously

**Check restart count:**
```bash
systemctl status trading-bot.service | grep "restart counter"
```

**Check logs for crash reason:**
```bash
journalctl -u trading-bot.service -n 100 --no-pager | grep -E "error|Error|Exception|Traceback"
```

## Best Practices

### 1. Always Use Systemd
- ✅ **DO:** Run bot under systemd service
- ❌ **DON'T:** Run manually with nohup, screen, or tmux in production

### 2. Enable on Boot
- ✅ **DO:** Enable service with `systemctl enable`
- ❌ **DON'T:** Leave service disabled (won't start on reboot)

### 3. Monitor Service Health
- ✅ **DO:** Regularly check `systemctl status trading-bot.service`
- ✅ **DO:** Monitor logs with `journalctl -u trading-bot.service -f`
- ❌ **DON'T:** Ignore service failures

### 4. Use Restart Policy
- ✅ **DO:** Keep `Restart=always` in service file
- ✅ **DO:** Set appropriate `RestartSec=10` (10 seconds between restarts)
- ❌ **DON'T:** Disable restart policy without good reason

### 5. Centralized Logging
- ✅ **DO:** Use `journalctl` for all service logs
- ✅ **DO:** Set `StandardOutput=journal` and `StandardError=journal` in service file
- ❌ **DON'T:** Redirect logs to files manually (systemd handles this)

### 6. Resource Limits (Optional)
Add to service file if needed:
```ini
[Service]
MemoryLimit=2G
CPUQuota=200%
```

## Integration with Deployment

### Deployment Scripts Must:
1. Check systemd service status before deployment
2. Stop service if needed: `systemctl stop trading-bot.service`
3. Deploy code changes
4. Reload systemd if service file changed: `systemctl daemon-reload`
5. Start service: `systemctl start trading-bot.service`
6. Verify service is running: `systemctl is-active trading-bot.service`

### Example Deployment Flow
```bash
# 1. Stop service
systemctl stop trading-bot.service

# 2. Deploy code
cd /root/stock-bot
git pull origin main
pip install -r requirements.txt

# 3. Reload if service file changed
systemctl daemon-reload

# 4. Start service
systemctl start trading-bot.service

# 5. Verify
systemctl status trading-bot.service
```

## References

- **Service File:** `/etc/systemd/system/trading-bot.service`
- **Start Script:** `/root/stock-bot/systemd_start.sh`
- **Supervisor:** `/root/stock-bot/deploy_supervisor.py`
- **Logs:** `journalctl -u trading-bot.service`
- **Status:** `systemctl status trading-bot.service`

## Last Updated
2025-12-26 - Systemd service configured and running as standard

