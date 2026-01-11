#!/bin/bash
cd /root/stock-bot
git pull origin main
systemctl restart trading-bot.service
sleep 5
python3 check_current_status.py
