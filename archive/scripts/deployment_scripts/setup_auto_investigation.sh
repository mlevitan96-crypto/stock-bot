#!/bin/bash
# One-time setup: Add cron job to auto-run investigations when triggered
# Run this ONCE on the droplet

cd ~/stock-bot

echo "Setting up automated investigation system..."

# Add cron job to check for triggers every 2 minutes
(crontab -l 2>/dev/null | grep -v "auto_investigation_trigger.sh"; 
 echo "*/2 * * * * cd ~/stock-bot && bash auto_investigation_trigger.sh >> /tmp/auto_investigation.log 2>&1") | crontab -

echo "✅ Cron job installed (checks every 2 minutes for investigation triggers)"
echo ""
echo "Workflow:"
echo "  1. Cursor runs: python trigger_investigation.py"
echo "  2. Droplet detects trigger (within 2 minutes)"
echo "  3. Droplet runs investigation and commits results"
echo "  4. Cursor reads: python read_investigation_results.py"
echo ""
echo "Test it: python trigger_investigation.py (from Cursor)"

