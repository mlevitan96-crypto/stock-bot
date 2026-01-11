#!/bin/bash
# Auto-trigger investigation when this file is updated in git
# This runs on the droplet via cron to check for new triggers

cd ~/stock-bot

# Check if trigger file exists and is newer than last run
TRIGGER_FILE=".investigation_trigger"
LAST_RUN_FILE=".last_investigation_run"

if [ ! -f "$TRIGGER_FILE" ]; then
    exit 0  # No trigger, exit silently
fi

# Check if we've already run for this trigger
if [ -f "$LAST_RUN_FILE" ]; then
    TRIGGER_TIME=$(stat -c %Y "$TRIGGER_FILE" 2>/dev/null || echo 0)
    LAST_RUN_TIME=$(stat -c %Y "$LAST_RUN_FILE" 2>/dev/null || echo 0)
    if [ "$TRIGGER_TIME" -le "$LAST_RUN_TIME" ]; then
        exit 0  # Already ran for this trigger
    fi
fi

# Pull latest code
git pull origin main --no-rebase > /dev/null 2>&1

# Run investigation
echo "Running automated investigation..."
python3 investigate_no_trades.py

# Mark as run
touch "$LAST_RUN_FILE"

# Commit and push results
git add investigate_no_trades.json "$LAST_RUN_FILE" 2>/dev/null
git commit -m "Auto-investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null
git push origin main > /dev/null 2>&1

echo "Investigation complete and results pushed to git"

