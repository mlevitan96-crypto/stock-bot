#!/usr/bin/env bash
# Start promotion candidate 1 check in background, tail log, wait for key artifacts, then print summary.
# Run on droplet: cd /root/stock-bot && bash scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

# 1) Update repo and ensure orchestration scripts are executable
git pull origin main
chmod +x scripts/run_final_finish_on_droplet.sh scripts/run_push_with_plugins_on_droplet.sh scripts/run_finalize_push_on_droplet.sh scripts/run_promotion_candidate_1_check_on_droplet.sh 2>/dev/null || true

# 2) Start the promotion candidate check in background and capture logs
LOG="/tmp/promotion_candidate_1_check.log"
nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 &
PID=$!
echo "Started promotion candidate check (PID ${PID}), logging to ${LOG}"

# 3) Tail the log in the foreground while the job runs (user can Ctrl-C to detach)
echo "Tailing log (press Ctrl-C to stop following):"
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# 4) Wait for key artifacts to appear; poll every 30s
RUN_DIR="reports/backtests/promotion_candidate_1_check"
MM_BOARD="${RUN_DIR}/multi_model/out/board_verdict.md"
METRIC_CAND="${RUN_DIR}/metrics.json"
ES_SUM="${RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
PROM_CAND="${RUN_DIR}/PROMOTION_CANDIDATES.md"

echo "Waiting for artifacts: metrics, exec_sensitivity, board_verdict, promotion candidates..."
while true; do
  if [ ! -d "${RUN_DIR}" ]; then
    sleep 30
    continue
  fi

  MET_OK=false
  ES_OK=false
  BOARD_OK=false
  PROM_OK=false

  if [ -f "${METRIC_CAND}" ] || [ -f "${RUN_DIR}/baseline/metrics.json" ]; then
    MET_OK=true
  fi
  if [ -f "${ES_SUM}" ] || [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
    ES_OK=true
  fi
  if [ -f "${MM_BOARD}" ]; then
    BOARD_OK=true
  fi
  if [ -f "${PROM_CAND}" ]; then
    PROM_OK=true
  fi

  if ${MET_OK} && ( ${ES_OK} || ${BOARD_OK} ) && ${PROM_OK}; then
    echo "All key artifacts detected."
    break
  fi

  if ! kill -0 "${PID}" 2>/dev/null; then
    echo "Background job PID ${PID} is no longer running. Final artifact check will continue for 2 more minutes."
    sleep 120
    break
  fi

  sleep 30
done

# 5) Stop tailing the log
kill "${TAIL_PID}" 2>/dev/null || true

# 6) Print concise top sections of the artifacts
echo
echo "=== Promotion candidate metrics (first 20 lines) ==="
if [ -f "${METRIC_CAND}" ]; then
  head -n 20 "${METRIC_CAND}"
elif [ -f "${RUN_DIR}/baseline/metrics.json" ]; then
  head -n 20 "${RUN_DIR}/baseline/metrics.json"
else
  echo "metrics.json not found under ${RUN_DIR}"
fi

echo
echo "=== Exec sensitivity summary (if present) ==="
if [ -f "${ES_SUM}" ]; then
  jq '.' "${ES_SUM}" 2>/dev/null || cat "${ES_SUM}"
elif [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
  jq '.' "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" 2>/dev/null || cat "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json"
else
  echo "exec_sensitivity summary not found under ${RUN_DIR}"
fi

echo
echo "=== Multi-model board verdict (first 40 lines) ==="
if [ -f "${MM_BOARD}" ]; then
  head -n 40 "${MM_BOARD}"
else
  echo "board_verdict.md not found at ${MM_BOARD}"
fi

echo
echo "=== Promotion candidates (first 40 lines) ==="
if [ -f "${PROM_CAND}" ]; then
  head -n 40 "${PROM_CAND}"
else
  echo "PROMOTION_CANDIDATES.md not found at ${PROM_CAND}"
fi

echo
echo "Artifacts directory listing:"
ls -la "${RUN_DIR}" 2>/dev/null || echo "Run dir ${RUN_DIR} not present"

echo
echo "If any artifact is missing or the run stalled, inspect the log: tail -n 400 ${LOG}"
echo "Done."
