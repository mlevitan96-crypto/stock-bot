#!/bin/bash
# Zero-Downtime Deployment Script
# Single command deployment: ./deploy.sh

set -e

cd /root/stock-bot

# Activate venv
source venv/bin/activate

# Run zero-downtime deployment
python3 zero_downtime_deploy.py

echo ""
echo "Deployment complete! Check dashboard at http://your-server:5000/"
