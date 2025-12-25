#!/bin/bash
# Trigger Droplet Pull - Creates a trigger file that signals droplet to pull
# This is a workaround when SSH is not available

echo "Creating trigger file for droplet to pull..."
touch .trigger_droplet_pull
git add .trigger_droplet_pull
git commit -m "Trigger droplet pull for structural intelligence deployment - $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "Trigger file created and pushed to Git"
echo "Droplet will pull automatically via post-merge hook"

