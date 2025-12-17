# Deployment Notes - Diagnostic Tools

## What Was Done

All diagnostic tools have been committed and pushed to git. The following files are now available:

### Diagnostic Tools Added:
1. **`check_system_health.py`** - Comprehensive file-based health checker
2. **`check_trades_api.py`** - API-based health checker (requires requests module)
3. **`check_status.ps1`** - PowerShell script for Windows
4. **`HOW_TO_CHECK_TRADES.md`** - Complete troubleshooting guide

## On Your Droplet (Ubuntu)

### First: Find Your Stock-Bot Directory

```bash
# Find where your stock-bot is located
find /root -name "stock-bot" -o -name "stock_bot" 2>/dev/null
# OR check common locations:
ls -la /root/stock_bot 2>/dev/null || ls -la /opt/trading-bot 2>/dev/null || ls -la ~/stock-bot 2>/dev/null
```

### Quick Setup (if needed):

```bash
# Navigate to your stock-bot directory (adjust path as needed)
cd /root/stock_bot  # or wherever your bot is located

# Pull latest changes
git pull origin main

# Ensure requests is installed (should already be in requirements.txt)
# If using venv:
source venv/bin/activate
pip install -r requirements.txt
# OR if not using venv:
pip3 install -r requirements.txt
```

### Usage on Droplet:

#### Option 1: File-based check (works even if services aren't running)
```bash
cd /root/stock_bot  # or your actual path
python3 check_system_health.py
```

#### Option 2: API-based check (requires services to be running)
```bash
cd /root/stock_bot  # or your actual path
python3 check_trades_api.py
```

#### Option 3: Quick one-liner (from any directory)
```bash
cd /root/stock_bot && python3 check_system_health.py
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

### Quick Health Check Commands:

```bash
# First, navigate to your bot directory
cd /root/stock_bot  # or your actual path

# Check health endpoint
curl http://localhost:8081/health | python3 -m json.tool

# Check last order from file
tail -1 data/live_orders.jsonl | python3 -m json.tool

# Check heartbeat
cat state/system_heartbeat.json | python3 -m json.tool
```

### Complete Copy/Paste Ready Commands:

```bash
# Step 1: Find and navigate to your stock-bot directory
cd /root/stock_bot || cd /opt/trading-bot || cd ~/stock-bot

# Step 2: Pull latest changes
git pull origin main

# Step 3: Run diagnostic (choose one)
python3 check_system_health.py
# OR if services are running:
python3 check_trades_api.py
```

## No Action Required

All tools are ready to use. The diagnostic scripts will:
- Auto-detect file locations
- Handle missing files gracefully
- Provide clear status indicators
- Show time ago in human-readable format

Just run the scripts when you need to check system health!
