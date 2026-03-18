#!/bin/bash
set -e
echo "## /root listing"
ls -la /root 2>/dev/null | head -40 || true
echo "## services"
systemctl list-units --type=service --all 2>/dev/null | grep -iE 'kraken|trading|stock|crypto' || true
echo "## dirs"
for d in /root/trading-bot-current /root/trading-bot /root/kraken-bot /root/stock-bot-current /root/stock-bot; do
  if [ -d "$d" ]; then echo "EXISTS: $d"; ls "$d"/logs/*.jsonl 2>/dev/null | head -25 || true; fi
done
echo "## unified_events anywhere under /root (max 15)"
find /root -maxdepth 4 -name 'unified_events.jsonl' 2>/dev/null | head -15 || true
echo "## exit_attribution"
find /root -maxdepth 4 -name 'exit_attribution.jsonl' 2>/dev/null | head -15 || true
