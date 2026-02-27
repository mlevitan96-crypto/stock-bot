#!/usr/bin/env bash
# CURSOR TASK — Run the full promotion candidate one-shot and print governance artifacts.
# Paste and run this on the droplet as the repo user in /root/stock-bot.
set -euo pipefail

REPO="/root/stock-bot"
LOG="/tmp/promotion_candidate_full_run.log"
TIMEOUT_MIN=90
POLL_SEC=15

cd "${REPO}" || { echo "Repo root ${REPO} not found"; exit 1; }

# Ensure script is executable and prerequisites
chmod +x scripts/run_promotion_candidate_full_on_droplet.sh 2>/dev/null || true
command -v parallel >/dev/null 2>&1 || echo "Warning: 'parallel' not found; install with: sudo apt update && sudo apt install -y parallel"

# Start the heavy one-shot run in background (idempotent)
if pgrep -f "run_promotion_candidate_full_on_droplet.sh" >/dev/null 2>&1; then
  echo "Full run already in progress; tailing log: ${LOG}"
else
  nohup bash scripts/run_promotion_candidate_full_on_droplet.sh >> "${LOG}" 2>&1 &
  echo "Started full promotion run; logging to ${LOG}"
fi

# Tail the log in background for live feedback (ensure file exists for tail -f)
: >> "${LOG}" 2>/dev/null || true
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# Wait for run dir to appear and key artifacts to be produced
END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  RUN_DIR=$(ls -td reports/backtests/promotion_candidate_full_* 2>/dev/null | head -n1 || true)
  if [ -n "${RUN_DIR}" ] && [ -d "${RUN_DIR}" ]; then
    if [ -f "${RUN_DIR}/multi_model/out/board_verdict.md" ] && [ -f "${RUN_DIR}/PROMOTION_CANDIDATES.md" ] && [ -f "${RUN_DIR}/baseline/metrics.json" ]; then
      echo "Key artifacts detected in ${RUN_DIR}"
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

# Stop tailing
kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${RUN_DIR}" ] || [ ! -d "${RUN_DIR}" ]; then
  echo "No run directory with key artifacts found within ${TIMEOUT_MIN} minutes. Check ${LOG} for progress."
  exit 2
fi

echo
echo "=== Run directory ==="
echo "${RUN_DIR}"

echo
echo "=== Promotion candidate metrics (first 20 lines) ==="
if [ -f "${RUN_DIR}/baseline/metrics.json" ]; then
  head -n 20 "${RUN_DIR}/baseline/metrics.json"
elif [ -f "${RUN_DIR}/metrics.json" ]; then
  head -n 20 "${RUN_DIR}/metrics.json"
else
  echo "metrics.json not found under ${RUN_DIR}"
fi

echo
echo "=== Exec sensitivity summary (if present) ==="
if [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  jq '.' "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" 2>/dev/null || cat "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
elif [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
  jq '.' "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" 2>/dev/null || cat "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json"
else
  echo "exec_sensitivity summary not found under ${RUN_DIR}"
fi

echo
echo "=== Multi-model board verdict (first 40 lines) ==="
if [ -f "${RUN_DIR}/multi_model/out/board_verdict.md" ]; then
  head -n 40 "${RUN_DIR}/multi_model/out/board_verdict.md"
else
  echo "board_verdict.md not found at ${RUN_DIR}/multi_model/out/board_verdict.md"
fi

echo
echo "=== Promotion candidates (first 40 lines) ==="
if [ -f "${RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
  head -n 40 "${RUN_DIR}/PROMOTION_CANDIDATES.md"
else
  echo "PROMOTION_CANDIDATES.md not found at ${RUN_DIR}"
fi

echo
echo "=== Persona recommendations JSON (first 40 lines) ==="
if [ -f "${RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then
  head -n 40 "${RUN_DIR}/multi_model/out/persona_recommendations.json"
else
  echo "persona_recommendations.json not found at ${RUN_DIR}/multi_model/out/persona_recommendations.json"
fi

echo
echo "Artifacts listing:"
ls -la "${RUN_DIR}" 2>/dev/null || true

# If board verdict contains ACCEPT, print next-step commands (best-effort)
if [ -f "${RUN_DIR}/multi_model/out/board_verdict.md" ] && grep -qi "ACCEPT" "${RUN_DIR}/multi_model/out/board_verdict.md" 2>/dev/null; then
  echo
  echo "BOARD VERDICT: ACCEPT detected."
  echo "Next steps (copy/paste):"
  echo "  git checkout main && git pull origin main"
  echo "  git checkout -b promote/promotion_candidate_1"
  echo "  git add configs/overlays/promotion_candidate_1.json"
  echo "  git commit -m \"Promotion candidate: reduce dark_pool and smooth freshness_factor (promotion_candidate_1)\""
  echo "  git push -u origin promote/promotion_candidate_1"
  echo "  # PR body available at: /tmp/promotion_candidate_1_PR_BODY.md (or in ${RUN_DIR})"
else
  echo
  echo "BOARD VERDICT: not ACCEPT (or board_verdict.md missing). Review artifacts and iterate."
fi

echo
echo "If anything looks off, inspect the run log: tail -n 400 ${LOG}"
echo "Done."
