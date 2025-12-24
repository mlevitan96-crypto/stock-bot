# Droplet Git Client Setup - Complete Step-by-Step Guide
## All Commands Run on Droplet Console

**Goal:** Set up git on droplet so Cursor can see everything happening through git, eliminating copy/paste.

**Repository:** https://github.com/mlevitan96-crypto/stock-bot  
**Droplet IP:** 104.236.102.57  
**Username:** mlevitan96-crypto

---

## Step 1: Navigate to Project Directory

```bash
cd ~/stock-bot
```

---

## Step 2: Configure Git (One-Time Setup)

Set your git identity and configure git to avoid merge editor issues:

```bash
cd ~/stock-bot
git config user.name "mlevitan96-crypto"
git config user.email "mlevitan96-crypto@users.noreply.github.com"
git config pull.rebase false
git config core.editor true
git config merge.commit no-edit
```

**Verify configuration:**
```bash
git config --list | grep -E "user|pull|core|merge"
```

---

## Step 3: Set Up GitHub Authentication

**Option A: Using Personal Access Token (Recommended)**

Set up git to use your token for authentication:

```bash
cd ~/stock-bot
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/mlevitan96-crypto/stock-bot.git
```

**Verify remote is set correctly:**
```bash
git remote -v
```

You should see your repository URL with the token embedded.

**Option B: Using SSH Key (Alternative)**

If you prefer SSH (more secure, but requires key setup):

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "mlevitan96-crypto@users.noreply.github.com" -f ~/.ssh/github_key

# Display public key to add to GitHub
cat ~/.ssh/github_key.pub
```

Then:
1. Copy the public key output
2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the key and save

After adding to GitHub:
```bash
git remote set-url origin git@github.com:mlevitan96-crypto/stock-bot.git
```

---

## Step 4: Test Git Connection

Test that you can pull from the repository:

```bash
cd ~/stock-bot
git fetch origin
git status
```

**Expected:** Should show your current branch and any differences from remote.

---

## Step 5: Create Auto-Sync Script

Create a script that automatically commits and pushes changes so Cursor can see them:

```bash
cat > ~/stock-bot/auto_sync_to_git.sh << 'EOF'
#!/bin/bash
# Auto-sync droplet changes to git so Cursor can see them

cd ~/stock-bot

# Add all changes (logs, state, data files that should be tracked)
git add -A

# Check if there are changes to commit
if ! git diff --staged --quiet; then
    # Commit with timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "Auto-sync: Droplet changes at $TIMESTAMP" || true
    
    # Push to remote
    git push origin main || true
    echo "Synced to git at $TIMESTAMP"
else
    echo "No changes to sync"
fi
EOF

chmod +x ~/stock-bot/auto_sync_to_git.sh
```

---

## Step 6: Create Status Reporter Script

Create a script that commits current status/logs for Cursor to see:

```bash
cat > ~/stock-bot/report_status_to_git.sh << 'EOF'
#!/bin/bash
# Report current droplet status to git for Cursor visibility

cd ~/stock-bot

# Create status report
STATUS_FILE="status_report.json"
cat > "$STATUS_FILE" << STATUSEOF
{
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "uptime": "$(uptime -p)",
  "services": {
    "supervisor": "$(ps aux | grep -c '[d]eploy_supervisor' || echo '0')",
    "main": "$(ps aux | grep -c '[p]ython.*main.py' || echo '0')",
    "dashboard": "$(ps aux | grep -c '[p]ython.*dashboard.py' || echo '0')"
  },
  "git_status": "$(git status --porcelain | wc -l) files changed",
  "last_commit": "$(git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo 'unknown')",
  "disk_usage": "$(df -h . | tail -1 | awk '{print $5}')",
  "memory_usage": "$(free -h | grep Mem | awk '{print $3"/"$2}')"
}
STATUSEOF

# Add and commit status
git add "$STATUS_FILE"
git commit -m "Status report: $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

echo "Status reported to git"
EOF

chmod +x ~/stock-bot/report_status_to_git.sh
```

---

## Step 7: Set Up Git Hooks (Optional - Auto-commit on Changes)

Create a post-commit hook that automatically pushes:

```bash
cat > ~/stock-bot/.git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-push after commit
git push origin main &
EOF

chmod +x ~/stock-bot/.git/hooks/post-commit
```

---

## Step 8: Create Log Sync Script

Create a script to sync important logs to git (so Cursor can see them):

```bash
cat > ~/stock-bot/sync_logs_to_git.sh << 'EOF'
#!/bin/bash
# Sync recent logs to git for Cursor visibility

