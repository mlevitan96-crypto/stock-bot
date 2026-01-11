#!/bin/bash
# Deploy freshness fix to droplet and restart bot

cd /root/stock-bot
git pull origin main
systemctl restart trading-bot.service
echo "Freshness fix deployed and bot restarted"
