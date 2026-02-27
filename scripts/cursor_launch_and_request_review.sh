#!/usr/bin/env bash
# cursor_launch_and_request_review.sh
# Single-run launcher: start the Cursor orchestrator (local|droplet|parallel),
# tail logs, wait for artifacts, and print governance excerpts + review bundle path.
#
# Usage examples:
#   MODE=local bash scripts/cursor_launch_and_request_review.sh
#   MODE=droplet bash scripts/cursor_launch_and_request_review.sh
#   MODE=parallel WORKERS="host1 host2" GH_TOKEN="..." bash scripts/cursor_launch_and_request_review.sh
set -euo pipefail

# -------------------------
# Configuration (edit as needed)
# -------------------------
MODE="${MODE:-local}"                       # local | droplet | parallel
WORKERS="${WORKERS:-}"                      # space-separated hosts for parallel mode
GH_TOKEN="${GH_TOKEN:-}"                    # optional: set to enable GitHub issue/PR creation
PARALLEL_JOBS="${PARALLEL_JOBS:-6}"
AUTO_MERGE="${AUTO_MERGE:-false}"
RUN_BASE="${RUN_BASE:-$(pwd)/reports/backtests}"
TIMEOUT_MIN="${TIMEOUT_MIN:-120}"
POLL_SEC="${POLL_SEC:-15}"
REPO_PATH="${REPO_PATH:-$(pwd)}"            # repo root where scripts live

# -------------------------
# Prepare environment
# -------------------------
cd "${REPO_PATH}" || { echo "Repo root ${REPO_PATH} not found"; exit 1; }
mkdir -p "${RUN_BASE}"
LOG="/tmp/cursor_orchestrator_run.log"
: > "${LOG}"

ORCH_SCRIPT="scripts/cursor_run_and_review.sh"
if [ ! -f "${ORCH_SCRIPT}" ]; then
  echo "Orchestrator script ${ORCH_SCRIPT} not found in ${REPO_PATH}" | tee -a "${LOG}"
  exit 1
fi
chmod +x "${ORCH_SCRIPT}"

export MODE WORKERS GH_TOKEN PARALLEL_JOBS AUTO_MERGE RUN_BASE TIMEOUT_MIN REPO_PATH

# -------------------------
# Start orchestrator
# -------------------------
echo "Starting Cursor orchestrator (MODE=${MODE}) — log: ${LOG}"
nohup bash "${ORCH_SCRIPT}" >> "${LOG}" 2>&1 &
ORCH_PID=$!
echo "Orchestrator PID ${ORCH_PID}"

echo "Tailing ${LOG} (Ctrl-C to stop tailing; orchestrator continues in background)"
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# -------------------------
# Wait for run dir and artifacts
# -------------------------
END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_full_* "${RUN_BASE}"/promotion_candidate_parallel_* "${RUN_BASE}"/promotion_candidate_run_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ]; then
    if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ] && [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
      echo "Artifacts detected in ${FOUND_RUN_DIR}" | tee -a "${LOG}"
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_RUN_DIR}" ] || [ ! -d "${FOUND_RUN_DIR}" ]; then
  echo "No run directory found within ${TIMEOUT_MIN} minutes. Check ${LOG} for progress." | tee -a "${LOG}"
  exit 2
fi

# -------------------------
# Print concise governance excerpts
# -------------------------
echo
echo "Run directory: ${FOUND_RUN_DIR}"
echo
echo "---- baseline metrics (first 20 lines) ----"
if [ -f "${FOUND_RUN_DIR}/baseline/metrics.json" ]; then
  head -n 20 "${FOUND_RUN_DIR}/baseline/metrics.json"
elif [ -f "${FOUND_RUN_DIR}/metrics.json" ]; then
  head -n 20 "${FOUND_RUN_DIR}/metrics.json"
else
  echo "metrics.json not found"
fi

echo
echo "---- exec sensitivity (if present) ----"
if [ -f "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  jq '.' "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" 2>/dev/null || cat "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
else
  echo "exec_sensitivity not found"
fi

echo
echo "---- board verdict (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ]; then
  head -n 40 "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md"
else
  echo "board_verdict.md not found"
fi

echo
echo "---- PROMOTION_CANDIDATES (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
  head -n 40 "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md"
else
  echo "PROMOTION_CANDIDATES.md not found"
fi

echo
echo "---- persona JSON (first 40 lines) ----"
if [ -f "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then
  head -n 40 "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json"
else
  echo "persona_recommendations.json not found"
fi

echo
echo "Review bundle and logs are under: ${FOUND_RUN_DIR}"
if [ -n "${GH_TOKEN}" ]; then
  echo "GH_TOKEN provided — orchestrator may have created a GitHub issue or PR for review."
else
  echo "No GH_TOKEN — review bundle created locally. To open a GitHub issue or PR, set GH_TOKEN and re-run in parallel mode."
fi

echo
echo "NEXT STEPS:"
echo "- Inspect the excerpts above and the review bundle under ${FOUND_RUN_DIR}/excerpts or ${FOUND_RUN_DIR}/cursor_review_bundle.txt"
echo "- If board verdict is ACCEPT and a PR was created, follow the PR for CI and merge on green; rollback commands are appended to the controller log."
echo
echo "Done."
