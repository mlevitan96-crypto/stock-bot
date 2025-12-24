#!/bin/bash
# Force immediate investigation - run this on droplet
cd ~/stock-bot
git pull origin main --no-rebase
chmod +x run_investigation_on_pull.sh
./run_investigation_on_pull.sh

