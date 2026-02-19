#!/bin/bash
# Droplet Truth Run + Research Dataset Build. Run on droplet: /root/stock-bot
set -e
cd /root/stock-bot
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
python3 scripts/run_droplet_truth_run.py
