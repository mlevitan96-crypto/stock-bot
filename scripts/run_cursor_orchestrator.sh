#!/usr/bin/env bash
# Run the Cursor orchestrator and review bundle
# Edit MODE and WORKERS below, then paste and run on controller or droplet.
set -euo pipefail

# -------------------------
# Configure here
# -------------------------
MODE="${MODE:-local}"                       # local | droplet | parallel
WORKERS="${WORKERS:-}"                      # space-separated hosts for parallel mode
GH_TOKEN="${GH_TOKEN:-}"                    # optional: set to enable GitHub issue/PR creation
PARALLEL_JOBS="${PARALLEL_JOBS:-6}"
AUTO_MERGE="${AUTO_MERGE:-false}"
RUN_BASE="${RUN_BASE:-$(pwd)/reports/backtests}"
TIMEOUT_MIN="${TIMEOUT_MIN:-120}"
REPO_PATH="${REPO_PATH:-$(pwd)}"

# -------------------------
# Run the orchestrator
# -------------------------
cd "${REPO_PATH}" || { echo "Repo root not found"; exit 1; }
mkdir -p "${RUN_BASE}"

echo "Starting Cursor orchestrator in MODE=${MODE}. Run base: ${RUN_BASE}"
export MODE WORKERS GH_TOKEN PARALLEL_JOBS AUTO_MERGE RUN_BASE TIMEOUT_MIN REPO_PATH

if [ ! -f scripts/cursor_run_and_review.sh ]; then
  echo "scripts/cursor_run_and_review.sh not found in repo root"; exit 1
fi
chmod +x scripts/cursor_run_and_review.sh

nohup bash scripts/cursor_run_and_review.sh >> /tmp/cursor_orchestrator_run.log 2>&1 &
ORCH_PID=$!
echo "Orchestrator started (PID ${ORCH_PID}); logging to /tmp/cursor_orchestrator_run.log"

echo "Tailing orchestrator log. Press Ctrl-C to stop tailing; orchestrator continues in background."
tail -n 200 -f /tmp/cursor_orchestrator_run.log & TAIL_PID=$!

END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_full_* "${RUN_BASE}"/promotion_candidate_parallel_* "${RUN_BASE}"/promotion_candidate_run_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ]; then
    if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ] && [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
      echo "Artifacts detected in ${FOUND_RUN_DIR}"
      break
    fi
  fi
  sleep 15
done

kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_RUN_DIR}" ] || [ ! -d "${FOUND_RUN_DIR}" ]; then
  echo "No run directory found within ${TIMEOUT_MIN} minutes. Check /tmp/cursor_orchestrator_run.log for progress."
  exit 2
fi

echo
echo "Run directory: ${FOUND_RUN_DIR}"
echo "---- baseline metrics (first 20 lines) ----"
if [ -f "${FOUND_RUN_DIR}/baseline/metrics.json" ]; then head -n 20 "${FOUND_RUN_DIR}/baseline/metrics.json"; elif [ -f "${FOUND_RUN_DIR}/metrics.json" ]; then head -n 20 "${FOUND_RUN_DIR}/metrics.json"; else echo "metrics.json not found"; fi
echo
echo "---- board verdict (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ]; then head -n 40 "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md"; else echo "board_verdict.md not found"; fi
echo
echo "---- PROMOTION_CANDIDATES (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then head -n 40 "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md"; else echo "PROMOTION_CANDIDATES.md not found"; fi
echo
echo "---- persona JSON (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then head -n 40 "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json"; else echo "persona_recommendations.json not found"; fi
echo
echo "Review bundle and logs are under ${FOUND_RUN_DIR} and ${RUN_BASE}. If GH_TOKEN was provided, a GitHub issue or PR may have been created."
