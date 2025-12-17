# Verify Tabs Are Working

## Step 1: Check if you pulled the latest code

```bash
cd /root/stock-bot
git log --oneline -3
```

You should see: "Add tab navigation to main dashboard for Positions and SRE Monitoring"

## Step 2: Verify the code is in dashboard.py

```bash
cd /root/stock-bot
grep -n "\.tabs {" dashboard.py
```

Should show line numbers around 120-125.

## Step 3: Check if dashboard process is running old code

```bash
cd /root/stock-bot
ps aux | grep dashboard | grep -v grep
# Note the PID, then check when it started
ps -p <PID> -o lstart
```

## Step 4: Force restart dashboard with new code

```bash
cd /root/stock-bot
source venv/bin/activate
git pull origin main --no-rebase
pkill -f "python.*dashboard.py"
sleep 3
nohup python3 dashboard.py > logs/dashboard-restart.log 2>&1 &
sleep 3
curl -s http://localhost:5000/ | grep -o "\.tabs" | head -1
```

If you see ".tabs" in the output, the tabs are in the HTML.

## Step 5: Check browser console for errors

Open browser dev tools (F12) and check the Console tab for JavaScript errors.

## Quick All-in-One Fix

```bash
cd /root/stock-bot && source venv/bin/activate && git pull origin main --no-rebase && pkill -f "python.*dashboard.py" && sleep 3 && nohup python3 dashboard.py > logs/dashboard-restart.log 2>&1 & sleep 5 && echo "Dashboard restarted. Check http://your-server:5000/" && tail -5 logs/dashboard-restart.log
```
