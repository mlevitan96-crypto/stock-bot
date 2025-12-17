# Droplet Quick Start - Diagnostic Tools

## Copy/Paste Ready Commands for Your Ubuntu Droplet

### Step 1: Find Your Stock-Bot Directory

```bash
# Try to find where your bot is located
find /root -type d -name "*stock*" 2>/dev/null
find /opt -type d -name "*stock*" 2>/dev/null
find /home -type d -name "*stock*" 2>/dev/null
```

Common locations:
- `/root/stock_bot` (from systemd_start.sh)
- `/opt/trading-bot` (from README.md)
- `~/stock-bot` (home directory)

### Step 2: Navigate and Pull Latest

```bash
# Replace with your actual path once found
cd /root/stock_bot

# Pull latest changes
git pull origin main
```

### Step 3: Run Diagnostic

```bash
# File-based check (works even if services aren't running)
python3 check_system_health.py

# OR API-based check (requires services to be running)
python3 check_trades_api.py
```

## If You Get "Command 'python' not found"

Ubuntu uses `python3` not `python`. Always use:
- `python3` instead of `python`
- `pip3` instead of `pip` (if not using venv)

## If You Get "fatal: not a git repository"

You're not in the stock-bot directory. Run:
```bash
# Find the directory first
find /root -name ".git" -type d 2>/dev/null | head -1

# Then navigate to the parent directory
cd /root/stock_bot  # or wherever the .git folder is
```

## Complete One-Liner (After Finding Your Path)

```bash
cd /root/stock_bot && git pull origin main && python3 check_system_health.py
```

## Troubleshooting

### If python3 command not found:
```bash
sudo apt update && sudo apt install -y python3 python3-pip
```

### If requests module missing:
```bash
pip3 install requests
# OR if using venv:
source venv/bin/activate
pip install requests
```

### Check if bot is running:
```bash
# Check process-compose
process-compose ps

# OR check systemd service
systemctl status trading-bot

# OR check running Python processes
ps aux | grep python
```
