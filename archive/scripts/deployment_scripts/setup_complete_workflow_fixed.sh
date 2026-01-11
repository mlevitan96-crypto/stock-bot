#!/bin/bash
# Complete one-time setup: Replace status script with version that auto-runs investigations
# Handles merge conflicts automatically

cd ~/stock-bot

echo "Setting up complete automated workflow..."
echo ""

# Handle any local changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Stashing local changes..."
    git stash
fi

# Pull latest
echo "Pulling latest code..."
git pull origin main --no-rebase || {
    echo "Merge conflict detected, resetting to remote..."
    git fetch origin
    git reset --hard origin/main
}

# Backup old script
if [ -f "report_status_to_git.sh" ]; then
    cp report_status_to_git.sh report_status_to_git.sh.backup
    echo "Backed up old script to report_status_to_git.sh.backup"
fi

# Copy new complete version
cp report_status_to_git_complete.sh report_status_to_git.sh
chmod +x report_status_to_git.sh

echo "✅ Status script updated - will now auto-run investigations when triggered"
echo ""
echo "Workflow is now:"
echo "  1. Cursor: python trigger_investigation.py"
echo "  2. Droplet: Auto-detects trigger (within 1 hour max)"
echo "  3. Droplet: Runs investigation and commits results"
echo "  4. Cursor: python read_investigation_results.py"
echo ""
echo "✅ Setup complete! Everything is now automated."