cd ~/stock-bot

# Create logs summary
LOG_SUMMARY="logs_summary.txt"
echo "=== Logs Summary - $(date) ===" > "$LOG_SUMMARY"
echo "" >> "$LOG_SUMMARY"

# Add recent trading log entries
if [ -f "logs/trading.log" ]; then
    echo "=== Trading Log (last 50 lines) ===" >> "$LOG_SUMMARY
    tail -50 logs/trading.log >> "$LOG_SUMMARY"
    echo "" >> "$LOG_SUMMARY"
fi

# Add recent learning log entries
if [ -f "logs/comprehensive_learning.log" ]; then
    echo "=== Learning Log (last 30 lines) ===" >> "$LOG_SUMMARY
    tail -30 logs/comprehensive_learning.log >> "$LOG_SUMMARY"
    echo "" >> "$LOG_SUMMARY"
fi

# Add recent errors
echo "=== Recent Errors ===" >> "$LOG_SUMMARY
grep -i error logs/*.log 2>/dev/null | tail -20 >> "$LOG_SUMMARY" || echo "No errors found" >> "$LOG_SUMMARY"

# Commit and push
git add "$LOG_SUMMARY"
git commit -m "Logs sync: $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

echo "Logs synced to git"
EOF

chmod +x ~/stock-bot/sync_logs_to_git.sh
```

---

## Step 9: Set Up Cron Job for Automatic Syncing (Optional)

Set up automatic syncing every hour so Cursor always sees current state:

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 * * * * cd ~/stock-bot && ./report_status_to_git.sh >> /tmp/git_sync.log 2>&1") | crontab -

# Verify it was added
crontab -l | grep report_status
```

---

## Step 10: Initial Sync - Push Current State

Do an initial sync to get everything into git:

```bash
cd ~/stock-bot
git add -A
git commit -m "Initial droplet state sync" || true
git push origin main
```

---

## Step 11: Verify Everything Works

Test the setup:

```bash
cd ~/stock-bot

# Test 1: Check git remote
echo "=== Git Remote ==="
git remote -v

# Test 2: Test push
echo ""
echo "=== Testing Push ==="
git fetch origin
git status

# Test 3: Run status report
echo ""
echo "=== Testing Status Report ==="
./report_status_to_git.sh

# Test 4: Check if changes are visible
echo ""
echo "=== Recent Commits ==="
git log --oneline -5
```

---

## Step 12: Manual Sync Commands (For Regular Use)

**Quick sync everything:**
```bash
cd ~/stock-bot && ./auto_sync_to_git.sh
```

**Sync just status:**
```bash
cd ~/stock-bot && ./report_status_to_git.sh
```

**Sync just logs:**
```bash
cd ~/stock-bot && ./sync_logs_to_git.sh
```

**Pull latest from git:**
```bash
cd ~/stock-bot && git pull origin main
```

---

## How Cursor Will See Everything

Once set up, Cursor can:

1. **See all changes** - Everything you do on the droplet gets synced to git
2. **View logs** - Log summaries are committed regularly
3. **Check status** - Status reports show current state
4. **Track history** - All changes are in git history
5. **No copy/paste needed** - Cursor reads directly from git

**Cursor can ask:**
- "What's the current status on the droplet?" → Reads from git
- "Show me recent logs" → Reads from git
- "What changes were made?" → Reads from git history
- "Deploy this change" → You commit on droplet, Cursor sees it

---

## Troubleshooting

### Git Push Fails with Authentication Error
```bash
# Re-set the remote URL with token
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/mlevitan96-crypto/stock-bot.git
```

### Merge Conflicts
```bash
# Reset to match remote exactly
git fetch origin
git reset --hard origin/main
```

### Permission Denied
```bash
# Make scripts executable
chmod +x ~/stock-bot/*.sh
```

### Cron Not Running
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog | tail -20
```

---

## Quick Reference

**Daily workflow:**
1. Work on droplet as normal
2. Run `./auto_sync_to_git.sh` periodically (or let cron do it)
3. Cursor sees everything through git - no copy/paste needed!

**After making changes:**
```bash
cd ~/stock-bot
git add -A
git commit -m "Your change description"
git push origin main
```

**Check what Cursor can see:**
```bash
cd ~/stock-bot
git log --oneline -10
git status
```

