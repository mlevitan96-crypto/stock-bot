# Restart Dashboard on Droplet

## Option 1: Kill Dashboard Process (Supervisor will auto-restart)

```bash
cd /root/stock-bot
pkill -f "python.*dashboard.py"
# Wait 5-10 seconds for supervisor to restart it
sleep 5
ps aux | grep dashboard
```

## Option 2: Find and Kill by PID

```bash
cd /root/stock-bot
ps aux | grep "dashboard.py"
# Find the PID, then:
kill <PID>
# Wait for supervisor to restart
sleep 5
```

## Option 3: Restart Entire Supervisor (restarts all services)

```bash
cd /root/stock-bot
# Find supervisor PID
ps aux | grep deploy_supervisor
# Kill it (systemd or your process manager will restart it)
# OR if running manually, Ctrl+C and restart:
source venv/bin/activate
python3 deploy_supervisor.py
```

## Verify Dashboard is Running

```bash
curl http://localhost:5000/health
# Should return: {"status":"healthy",...}
```

## Check Dashboard Logs

```bash
tail -f logs/dashboard-pc.log
# OR if using supervisor:
# Check supervisor output or logs/
```
