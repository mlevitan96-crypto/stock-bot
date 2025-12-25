#!/bin/bash
# Fix git merge conflict on droplet
# This script resolves conflicts by resetting to origin/main

cd ~/stock-bot

echo "=========================================="
echo "FIXING GIT MERGE CONFLICT"
echo "=========================================="
echo ""

# Step 1: Check current status
echo "Step 1: Checking git status..."
git status
echo ""

# Step 2: Fetch latest from origin
echo "Step 2: Fetching latest from origin..."
git fetch origin main
echo ""

# Step 3: Reset to origin/main (discards local changes)
echo "Step 3: Resetting to origin/main..."
echo "WARNING: This will discard any local changes on the droplet"
git reset --hard origin/main
echo ""

# Step 4: Verify we're clean
echo "Step 4: Verifying git status..."
git status
echo ""

# Step 5: Now pull should work
echo "Step 5: Pulling latest code..."
git pull origin main
echo ""

echo "=========================================="
echo "MERGE CONFLICT RESOLVED"
echo "=========================================="
echo ""

# Step 6: Run deployment if script exists
if [ -f "FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh" ]; then
    echo "Step 6: Running deployment verification..."
    chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
    bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh
fi

