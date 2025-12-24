#!/bin/bash
# Report current droplet status to git for Cursor visibility
# ALSO checks for investigation triggers and runs them automatically

cd ~/stock-bot

# Pull latest first
git pull origin main --no-rebase || true

# Create status report
STATUS_FILE="status_report.json"
cat > "$STATUS_FILE" << STATUSEOF
{
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "uptime": "$(uptime -p)",
  "services": {
    "supervisor": "$(ps aux | grep -c '[d]eploy_supervisor' || echo '0')",
    "main": "$(ps aux | grep -c '[p]ython.*main.py' || echo '0')",
    "dashboard": "$(ps aux | grep -c '[p]ython.*dashboard.py' || echo '0')"
  },
  "git_status": "$(git status --porcelain | wc -l) files changed",
  "last_commit": "$(git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo 'unknown')",
  "disk_usage": "$(df -h . | tail -1 | awk '{print $5}')",
  "memory_usage": "$(free -h | grep Mem | awk '{print $3"/"$2}')"
}
STATUSEOF

# Add and commit status
git add "$STATUS_FILE"
git commit -m "Status report: $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin main || true

# Run UW endpoint test if script exists (first time only, or if .trigger_uw_test exists)
if [ -f "test_uw_endpoints_comprehensive.py" ] && ([ ! -f ".uw_test_run" ] || [ -f ".trigger_uw_test" ]); then
    echo "Running UW endpoint test..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python3 test_uw_endpoints_comprehensive.py 2>&1
    
    if [ -f "uw_endpoint_test_results.json" ]; then
        git add uw_endpoint_test_results.json 2>/dev/null
        git commit -m "UW endpoint test results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
        git push origin main 2>/dev/null || true
        touch .uw_test_run
        rm -f .trigger_uw_test 2>/dev/null
    fi
fi

# Check for investigation triggers (multiple trigger methods)
TRIGGER_DETECTED=false

# Method 1: .investigation_trigger file
if [ -f ".investigation_trigger" ]; then
    TRIGGER_TIME=$(stat -c %Y .investigation_trigger 2>/dev/null || echo 0)
    LAST_RUN_TIME=$(stat -c %Y .last_investigation_run 2>/dev/null || echo 0)
    if [ "$TRIGGER_TIME" -gt "$LAST_RUN_TIME" ]; then
        TRIGGER_DETECTED=true
    fi
fi

# Method 2: RUN_INVESTIGATION_NOW.flag file
if [ -f "RUN_INVESTIGATION_NOW.flag" ]; then
    TRIGGER_DETECTED=true
fi

# Method 3: run_investigation_on_pull.sh exists and is newer than last run
if [ -f "run_investigation_on_pull.sh" ]; then
    SCRIPT_TIME=$(stat -c %Y run_investigation_on_pull.sh 2>/dev/null || echo 0)
    LAST_RUN_TIME=$(stat -c %Y .last_investigation_run 2>/dev/null || echo 0)
    if [ "$SCRIPT_TIME" -gt "$LAST_RUN_TIME" ]; then
        TRIGGER_DETECTED=true
    fi
fi

# Run investigation if triggered
if [ "$TRIGGER_DETECTED" = true ]; then
    echo "Investigation trigger detected, running investigation immediately..."
    python3 investigate_no_trades.py 2>/dev/null || true
    touch .last_investigation_run
    git add investigate_no_trades.json .last_investigation_run 2>/dev/null || true
    git commit -m "Auto-investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
    echo "Investigation complete and results pushed to git"
    # Clean up trigger files
    rm -f RUN_INVESTIGATION_NOW.flag 2>/dev/null || true
fi

echo "Status reported to git"

