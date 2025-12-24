#!/bin/bash
# Resolve merge conflict and trigger automatic deployment
# This script fixes the conflict, pulls, and the post-merge hook will run automatically

cd ~/stock-bot

echo "Resolving merge conflict and deploying..."
echo ""

# Remove conflicting file
rm -f setup_droplet_git.sh 2>/dev/null
echo "Removed conflicting file"

# Now pull - this will trigger post-merge hook automatically
echo "Pulling latest code (will trigger post-merge hook)..."
git pull origin main

# The post-merge hook will automatically run run_investigation_on_pull.sh
echo ""
echo "Deployment triggered via post-merge hook"

