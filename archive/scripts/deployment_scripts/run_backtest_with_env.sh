#!/bin/bash
# Run backtest with proper environment loading
cd ~/stock-bot

# Load .env file if it exists (same as deploy_supervisor does)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run backtest
python3 historical_replay_engine.py --days 7 --output reports/7_day_quick_audit.json
