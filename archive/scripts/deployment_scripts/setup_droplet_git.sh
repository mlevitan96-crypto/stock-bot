#!/bin/bash
# Complete Droplet Git Setup Script
# Run this on your droplet to set up git client for Cursor visibility

set -e

echo "=========================================="
echo "Droplet Git Client Setup"
echo "=========================================="
echo ""

# Step 1: Navigate to project
cd ~/stock-bot
echo "✅ Step 1: In project directory"

# Step 2: Configure git
echo ""
echo "Step 2: Configuring git..."
git config user.name "mlevitan96-crypto"
git config user.email "mlevitan96-crypto@users.noreply.github.com"
git config pull.rebase false
git config core.editor true
git config merge.commit no-edit
echo "✅ Git configured"

# Step 3: Set up GitHub authentication
echo ""
echo "Step 3: Setting up GitHub authentication..."
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/mlevitan96-crypto/stock-bot.git
echo "✅ GitHub authentication configured"

# Step 4: Test connection
echo ""
echo "Step 4: Testing git connection..."
git fetch origin
echo "✅ Git connection working"

# Step 5: Create auto-sync script
echo ""
echo "Step 5: Creating auto-sync script..."
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
echo "✅ Auto-sync script created"

# Step 6: Create status reporter
echo ""
echo "Step 6: Creating status reporter..."
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
echo "✅ Status reporter created"

# Step 7: Create log sync script
echo ""
echo "Step 7: Creating log sync script..."
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
    echo "=== Trading Log (last 50 lines) ===" >> "$LOG_SUMMARY"
    tail -50 logs/trading.log >> "$LOG_SUMMARY"
    echo "" >> "$LOG_SUMMARY"
fi

# Add recent learning log entries
if [ -f "logs/comprehensive_learning.log" ]; then
    echo "=== Learning Log (last 30 lines) ===" >> "$LOG_SUMMARY"
    tail -30 logs/comprehensive_learning.log >> "$LOG_SUMMARY"
    echo "" >> "$LOG_SUMMARY"
fi

# Add recent errors
echo "=== Recent Errors ===" >> "$LOG_SUMMARY"
grep -i error logs/*.log 2>/dev/null | tail -20 >> "$LOG_SUMMARY" || echo "No errors found" >> "$LOG_SUMMARY"

# Commit and push
git add "$LOG_SUMMARY"
git commit -m "Logs sync: $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

echo "Logs synced to git"
EOF
chmod +x ~/stock-bot/sync_logs_to_git.sh
echo "✅ Log sync script created"

# Step 8: Set up post-commit hook
echo ""
echo "Step 8: Setting up git hooks..."
mkdir -p ~/stock-bot/.git/hooks
cat > ~/stock-bot/.git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-push after commit
git push origin main &
EOF
chmod +x ~/stock-bot/.git/hooks/post-commit
echo "✅ Git hooks configured"

# Step 9: Set up cron job (optional)
echo ""
echo "Step 9: Setting up automatic hourly sync..."
(crontab -l 2>/dev/null | grep -v "report_status_to_git.sh"; echo "0 * * * * cd ~/stock-bot && ./report_status_to_git.sh >> /tmp/git_sync.log 2>&1") | crontab -
echo "✅ Cron job configured (runs every hour)"

# Step 10: Initial sync
echo ""
echo "Step 10: Performing initial sync..."
git add -A
git commit -m "Initial droplet state sync - $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"
git push origin main || echo "Push completed or no changes"
echo "✅ Initial sync complete"

# Final verification
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Verification:"
echo "  Git remote:"
git remote -v
echo ""
echo "  Recent commits:"
git log --oneline -5
echo ""
echo "=========================================="
echo "Quick Commands:"
echo "  Sync everything: ./auto_sync_to_git.sh"
echo "  Report status:   ./report_status_to_git.sh"
echo "  Sync logs:       ./sync_logs_to_git.sh"
echo "  Pull latest:     git pull origin main"
echo "=========================================="

