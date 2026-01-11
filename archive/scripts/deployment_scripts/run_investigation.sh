#!/bin/bash
# Run investigation and sync results to git for Cursor

cd ~/stock-bot

echo "Running comprehensive investigation..."
python3 investigate_no_trades.py

echo ""
echo "Syncing results to git..."
git add investigate_no_trades.json
git commit -m "Investigation: No trades today - $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

echo ""
echo "✅ Investigation complete and synced to git"
echo "   Cursor can now see the results in investigate_no_trades.json"

