#!/bin/bash
# Phase 3 only: deploy + restart paper on droplet. Run from /root/stock-bot.
set -e
cd /root/stock-bot
git pull --rebase origin main
grep -q group_sums score_snapshot_writer.py || { echo "Attribution commit not present"; exit 1; }
tmux kill-session -t stock_bot_paper_run 2>/dev/null || true
sleep 2
tmux new-session -d -s stock_bot_paper_run 'cd /root/stock-bot && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'
echo "Paper restarted. Wait for new snapshots/blocked_trades with attribution, then run: python3 scripts/run_multi_model_signal_edge_cycle_on_droplet.py --phase 4"
