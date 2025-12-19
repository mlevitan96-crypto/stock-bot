# Environment Variables Setup Guide

## Problem

Environment variables from `.env` file are only loaded by the Python process (via `python-dotenv`), not by the shell. This means:
- `.env` file exists ✅
- Supervisor loads it via `load_dotenv()` ✅  
- But shell commands can't see those variables ❌

## Solution: Verify Bot is Actually Running

The bot IS running (check supervisor logs show `[trading-bot]`), but environment variables aren't visible in shell because they're only in the Python process.

## How to Check if Bot is Running

```bash
# Method 1: Check processes
ps aux | grep "python.*main.py" | grep -v grep

# Method 2: Check supervisor logs
screen -r supervisor
# Look for [trading-bot] messages

# Method 3: Check if bot is responding
curl http://localhost:8081/health

# Method 4: Check recent activity
tail -20 logs/run.jsonl
```

## How Secrets Are Actually Loaded

1. **deploy_supervisor.py** runs `load_dotenv()` which reads `.env` file
2. Secrets are loaded into the Python process environment
3. Services (main.py, dashboard.py) inherit those environment variables
4. Shell commands DON'T see them (different process)

## Verification: Is Bot Actually Running?

Based on your supervisor logs showing `[trading-bot]` messages, **the bot IS running**. The environment variables are loaded by Python, not visible in shell.

## How to Verify Bot Has Secrets

```bash
# Check if bot can access Alpaca API (proves secrets work)
curl -s http://localhost:8081/health | python3 -m json.tool | grep -i "alpaca\|error"

# Check bot logs for API connection
tail -50 logs/run.jsonl | grep -i "alpaca\|connected\|api"

# Check if positions are being tracked
tail -20 logs/orders.jsonl | tail -5
```

## Best Practice: Environment Variable Management

### Option 1: .env File (Current Setup)
- ✅ Works with deploy_supervisor.py
- ✅ Secrets stay on server
- ✅ Loaded automatically by Python
- ❌ Not visible in shell (expected behavior)

### Option 2: System Environment Variables
```bash
# Export in shell profile
echo 'export UW_API_KEY=your_key' >> ~/.bashrc
echo 'export ALPACA_KEY=your_key' >> ~/.bashrc
echo 'export ALPACA_SECRET=your_secret' >> ~/.bashrc
source ~/.bashrc
```

### Option 3: Systemd EnvironmentFile
If using systemd, specify in service file:
```ini
EnvironmentFile=/root/stock-bot/.env
```

## Current Status Check

Run this to verify everything is working:

```bash
cd ~/stock-bot

# 1. Check if bot process is running
ps aux | grep "python.*main.py" | grep -v grep

# 2. Check if bot is responding
curl -s http://localhost:8081/health 2>/dev/null | python3 -m json.tool | head -10

# 3. Check recent bot activity
tail -5 logs/run.jsonl

# 4. Check supervisor thinks bot is running
screen -r supervisor
# Look for [trading-bot] messages
# Press Ctrl+A then D to detach
```

## Troubleshooting

### If Bot Process Not Running:

1. Check supervisor logs for errors:
```bash
screen -r supervisor
# Look for ERROR messages about missing secrets
```

2. Verify .env file has correct format:
```bash
cat .env | grep -E "UW_API_KEY|ALPACA_KEY|ALPACA_SECRET"
# Should show: KEY=value (no spaces around =)
```

3. Restart supervisor:
```bash
pkill -f deploy_supervisor
cd ~/stock-bot
source venv/bin/activate
python deploy_supervisor.py
```

### If Bot Process IS Running but Not Trading:

1. Check if market is open
2. Check if signals are being generated: `tail logs/signals.jsonl`
3. Check if orders are being placed: `tail logs/orders.jsonl`
4. Check for displacement/exits: `tail logs/displacement.jsonl logs/exit.jsonl`

## Summary

- ✅ `.env` file exists
- ✅ Supervisor loads it via `load_dotenv()`
- ✅ Bot process gets secrets (Python process)
- ❌ Shell doesn't see them (different process - this is NORMAL)
- ✅ Bot IS running (supervisor logs show `[trading-bot]` activity)

The "NOT SET" message in shell is EXPECTED - secrets are only in the Python process, not the shell.
