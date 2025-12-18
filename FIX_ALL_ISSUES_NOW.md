# FIX ALL ISSUES - Step-by-Step Commands

## CRITICAL: Your secrets aren't being loaded!

The supervisor says secrets are missing. You need to load them.

## STEP 1: Check if .env file exists
```bash
cd /root/stock-bot
ls -la .env
```

## STEP 2A: If .env exists, load it
```bash
cd /root/stock-bot
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
```

## STEP 2B: If no .env file, export secrets manually
```bash
export UW_API_KEY="your_uw_key_here"
export ALPACA_KEY="your_alpaca_key_here"
export ALPACA_SECRET="your_alpaca_secret_here"
```

## STEP 3: Kill ALL processes using ports 5000-5003
```bash
cd /root/stock-bot
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 5001/tcp 2>/dev/null || true
fuser -k 5002/tcp 2>/dev/null || true
fuser -k 5003/tcp 2>/dev/null || true
pkill -f dashboard.py 2>/dev/null || true
pkill -f dashboard_proxy 2>/dev/null || true
sleep 2
```

## STEP 4: Verify secrets are loaded
```bash
env | grep -E "UW_API_KEY|ALPACA_KEY|ALPACA_SECRET"
```

You should see all 3 variables. If not, go back to STEP 2.

## STEP 5: Pull latest code (includes .env loading fix)
```bash
cd /root/stock-bot
git pull origin main --no-rebase
```

## STEP 6: Stop old supervisor
```bash
pkill -f deploy_supervisor
sleep 3
```

## STEP 7: Start supervisor (secrets should now be loaded)
```bash
cd /root/stock-bot
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## STEP 8: Wait 60 seconds, then check if services started

Open a NEW terminal and run:
```bash
cd /root/stock-bot
ps aux | grep -E "uw_flow_daemon|main.py|dashboard" | grep -v grep
```

You should see:
- uw_flow_daemon running
- main.py (trading-bot) running  
- dashboard.py running

## STEP 9: Check logs for trades
```bash
cd /root/stock-bot
tail -50 logs/trading-bot-pc.log 2>/dev/null | grep -E "clustering|flow_trades|normalized" | tail -10
```

OR if that log doesn't exist, check supervisor output directly.

## If Still Having Issues

### Check 1: Are secrets actually set?
```bash
echo "UW_API_KEY: ${UW_API_KEY:0:10}..." 
echo "ALPACA_KEY: ${ALPACA_KEY:0:10}..."
```

### Check 2: What's using the ports?
```bash
netstat -tulpn | grep -E "5000|5001|5002"
```

### Check 3: Is daemon running?
```bash
ps aux | grep uw_flow_daemon | grep -v grep
```

If not, check why:
```bash
tail -50 logs/uw-daemon-pc.log 2>/dev/null || echo "No daemon log - check supervisor output"
```
