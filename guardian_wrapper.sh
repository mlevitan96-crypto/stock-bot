#!/bin/bash
# Guardian Wrapper - Self-Healing Layer for Cron Jobs
# Authoritative Source: MEMORY_BANK.md
#
# This script wraps Python scripts in a self-healing layer that:
# 1. Runs the targeted Python script
# 2. Catches exit codes 1 (Error/Degraded) or 2 (Unhealthy)
# 3. If unhealthy, attempts automatic recovery
#
# Usage:
#   bash guardian_wrapper.sh <script_name.py> [script_args...]
#
# Recovery Actions:
#   - UW_SOCKET_FAIL: Force kill 'uw_flow_daemon.py' and restart
#   - ALPACA_SIP_DELAY: Log critical alert and re-initialize Alpaca Client
#   - STALE_METADATA_LOCK: Delete any '.lock' files in 'state/' directory

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
STATE_DIR="${SCRIPT_DIR}/state"
VENV_PYTHON="${SCRIPT_DIR}/venv/bin/python"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Logging function
log() {
    local level="$1"
    shift
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${timestamp}] [${level}] $*" | tee -a "${LOG_DIR}/guardian.log"
}

# Parse arguments
if [ $# -lt 1 ]; then
    log "ERROR" "Usage: $0 <script_name.py> [script_args...]"
    exit 1
fi

SCRIPT_NAME="$1"
shift
SCRIPT_ARGS=("$@")

# Resolve script path
SCRIPT_PATH="${SCRIPT_DIR}/${SCRIPT_NAME}"
if [ ! -f "${SCRIPT_PATH}" ]; then
    log "ERROR" "Script not found: ${SCRIPT_PATH}"
    exit 1
fi

log "INFO" "Starting guardian wrapper for: ${SCRIPT_NAME}"
log "INFO" "Script path: ${SCRIPT_PATH}"
log "INFO" "Working directory: ${SCRIPT_DIR}"

# Determine Python interpreter
if [ -f "${VENV_PYTHON}" ]; then
    PYTHON_CMD="${VENV_PYTHON}"
    log "INFO" "Using venv Python: ${PYTHON_CMD}"
else
    PYTHON_CMD="python3"
    log "INFO" "Using system Python: ${PYTHON_CMD}"
fi

# Change to script directory
cd "${SCRIPT_DIR}"

# Function: Clear stale lock files
clear_stale_locks() {
    log "INFO" "Clearing stale lock files in ${STATE_DIR}/"
    local lock_count=0
    
    if [ -d "${STATE_DIR}" ]; then
        while IFS= read -r -d '' lock_file; do
            log "WARN" "Removing stale lock file: ${lock_file}"
            rm -f "${lock_file}"
            ((lock_count++)) || true
        done < <(find "${STATE_DIR}" -name "*.lock" -type f -print0 2>/dev/null || true)
        
        if [ "${lock_count}" -eq 0 ]; then
            log "INFO" "No lock files found to clear"
        else
            log "INFO" "Cleared ${lock_count} lock file(s)"
        fi
    else
        log "WARN" "State directory not found: ${STATE_DIR}"
    fi
}

# Function: Restart UW Flow Daemon
restart_uw_daemon() {
    log "WARN" "Attempting to restart UW Flow Daemon..."
    
    # Check if using process-compose
    if command -v process-compose >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/process-compose.yaml" ]; then
        log "INFO" "Using process-compose - triggering restart..."
        process-compose restart uw-daemon 2>&1 | tee -a "${LOG_DIR}/guardian.log" || {
            log "ERROR" "Failed to restart via process-compose, trying direct kill"
            pkill -f "uw_flow_daemon.py" || true
            sleep 2
        }
    else
        # Direct kill and let supervisor restart
        log "INFO" "Killing UW daemon process (supervisor will restart)..."
        pkill -f "uw_flow_daemon.py" || {
            log "WARN" "No uw_flow_daemon.py process found to kill"
        }
        sleep 2
    fi
    
    # Verify restart
    sleep 3
    if pgrep -f "uw_flow_daemon.py" >/dev/null 2>&1; then
        log "INFO" "UW daemon restarted successfully"
        return 0
    else
        log "ERROR" "UW daemon restart verification failed - process not running"
        return 1
    fi
}

# Function: Re-initialize Alpaca Client (log critical alert)
reinitialize_alpaca() {
    log "CRITICAL" "ALPACA_SIP_DELAY detected - attempting Alpaca Client re-initialization"
    
    # Log critical alert
    local alert_file="${LOG_DIR}/alpaca_sip_alert_$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "CRITICAL ALERT: Alpaca SIP Delay Detected"
        echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        echo "Action: Attempting Alpaca Client re-initialization"
        echo ""
        echo "Manual intervention may be required if this persists."
    } > "${alert_file}"
    
    log "INFO" "Critical alert logged to: ${alert_file}"
    
    # Attempt to restart trading bot (which will re-initialize Alpaca client)
    if command -v process-compose >/dev/null 2>&1 && [ -f "${SCRIPT_DIR}/process-compose.yaml" ]; then
        log "INFO" "Restarting trading-bot via process-compose..."
        process-compose restart trading-bot 2>&1 | tee -a "${LOG_DIR}/guardian.log" || true
    else
        log "INFO" "Killing main.py process (supervisor will restart)..."
        pkill -f "python.*main.py" || true
        sleep 2
    fi
    
    return 0
}

