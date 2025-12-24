#!/bin/bash
# Quick fix for merge conflict and deploy
# Run this on the droplet to fix the conflict and deploy

cd ~/stock-bot

echo "Fixing merge conflict and deploying..."
echo ""

# Remove conflicting file
rm -f setup_droplet_git.sh 2>/dev/null
echo "Removed conflicting file: setup_droplet_git.sh"
echo ""

# Pull latest (including fixed deployment script)
git pull origin main
echo ""

# Run deployment
bash FINAL_DEPLOYMENT_SCRIPT.sh
