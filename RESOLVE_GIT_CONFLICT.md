# Resolve Git Conflict - Quick Fix

## Problem
Git merge conflict with `CHECK_DAEMON_AND_TRADES.sh`

## Solution (Copy/Paste)

```bash
cd /root/stock-bot

# Discard local changes and use the fixed version from git
git checkout --theirs CHECK_DAEMON_AND_TRADES.sh

# Pull latest changes
git pull origin main --no-rebase

# Now run the diagnostic
chmod +x CHECK_DAEMON_AND_TRADES.sh
./CHECK_DAEMON_AND_TRADES.sh
```

## Alternative: Stash and Pull

```bash
cd /root/stock-bot

# Stash local changes
git stash

# Pull latest
git pull origin main --no-rebase

# Run diagnostic
chmod +x CHECK_DAEMON_AND_TRADES.sh CHECK_SUPERVISOR_OUTPUT.sh
./CHECK_DAEMON_AND_TRADES.sh
```
