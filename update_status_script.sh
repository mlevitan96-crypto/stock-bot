#!/bin/bash
# Update the existing report_status_to_git.sh to also check for investigation triggers
# This runs ONCE on the droplet to update the script

cd ~/stock-bot
git pull origin main

# The updated script is already in git, just need to make sure it's the active one
chmod +x report_status_to_git.sh

echo "Status script updated - it will now auto-run investigations when triggered"
echo "Next hourly run will check for triggers automatically"

