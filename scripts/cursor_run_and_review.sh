#!/usr/bin/env bash
# cursor_run_and_review.sh
# Single block to run the full promotion-candidate flow (local/droplet/parallel)
# and produce an automated code+plan review (optionally open a GitHub issue).
#
# Usage examples:
#   MODE=local bash scripts/cursor_run_and_review.sh
#   MODE=droplet bash scripts/cursor_run_and_review.sh
#   MODE=parallel WORKERS="host1 host2" GH_TOKEN="..." bash scripts/cursor_run_and_review.sh
#
# Environment variables:
#   MODE            = local | droplet | parallel   (default: local)
#   WORKERS         = space-separated worker hosts (for parallel; also set in orchestrator if needed)
#   REMOTE_USER     = SSH user for workers (default: root)
#   PARALLEL_JOBS   = parallelism for local runs (default: 6)
#   GH_TOKEN        = GitHub token for creating issue/PR (optional)
#   AUTO_MERGE      = true|false (if GH_TOKEN set and you want auto-merge; default false)
#   RUN_BASE        = base dir for run artifacts (default: ./reports/backtests)
#   TIMEOUT_MIN     = minutes to wait for artifacts (default: 120)
#   REPO_PATH       = repo root (default: $(pwd))
set -euo pipefail

# -------------------------
# Config and defaults
# -------------------------
MODE="${MODE:-local}"
WORKERS="${WORKERS:-}"
REMOTE_USER="${REMOTE_USER:-root}"
PARALLEL_JOBS="${PARALLEL_JOBS:-6}"
GH_TOKEN="${GH_TOKEN:-}"
AUTO_MERGE="${AUTO_MERGE:-false}"
RUN_BASE="${RUN_BASE:-$(pwd)/reports/backtests}"
TIMEOUT_MIN="${TIMEOUT_MIN:-120}"
POLL_SEC="${POLL_SEC:-15}"
REPO_PATH="${REPO_PATH:-$(pwd)}"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${RUN_BASE}/promotion_candidate_run_${TIMESTAMP}"
LOG="${RUN_DIR}/controller.log"
REVIEW_FILE="${RUN_DIR}/cursor_review_bundle.txt"
mkdir -p "${RUN_DIR}"
: >> "${LOG}" 2>/dev/null || true

echo "Cursor orchestrator starting" | tee -a "${LOG}"
echo "Mode: ${MODE}" | tee -a "${LOG}"
echo "Run dir: ${RUN_DIR}" | tee -a "${LOG}"

# -------------------------
# Helper functions
# -------------------------
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail() { log "ERROR: $*"; exit 1; }

# Wait for artifacts helper
wait_for_artifacts() {
  local run_dir="$1"
  local timeout_min="$2"
  local poll_sec="$3"
  local end_time=$(( $(date +%s) + timeout_min*60 ))
  while [ "$(date +%s)" -lt "${end_time}" ]; do
    if [ -d "${run_dir}" ]; then
      if [ -f "${run_dir}/baseline/metrics.json" ] && [ -f "${run_dir}/multi_model/out/board_verdict.md" ] && [ -f "${run_dir}/PROMOTION_CANDIDATES.md" ]; then
        log "Artifacts present in ${run_dir}"
        return 0
      fi
    fi
    sleep "${poll_sec}"
  done
  return 1
}

# Create PR body file (used if GH_TOKEN present)
write_pr_body() {
  local out="$1"
  cat > "${out}" <<'MD'
PR title: Paper promotion: reduce dark_pool weight and smooth freshness_factor

Summary
-------
Introduce a minimal, reversible overlay to reduce single-signal fragility and improve robustness in paper trading.

Changes
-------
- configs/overlays/promotion_candidate_1.json
  - dark_pool weight set to 0.75
  - freshness_factor weight set to 0.7
  - freshness_smoothing_window set to 3

Validation plan
---------------
1. Focused backtest with overlay and compare metrics to baseline.
2. Exec sensitivity at 0x, 1x, 2x slippage and confirm acceptable degradation.
3. Multi-model adversarial review with full evidence and board verdict.
4. Paper run for 7 trading days with monitoring; if stable, canary for 14 days.

Acceptance criteria
-------------------
- Net PnL ≥ 90% of baseline on snapshot
- Exec sensitivity positive at 1x and 2x slippage
- Reduced single-signal fragility for dark_pool and freshness_factor
- Multi-model board verdict ACCEPT or minor mitigations
- Customer advocate endorses or lists manageable concerns

Rollback
--------
Revert the overlay file or re-apply the previous overlay. This is a single-file change and can be reverted in one commit.
MD
}

