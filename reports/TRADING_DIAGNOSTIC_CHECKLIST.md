# Stock-Bot Trading Flow Diagnostic Checklist
**Generated:** 2026-01-26T16:17:41.526803+00:00

## SIGNAL CAPTURE
- [FAIL] Uw Daemon Running
- [FAIL] Cache File Exists
- [FAIL] Cache Has Data
- [FAIL] Cache Recent
- [PASS] Enrichment Working

### Issues Found:
- [ISSUE] UW Flow Daemon is not running - signals won't be captured
- [ISSUE] Cache file missing or invalid

## SIGNAL PROCESSING
- [PASS] Composite Scoring Available
- [FAIL] Composite Scoring Working
- [FAIL] Signals Logged
- [FAIL] Recent Signals
- [FAIL] Gate Logging Working

### Issues Found:
- [ISSUE] Composite scoring test failed: No composite scoring function found
- [ISSUE] Signal history log missing or empty

## EXIT CRITERIA
- [PASS] Evaluate Exits Function
- [FAIL] Exit Logging Working
- [FAIL] Recent Exit Logs
- [FAIL] Exit Signals Captured
- [PASS] Structural Exit Available

### Issues Found:
- [ISSUE] Exit event log missing or empty

## LOGGING SYSTEMS
- [PASS] Log Functions Available
- [PASS] Log Directories Exist
- [PASS] Attribution Logging
- [FAIL] Order Logging
- [FAIL] Run Cycle Logging

## TRADE EXECUTION
- [PASS] Executor Available
- [PASS] Decide And Execute Function
- [FAIL] Order Submission Working
- [FAIL] Position Tracking

## Overall Status

- **Total Checks:** 24
- **Passed:** 9
- **Failed:** 15
- **Success Rate:** 37.5%

## Proposed Fixes

### Issue 1: UW Flow Daemon is not running - signals won't be captured

**Proposed Fix:**
1. Check if `uw_flow_daemon.py` is running: `ps aux | grep uw_flow_daemon` (Linux) or check Task Manager (Windows)
2. Restart the trading bot service: `systemctl restart trading-bot.service` (Linux) or restart manually (Windows)
3. Verify daemon starts in supervisor logs
4. Check lock file: `state/uw_flow_daemon.lock`

### Issue 2: Cache file missing or invalid

**Proposed Fix:**
1. Check UW API credentials in `.env` file
2. Verify UW daemon is running and polling API
3. Check `data/uw_flow_cache.json` for data
4. Review daemon logs: `tail -f logs/uw_flow_daemon.jsonl`

### Issue 3: Composite scoring test failed: No composite scoring function found

**Proposed Fix:**
- Review error logs and code implementation
- Check related components for issues

### Issue 4: Signal history log missing or empty

**Proposed Fix:**
1. Verify log directories exist: `logs/`, `data/`, `state/`
2. Check file permissions on log directories
3. Review recent log entries for errors
4. Ensure logging functions are being called in code

### Issue 5: Exit event log missing or empty

**Proposed Fix:**
1. Verify log directories exist: `logs/`, `data/`, `state/`
2. Check file permissions on log directories
3. Review recent log entries for errors
4. Ensure logging functions are being called in code

