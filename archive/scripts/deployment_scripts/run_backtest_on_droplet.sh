#!/bin/bash
# Run backtest on droplet
cd ~/stock-bot
git pull origin main
python3 historical_replay_engine.py --days 30 --output reports/30_day_physics_audit.json
