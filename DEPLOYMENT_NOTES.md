# Deployment Notes - Diagnostic Tools

## What Was Done

All diagnostic tools have been committed and pushed to git. The following files are now available:

### Diagnostic Tools Added:
1. **`check_system_health.py`** - Comprehensive file-based health checker
2. **`check_trades_api.py`** - API-based health checker (requires requests module)
3. **`check_status.ps1`** - PowerShell script for Windows
4. **`HOW_TO_CHECK_TRADES.md`** - Complete troubleshooting guide

## On Your Droplet

### Quick Setup (if needed):

```bash
# Pull latest changes
cd /path/to/stock-bot
git pull origin main

# Ensure requests is installed (should already be in requirements.txt)
pip install -r requirements.txt
```

### Usage on Droplet:

#### Option 1: File-based check (works even if services aren't running)
```bash
python check_system_health.py
```

#### Option 2: API-based check (requires services to be running)
```bash
python check_trades_api.py
```

#### Option 3: Quick status check (if you have PowerShell on Linux)
```bash
# Or use the Python scripts instead
python check_system_health.py
```

### What These Tools Check:

1. **Last Order Status** - Checks `data/live_orders.jsonl` for most recent order timestamp
2. **Doctor/Heartbeat** - Checks `state/system_heartbeat.json` or `state/heartbeat.json`
3. **Alpaca Connectivity** - Verifies API connection and account status
4. **Recent Trades** - Queries Alpaca API for recent filled orders
5. **UW Cache Freshness** - Checks if UW flow cache is being updated
6. **Health Supervisor** - Gets status from health monitoring system

### Understanding Your Yellow Indicators:

- **Last Order: 3 hours old**
  - Normal if market is closed
  - Check if signals are being generated during market hours
  - Verify bot is running: `process-compose ps`

- **Doctor: 50 minutes**
  - Warning range (yellow) but not critical
  - Should be < 5 minutes for healthy
  - Check `heartbeat-keeper` process is running

### Quick Health Check Command:

```bash
# Check health endpoint
curl http://localhost:8081/health | python -m json.tool

# Check last order from file
tail -1 data/live_orders.jsonl | python -m json.tool

# Check heartbeat
cat state/system_heartbeat.json | python -m json.tool
```

## No Action Required

All tools are ready to use. The diagnostic scripts will:
- Auto-detect file locations
- Handle missing files gracefully
- Provide clear status indicators
- Show time ago in human-readable format

Just run the scripts when you need to check system health!
