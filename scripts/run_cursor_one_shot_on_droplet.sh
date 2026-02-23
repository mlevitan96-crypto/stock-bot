#!/usr/bin/env bash
# Run full one-shot orchestrator on the droplet and wait for final summary
set -euo pipefail

cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

# Configure run (edit values here if desired)
export MODE="droplet"
export MIN_TRADES="${MIN_TRADES:-100}"
export MAX_ITER="${MAX_ITER:-3}"
export TIMEOUT_MIN="${TIMEOUT_MIN:-360}"   # allow up to 6 hours for heavy runs
export POLL_SEC="${POLL_SEC:-30}"

LOG="/tmp/cursor_full_automated_orchestrator_runall.log"
: > "${LOG}"

# Ensure the compact one-shot script exists and is executable
SCRIPT="scripts/cursor_one_shot_runall.sh"
if [ ! -x "${SCRIPT}" ]; then
  echo "Missing or non-executable ${SCRIPT}. Ensure scripts/cursor_one_shot_runall.sh is present and chmod +x." | tee -a "${LOG}"
  exit 1
fi

# Start the orchestrator in background
nohup bash "${SCRIPT}" >> "${LOG}" 2>&1 &
ORCH_PID=$!
echo "Started orchestrator (PID ${ORCH_PID}); logging to ${LOG}"

# Tail the log for live feedback (background)
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# Wait for final summary file (timeout)
END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_SUMMARY=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  RUN_DIR=$(ls -td reports/backtests/promotion_candidate_* reports/backtests/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${RUN_DIR}" ] && [ -f "${RUN_DIR}/cursor_final_summary.txt" ]; then
    FOUND_SUMMARY="${RUN_DIR}/cursor_final_summary.txt"
    break
  fi
  sleep "${POLL_SEC}"
done

# Stop tailing
kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_SUMMARY}" ]; then
  echo "ERROR: No final summary found within ${TIMEOUT_MIN} minutes. Check ${LOG} for errors." | tee -a "${LOG}"
  exit 2
fi

# Print the three machine-readable lines and show the human report head
grep -E '^RUN_DIR:|^DECISION:|^PR_BRANCH:' "${FOUND_SUMMARY}" || true
echo
echo "---- cursor_report.md (first 200 lines) ----"
REPORT_DIR=$(dirname "${FOUND_SUMMARY}")
if [ -f "${REPORT_DIR}/cursor_report.md" ]; then
  sed -n '1,200p' "${REPORT_DIR}/cursor_report.md"
else
  echo "cursor_report.md not found in ${REPORT_DIR}"
fi
echo
echo "Artifacts in run dir:"
ls -la "${REPORT_DIR}" | sed -n '1,200p'
echo
echo "Excerpts directory (if present):"
ls -ld /tmp/cursor_run_excerpts_* 2>/dev/null || true
