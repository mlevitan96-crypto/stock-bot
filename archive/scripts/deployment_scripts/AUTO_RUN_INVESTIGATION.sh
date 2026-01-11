#!/bin/bash
# Auto-run investigation on every git pull
# This ensures investigation always runs when code is updated

cd ~/stock-bot

# Run comprehensive diagnosis (works even if investigate_no_trades.py has issues)
if [ -f "comprehensive_no_trades_diagnosis.py" ]; then
    python3 comprehensive_no_trades_diagnosis.py 2>&1 | tee /tmp/investigation_output.txt
else
    python3 investigate_no_trades.py 2>&1 | tee /tmp/investigation_output.txt
fi

# Always commit and push results (even if there were errors)
if [ -f "investigate_no_trades.json" ]; then
    touch .last_investigation_run
    git add investigate_no_trades.json .last_investigation_run 2>/dev/null
    git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
fi

