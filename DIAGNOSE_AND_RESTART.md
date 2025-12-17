# Diagnose and Restart Dashboard

## Step 1: Check What's Running

```bash
cd /root/stock-bot
ps aux | grep -E "(dashboard|deploy_supervisor|python)" | grep -v grep
```

## Step 2: Check if Dashboard Port is in Use

```bash
netstat -tlnp | grep 5000
# OR
ss -tlnp | grep 5000
```

## Step 3: Check Supervisor Status

```bash
ps aux | grep deploy_supervisor
```

## Step 4: Manual Dashboard Start (if supervisor not running)

```bash
cd /root/stock-bot
source venv/bin/activate
python3 dashboard.py
# Run in background: python3 dashboard.py &
# Or use screen/tmux
```

## Step 5: Check Dashboard Logs

```bash
cd /root/stock-bot
ls -la logs/ | grep dashboard
tail -20 logs/dashboard*.log
```

## Step 6: Test Dashboard Endpoint

```bash
curl -v http://localhost:5000/health
curl -v http://127.0.0.1:5000/health
```
