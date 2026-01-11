#!/bin/bash
# Deploy hardened code to droplet

cd /root/stock-bot
git pull origin main
systemctl restart trading-bot.service
echo "Hardened code deployed and bot restarted"