# -------------------------
# Ensure repo and scripts are executable
# -------------------------
log "Preparing repository and scripts"
cd "${REPO_PATH}" || fail "Repo path ${REPO_PATH} not found"
git pull origin main >> "${LOG}" 2>&1 || log "git pull failed or offline; continuing"

for s in \
  scripts/run_promotion_candidate_full_on_droplet.sh \
  scripts/run_promotion_candidate_full_oneshot_on_droplet.sh \
  scripts/run_promotion_candidate_1_single_run_on_droplet.sh \
  scripts/run_promotion_candidate_parallel_orchestrator.sh; do
  [ -f "${s}" ] && chmod +x "${s}" 2>/dev/null || true
done

# -------------------------
# Run the chosen mode
# -------------------------
case "${MODE}" in
  local)
    log "MODE=local: running full one-shot locally"
    if [ ! -x scripts/run_promotion_candidate_full_on_droplet.sh ]; then
      fail "Local run script scripts/run_promotion_candidate_full_on_droplet.sh not found or not executable"
    fi
    nohup bash scripts/run_promotion_candidate_full_on_droplet.sh >> "${LOG}" 2>&1 &
    RUN_PID=$!
    log "Started local run (PID ${RUN_PID})"
    ;;

  droplet)
    log "MODE=droplet: running single-node droplet script"
    if [ -x scripts/run_promotion_candidate_full_oneshot_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_full_oneshot_on_droplet.sh >> "${LOG}" 2>&1 &
    elif [ -x scripts/run_promotion_candidate_1_single_run_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_single_run_on_droplet.sh >> "${LOG}" 2>&1 &
    else
      fail "Droplet run script not found (run_promotion_candidate_full_oneshot_on_droplet.sh or run_promotion_candidate_1_single_run_on_droplet.sh)"
    fi
    RUN_PID=$!
    log "Started droplet run (PID ${RUN_PID})"
    ;;

  parallel)
    log "MODE=parallel: running parallel orchestrator (controller dispatches to workers)"
    if [ -z "${WORKERS}" ]; then
      fail "WORKERS not set. Provide WORKERS=\"host1 host2\" and ensure scripts/run_promotion_candidate_parallel_orchestrator.sh WORKERS array matches or is overridden by env."
    fi
    if [ ! -x scripts/run_promotion_candidate_parallel_orchestrator.sh ]; then
      fail "Parallel orchestrator script not found or not executable"
    fi
    export WORKERS
    export REMOTE_USER
    export PARALLEL_JOBS
    export GH_TOKEN
    export AUTO_MERGE
    nohup bash scripts/run_promotion_candidate_parallel_orchestrator.sh >> "${LOG}" 2>&1 &
    RUN_PID=$!
    log "Started parallel orchestrator (PID ${RUN_PID})"
    ;;

  *)
    fail "Unknown MODE: ${MODE}. Use local|droplet|parallel"
    ;;
esac

# -------------------------
# Tail log and wait for artifacts
# -------------------------
log "Tailing log (${LOG}) in background for live feedback"
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# Wait for run dir to appear (run scripts create timestamped or fixed dirs under reports/backtests)
END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_full_* "${RUN_BASE}"/promotion_candidate_parallel_* "${RUN_BASE}"/promotion_candidate_run_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ]; then
    log "Detected run dir: ${FOUND_RUN_DIR}"
    if wait_for_artifacts "${FOUND_RUN_DIR}" 5 5; then
      log "Key artifacts detected in ${FOUND_RUN_DIR}"
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_RUN_DIR}" ] || [ ! -d "${FOUND_RUN_DIR}" ]; then
  log "No run directory with artifacts found within ${TIMEOUT_MIN} minutes. Check ${LOG} for progress."
  FOUND_RUN_DIR="${RUN_DIR}"
fi

# -------------------------
# Collect governance excerpts
# -------------------------
EXCERPT_DIR="${RUN_DIR}/excerpts"
mkdir -p "${EXCERPT_DIR}"
log "Collecting governance excerpts into ${EXCERPT_DIR}"

if [ -f "${FOUND_RUN_DIR}/baseline/metrics.json" ]; then
  head -n 20 "${FOUND_RUN_DIR}/baseline/metrics.json" > "${EXCERPT_DIR}/baseline_metrics_head.txt" 2>/dev/null || true
elif [ -f "${FOUND_RUN_DIR}/metrics.json" ]; then
  head -n 20 "${FOUND_RUN_DIR}/metrics.json" > "${EXCERPT_DIR}/baseline_metrics_head.txt" 2>/dev/null || true
fi

