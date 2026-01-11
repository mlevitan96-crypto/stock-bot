#!/bin/bash
# Deploy hardened code to droplet

set -e

echo "Deploying hardened code to droplet..."
cd /root/stock-bot

echo "Pulling latest code..."
git pull origin main

echo "Restarting trading bot..."
systemctl restart trading-bot.service

sleep 3

echo "Checking bot status..."
systemctl status trading-bot.service --no-pager | head -10

echo ""
echo "Deployment complete!"
echo "Run: python3 check_current_status.py"
echo "to verify bot is running and check for trades"