# Function: Analyze health check output for specific failures
analyze_health_check_output() {
    local output_file="$1"
    local has_uw_fail=false
    local has_alpaca_delay=false
    local has_lock_issue=false
    
    if [ -f "${output_file}" ]; then
        # Check for UW socket/connection failures
        if grep -qiE "(connection_error|timeout|UW.*fail|socket.*fail)" "${output_file}" 2>/dev/null; then
            has_uw_fail=true
            log "INFO" "Detected UW socket/connection failure in output"
        fi
        
        # Check for Alpaca SIP delay
        if grep -qiE "(SIP.*delay|sip_feed.*error|sip_feed.*no_data)" "${output_file}" 2>/dev/null; then
            has_alpaca_delay=true
            log "INFO" "Detected Alpaca SIP delay in output"
        fi
        
        # Check for lock/metadata issues (implicit - we'll always check)
        has_lock_issue=true
    fi
    
    echo "${has_uw_fail}:${has_alpaca_delay}:${has_lock_issue}"
}

# Function: Perform recovery actions based on script and exit code
perform_recovery() {
    local exit_code="$1"
    local script_output_file="${LOG_DIR}/guardian_${SCRIPT_NAME%.py}_output.log"
    
    log "WARN" "Recovery triggered for exit code: ${exit_code}"
    
    # Always clear stale locks first (safe operation)
    clear_stale_locks
    
    # If this is pre_market_health_check.py, analyze output for specific issues
    if [ "${SCRIPT_NAME}" = "pre_market_health_check.py" ]; then
        local analysis
        analysis=$(analyze_health_check_output "${script_output_file}" || echo "false:false:true")
        IFS=':' read -r has_uw_fail has_alpaca_delay has_lock_issue <<< "${analysis}"
        
        if [ "${has_uw_fail}" = "true" ]; then
            log "WARN" "UW_SOCKET_FAIL detected - restarting UW daemon"
            restart_uw_daemon
        fi
        
        if [ "${has_alpaca_delay}" = "true" ]; then
            log "WARN" "ALPACA_SIP_DELAY detected - re-initializing Alpaca Client"
            reinitialize_alpaca
        fi
    else
        # For other scripts, apply general recovery
        log "INFO" "Applying general recovery actions..."
        restart_uw_daemon || true
    fi
    
    # Wait a moment for services to stabilize
    sleep 5
    
    # Re-verify connectivity by re-running health check (if it was a health check)
    if [ "${SCRIPT_NAME}" = "pre_market_health_check.py" ]; then
        log "INFO" "Re-verifying connectivity..."
        local retry_output="${LOG_DIR}/guardian_retry_${SCRIPT_NAME%.py}.log"
        if "${PYTHON_CMD}" "${SCRIPT_PATH}" "${SCRIPT_ARGS[@]}" > "${retry_output}" 2>&1; then
            log "INFO" "Re-verification successful - system recovered"
        else
            local retry_code=$?
            log "ERROR" "Re-verification failed with exit code: ${retry_code}"
            log "ERROR" "System may require manual intervention"
        fi
    fi
}

# Run the script and capture output
log "INFO" "Executing: ${PYTHON_CMD} ${SCRIPT_PATH} ${SCRIPT_ARGS[*]}"
SCRIPT_OUTPUT="${LOG_DIR}/guardian_${SCRIPT_NAME%.py}_output.log"

if "${PYTHON_CMD}" "${SCRIPT_PATH}" "${SCRIPT_ARGS[@]}" > "${SCRIPT_OUTPUT}" 2>&1; then
    EXIT_CODE=0
    log "INFO" "Script completed successfully (exit code: 0)"
else
    EXIT_CODE=$?
    log "WARN" "Script exited with code: ${EXIT_CODE}"
    
    # Log script output for debugging
    if [ -f "${SCRIPT_OUTPUT}" ]; then
        log "INFO" "Script output (last 50 lines):"
        tail -50 "${SCRIPT_OUTPUT}" | while IFS= read -r line; do
            log "OUTPUT" "${line}"
        done
    fi
    
    # Perform recovery for exit codes 1 (degraded) or 2 (unhealthy)
    if [ "${EXIT_CODE}" -eq 1 ] || [ "${EXIT_CODE}" -eq 2 ]; then
        log "WARN" "Exit code ${EXIT_CODE} indicates degraded/unhealthy state - initiating recovery"
        perform_recovery "${EXIT_CODE}"
        
        # After recovery, exit with the original code so cron knows the initial check failed
        log "INFO" "Recovery actions completed. Exiting with original code: ${EXIT_CODE}"
        exit "${EXIT_CODE}"
    else
        # Unexpected exit code - log and exit as-is
        log "ERROR" "Unexpected exit code: ${EXIT_CODE}"
        exit "${EXIT_CODE}"
    fi
fi

# Success
exit 0
