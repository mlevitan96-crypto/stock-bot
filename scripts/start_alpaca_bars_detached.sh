#!/bin/bash
# Start enable_alpaca_bars_resume.sh detached (nohup). Record PID. No long-lived SSH.
set -e
REPO="${REPO:-/root/stock-bot}"
cd "$REPO"
mkdir -p "$REPO/reports/bars"
rm -f "$REPO/reports/bars/final_verdict.txt"
nohup bash scripts/enable_alpaca_bars_resume.sh \
  > reports/bars/nohup_run.log 2>&1 &
echo $! > reports/bars/nohup_pid.txt
echo "PID=$(cat reports/bars/nohup_pid.txt)"
echo "Verdict will be written to: $REPO/reports/bars/final_verdict.txt"
echo "To check later: cat $REPO/reports/bars/final_verdict.txt"
