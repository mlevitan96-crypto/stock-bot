#!/bin/bash
cd ~/stock-bot
python3 investigate_no_trades.py
git add investigate_no_trades.json 2>/dev/null
git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
git push origin main 2>/dev/null || true