if [ -f "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  jq '.' "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" 2>/dev/null > "${EXCERPT_DIR}/exec_sensitivity.json" || cp "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" "${EXCERPT_DIR}/exec_sensitivity.json" 2>/dev/null || true
fi

if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ]; then
  head -n 40 "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" > "${EXCERPT_DIR}/board_verdict_head.md" 2>/dev/null || true
fi

if [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
  head -n 40 "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" > "${EXCERPT_DIR}/promotion_candidates_head.md" 2>/dev/null || true
fi

if [ -f "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then
  head -n 40 "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" > "${EXCERPT_DIR}/persona_json_head.json" 2>/dev/null || true
fi

tail -n 200 "${LOG}" > "${EXCERPT_DIR}/run_log_tail.txt" 2>/dev/null || true

# -------------------------
# Automated code + plan review
# -------------------------
log "Running automated code + plan review (static checks and summary)"

{
  echo "Cursor review bundle"
  echo "Run dir: ${FOUND_RUN_DIR}"
  echo "Timestamp: ${TIMESTAMP}"
  echo
  echo "=== Git status (controller) ==="
  git status --porcelain --untracked-files=no 2>/dev/null || true
  echo
  echo "=== Recent commits (last 5) ==="
  git --no-pager log -n 5 --pretty=oneline 2>/dev/null || true
  echo
  echo "=== Scripts present ==="
  ls -1 scripts 2>/dev/null | sed -n '1,200p' || true
  echo
  echo "=== Static checks ==="
} > "${REVIEW_FILE}"

if command -v shellcheck >/dev/null 2>&1; then
  echo "Running shellcheck on scripts/*.sh" >> "${REVIEW_FILE}"
  shellcheck -x scripts/*.sh >> "${REVIEW_FILE}" 2>&1 || true
else
  echo "shellcheck not installed; skipping shellcheck" >> "${REVIEW_FILE}"
fi

if command -v flake8 >/dev/null 2>&1; then
  echo "Running flake8 on python scripts" >> "${REVIEW_FILE}"
  flake8 . >> "${REVIEW_FILE}" 2>&1 || true
elif command -v pyflakes >/dev/null 2>&1; then
  echo "Running pyflakes on python scripts" >> "${REVIEW_FILE}"
  pyflakes . >> "${REVIEW_FILE}" 2>&1 || true
else
  echo "flake8/pyflakes not installed; skipping python lint" >> "${REVIEW_FILE}"
fi

{
  echo
  echo "=== Governance excerpts ==="
  for f in "${EXCERPT_DIR}"/*; do
    [ -f "$f" ] || continue
    echo
    echo "---- $(basename "$f") ----"
    sed -n '1,200p' "$f" 2>/dev/null || true
  done
} >> "${REVIEW_FILE}"

log "Review bundle written to ${REVIEW_FILE}"

# -------------------------
# Optionally create GitHub issue to request Cursor review
# -------------------------
if [ -n "${GH_TOKEN}" ] && command -v gh >/dev/null 2>&1; then
  log "Creating GitHub issue with review bundle (requires GH_TOKEN)"
  echo "${GH_TOKEN}" | gh auth login --with-token 2>/dev/null || true
  ISSUE_TITLE="Cursor: review orchestrator run ${TIMESTAMP}"
  gh issue create --title "${ISSUE_TITLE}" --body-file "${REVIEW_FILE}" 2>/dev/null || log "gh issue create failed"
  log "GitHub issue created (or attempted)."
else
  log "GH_TOKEN not set or gh not installed; skipping GitHub issue creation."
  log "Review bundle available at: ${REVIEW_FILE}"
fi

# -------------------------
# Final output and next steps
# -------------------------
log "Cursor orchestrator finished. Artifacts and review bundle are in ${RUN_DIR}"
cat <<EOF | tee -a "${LOG}"
NEXT STEPS:
- Inspect excerpts in ${EXCERPT_DIR}
- If board verdict is ACCEPT and GH_TOKEN was provided, check the created PR or issue in the repo
- To re-run with parallel workers: MODE=parallel WORKERS="host1 host2" bash scripts/cursor_run_and_review.sh
- To run locally: MODE=local bash scripts/cursor_run_and_review.sh
- Review bundle: ${REVIEW_FILE}
EOF

echo
echo "=== Quick artifact pointers ==="
echo "Run dir: ${FOUND_RUN_DIR}"
echo "Baseline metrics: ${FOUND_RUN_DIR}/baseline/metrics.json"
echo "Board verdict: ${FOUND_RUN_DIR}/multi_model/out/board_verdict.md"
echo "Persona JSON: ${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json"
echo "Promotion candidates: ${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md"
echo "Review bundle: ${REVIEW_FILE}"

exit 0
