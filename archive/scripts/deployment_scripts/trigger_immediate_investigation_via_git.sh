#!/bin/bash
# This script is pushed to git and tells the droplet to run investigation immediately
# The droplet should have a git hook or cron that runs run_investigation_on_pull.sh on pull

cd ~/stock-bot

# Pull latest (this will trigger the investigation if hooks are set up)
git pull origin main --no-rebase

# If hooks aren't set up, run investigation directly
if [ -f "run_investigation_on_pull.sh" ]; then
    chmod +x run_investigation_on_pull.sh
    ./run_investigation_on_pull.sh
fi

