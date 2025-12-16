#!/bin/bash
# DigitalOcean Trading Bot Startup Script

set -e

echo "=== Trading Bot Startup ==="
echo "Timestamp: $(date)"

# Check required environment variables
if [ -z "$ALPACA_KEY" ] || [ -z "$ALPACA_SECRET" ] || [ -z "$UW_API_KEY" ]; then
    echo "ERROR: Required environment variables not set!"
    echo "Please set: ALPACA_KEY, ALPACA_SECRET, UW_API_KEY"
    exit 1
fi

# Create required directories
mkdir -p logs state feature_store

# Set Python to unbuffered mode (critical for crash logs)
export PYTHONUNBUFFERED=1

# Start the supervisor which manages all services
echo "Starting deploy_supervisor.py..."
python3 deploy_supervisor.py
