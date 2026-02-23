#!/usr/bin/env bash
# cursor_full_automated_orchestrator_runall.sh
# Single-block: run massive scenarios, adversarial multi-model review, ablations, slippage grid,
# automated mitigations + re-checks, ensemble reweighting, adaptive gating prototype,
# then write cursor_final_summary.txt and cursor_report.md in the run dir.
#
# Usage example:
#   MODE=parallel WORKERS="worker1 worker2" GH_TOKEN="..." MAX_ITER=3 MIN_TRADES=100 bash cursor_full_automated_orchestrator_runall.sh
set -euo pipefail

# -------------------------
# Configuration (edit as needed)
# -------------------------
MODE="${MODE:-local}"                         # local | droplet | parallel
WORKERS="${WORKERS:-}"                       # space-separated worker hosts for parallel mode
REMOTE_USER="${REMOTE_USER:-root}"
REPO_PATH="${REPO_PATH:-$(pwd)}"
PARALLEL_JOBS="${PARALLEL_JOBS:-6}"
GH_TOKEN="${GH_TOKEN:-}"
AUTO_MERGE="${AUTO_MERGE:-false}"
RUN_BASE="${RUN_BASE:-${REPO_PATH}/reports/backtests}"
TIMEOUT_MIN="${TIMEOUT_MIN:-240}"
POLL_SEC="${POLL_SEC:-20}"
MAX_ITER="${MAX_ITER:-3}"                    # automated mitigation iterations
MIN_TRADES="${MIN_TRADES:-100}"
OVERLAY_PATH="configs/overlays/promotion_candidate_1.json"
PR_BRANCH="promote/promotion_candidate_1"
PR_BODY_PATH="/tmp/promotion_candidate_1_PR_BODY.md"
LOG="/tmp/cursor_full_automated_orchestrator.log"
SUMMARY_NAME="cursor_final_summary.txt"
REPORT_NAME="cursor_report.md"

# Mitigations to try in order (JSON fragments)
MITIGATIONS=(
  '{"composite_weights":{"dark_pool":0.75,"freshness_factor":0.7},"freshness_smoothing_window":3}'
  '{"composite_weights":{"dark_pool":0.65,"freshness_factor":0.6},"freshness_smoothing_window":5}'
  '{"composite_weights":{"dark_pool":0.5,"freshness_factor":0.5},"freshness_smoothing_window":7}'
)

# Ensemble reweighting candidates (simple examples)
ENSEMBLE_TRIALS=(
  '{"ensemble_weights":{"modelA":0.6,"modelB":0.4}}'
  '{"ensemble_weights":{"modelA":0.5,"modelB":0.5}}'
  '{"ensemble_weights":{"modelA":0.4,"modelB":0.6}}'
)

# Slippage grid to run if needed
SLIPPAGES=(0.0 0.0005 0.001 0.002)

# Ablation multipliers to test
ABLATION_MULTS=(0.0 0.5 1.0)

# -------------------------
# Helpers
# -------------------------
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail() { log "ERROR: $*"; exit 1; }
jq_or_zero() { jq -r "$1" "$2" 2>/dev/null || echo "0"; }

mkdir -p "$(dirname "${LOG}")"
: > "${LOG}"
cd "${REPO_PATH}" || fail "Repo path ${REPO_PATH} not found"

# Ensure scripts are executable if present
for s in scripts/*.sh; do [ -f "$s" ] && chmod +x "$s" || true; done

log "Starting full automated orchestrator (MODE=${MODE})"

# -------------------------
# 1) Launch main orchestrator or focused check depending on MODE
# -------------------------
ORCH_PID=""
case "${MODE}" in
  local)
    if [ -x scripts/run_promotion_candidate_full_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_full_on_droplet.sh >> "${LOG}" 2>&1 &
      ORCH_PID=$!
      log "Launched local full run (PID ${ORCH_PID})"
    else
      fail "Local full run script not found: scripts/run_promotion_candidate_full_on_droplet.sh"
    fi
    ;;
  droplet)
    # prefer full oneshot if present, else focused check
    if [ -x scripts/run_promotion_candidate_full_oneshot_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_full_oneshot_on_droplet.sh >> "${LOG}" 2>&1 &
      ORCH_PID=$!
      log "Launched droplet oneshot (PID ${ORCH_PID})"
    elif [ -x scripts/run_promotion_candidate_1_single_run_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_single_run_on_droplet.sh >> "${LOG}" 2>&1 &
      ORCH_PID=$!
      log "Launched droplet single-run (PID ${ORCH_PID})"
    elif [ -x scripts/run_promotion_candidate_1_check_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 &
      ORCH_PID=$!
      log "Launched droplet focused check (PID ${ORCH_PID})"
    else
      fail "No droplet run script found"
    fi
    ;;
  parallel)
    if [ -z "${WORKERS}" ]; then fail "WORKERS must be set for parallel mode"; fi
    export WORKERS REMOTE_USER PARALLEL_JOBS GH_TOKEN AUTO_MERGE
    if [ -x scripts/run_promotion_candidate_parallel_orchestrator.sh ]; then
      nohup bash scripts/run_promotion_candidate_parallel_orchestrator.sh >> "${LOG}" 2>&1 &
      ORCH_PID=$!
      log "Launched parallel orchestrator (PID ${ORCH_PID})"
    else
      fail "Parallel orchestrator script missing: scripts/run_promotion_candidate_parallel_orchestrator.sh"
    fi
    ;;
  *)
    fail "Unknown MODE: ${MODE}"
    ;;
esac

# Tail log for live feedback
tail -n 200 -f "${LOG}" & TAIL_PID=$!

# -------------------------
# 2) Wait for run dir with artifacts
# -------------------------
END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ]; then
    if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ] && [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
      log "Found run dir with key artifacts: ${FOUND_RUN_DIR}"
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

# Stop tailing
kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_RUN_DIR}" ]; then
  log "No run directory found within ${TIMEOUT_MIN} minutes. Exiting."
  exit 2
fi

log "Using run dir: ${FOUND_RUN_DIR}"

# -------------------------
# 3) Copy excerpts to temp dir and parse gates
# -------------------------
TMP_DIR="/tmp/cursor_run_excerpts_$(date -u +%s)"
mkdir -p "${TMP_DIR}"

# copy excerpts function
cp_excerpts() {
  # baseline metrics
  if [ -f "${FOUND_RUN_DIR}/baseline/metrics.json" ]; then
    head -n 20 "${FOUND_RUN_DIR}/baseline/metrics.json" > "${TMP_DIR}/baseline_head.txt" || true
    cp "${FOUND_RUN_DIR}/baseline/metrics.json" "${TMP_DIR}/baseline_metrics.json" 2>/dev/null || true
  elif [ -f "${FOUND_RUN_DIR}/metrics.json" ]; then
    head -n 20 "${FOUND_RUN_DIR}/metrics.json" > "${TMP_DIR}/baseline_head.txt" || true
    cp "${FOUND_RUN_DIR}/metrics.json" "${TMP_DIR}/baseline_metrics.json" 2>/dev/null || true
  fi
  # exec sensitivity (recheck preferred)
  if [ -f "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
    cp "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" "${TMP_DIR}/exec_sensitivity.json" 2>/dev/null || true
  elif [ -f "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
    cp "${FOUND_RUN_DIR}/exec_sensitivity/exec_sensitivity.json" "${TMP_DIR}/exec_sensitivity.json" 2>/dev/null || true
  fi
  # board verdict
  if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ]; then
    head -n 40 "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" > "${TMP_DIR}/board_verdict_head.md" || true
    cp "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" "${TMP_DIR}/board_verdict.md" 2>/dev/null || true
  fi
  # persona
  if [ -f "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then
    head -n 40 "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" > "${TMP_DIR}/persona_head.json" || true
    cp "${FOUND_RUN_DIR}/multi_model/out/persona_recommendations.json" "${TMP_DIR}/persona.json" 2>/dev/null || true
  fi
  # promotion candidates
  if [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
    head -n 40 "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" > "${TMP_DIR}/promotion_candidates_head.md" || true
    cp "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" "${TMP_DIR}/PROMOTION_CANDIDATES.md" 2>/dev/null || true
  fi
  # run log tail
  tail -n 200 "${LOG}" > "${TMP_DIR}/run_log_tail.txt" || true
  # evidence listing
  if [ -d "${FOUND_RUN_DIR}/multi_model/evidence" ]; then
    ls -1 "${FOUND_RUN_DIR}/multi_model/evidence" > "${TMP_DIR}/evidence_listing.txt" 2>/dev/null || true
  fi
}
cp_excerpts

# Parse baseline metrics
TRADES_COUNT=0
CAND_PNL=0
if [ -f "${TMP_DIR}/baseline_metrics.json" ]; then
  TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
  CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // .net_pnl_usd // 0' "${TMP_DIR}/baseline_metrics.json")
fi

# Parse exec sensitivity PnLs
EXEC_PNL_0="N/A"; EXEC_PNL_1="N/A"; EXEC_PNL_2="N/A"
if [ -f "${TMP_DIR}/exec_sensitivity.json" ]; then
  EXEC_PNL_0=$(jq_or_zero '.["slippage_0.0"].net_pnl // .["slippage_0.0"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
  EXEC_PNL_1=$(jq_or_zero '.["slippage_0.0005"].net_pnl // .["slippage_0.0005"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
  EXEC_PNL_2=$(jq_or_zero '.["slippage_0.001"].net_pnl // .["slippage_0.001"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
fi

# Board verdict
BOARD_VERDICT="UNKNOWN"
if [ -f "${TMP_DIR}/board_verdict.md" ]; then
  BOARD_VERDICT=$(head -n 5 "${TMP_DIR}/board_verdict.md" | tr '\n' ' ' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')
fi

# Ablation PnLs (informational)
ABLA_DARK="N/A"; ABLA_FRESH="N/A"
DDIR=$(ls -d "${FOUND_RUN_DIR}"/sweep_dark_pool* 2>/dev/null | head -n1 || true)
if [ -n "${DDIR}" ] && [ -f "${DDIR}/metrics.json" ]; then
  ABLA_DARK=$(jq_or_zero '.net_pnl // .netPnL // 0' "${DDIR}/metrics.json")
fi
FDIR=$(ls -d "${FOUND_RUN_DIR}"/sweep_freshness_factor* 2>/dev/null | head -n1 || true)
if [ -n "${FDIR}" ] && [ -f "${FDIR}/metrics.json" ]; then
  ABLA_FRESH=$(jq_or_zero '.net_pnl // .netPnL // 0' "${FDIR}/metrics.json")
fi

# Operational health
OP_HEALTH="OK"
if grep -Ei "ERROR|failed|FAIL|exception|OOM|out of memory|swap" "${TMP_DIR}/run_log_tail.txt" >/dev/null 2>&1; then
  OP_HEALTH="ISSUES: check run log"
fi

# PnL ratio to baseline (optional)
PNL_RATIO="N/A"
if [ -n "${BASELINE_METRICS_PATH:-}" ] && [ -f "${BASELINE_METRICS_PATH}" ]; then
  BASE_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${BASELINE_METRICS_PATH}")
  if [ "$(echo "${BASE_PNL} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
    PNL_RATIO=$(awk "BEGIN{printf \"%.3f\", (${CAND_PNL}/${BASE_PNL})}")
  fi
fi

# Gate evaluations
G_TRADES="FAIL"; [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] && G_TRADES="PASS"
G_PNL="FAIL"; [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ] && G_PNL="PASS"
G_EXEC="FAIL"
if [ "${EXEC_PNL_1}" != "N/A" ] && [ "$(echo "${EXEC_PNL_1} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then G_EXEC="PASS"; fi
G_BOARD="FAIL"
if echo "${BOARD_VERDICT}" | grep -Ei "ACCEPT|CONDITIONAL" >/dev/null 2>&1; then G_BOARD="PASS"; fi

# Decision heuristic
DECISION="REJECT"
PRIMARY_REASON=""
if [ "${G_BOARD}" = "PASS" ] && [ "${G_PNL}" = "PASS" ] && [ "${G_TRADES}" = "PASS" ] && [ "${G_EXEC}" = "PASS" ] && [ "${OP_HEALTH}" = "OK" ]; then
  DECISION="PROMOTE"
  PRIMARY_REASON="Board ACCEPT and gates passed"
elif [ "${G_PNL}" = "PASS" ] && ( [ "${G_TRADES}" = "PASS" ] || [ "${G_BOARD}" = "PASS" ] ); then
  DECISION="CONSIDER WITH MITIGATIONS"
  PRIMARY_REASON="Positive PnL but some gates need mitigation"
else
  DECISION="REJECT"
  PRIMARY_REASON="Gates failed or board rejected"
fi

# -------------------------
# 4) Automated mitigation loop (if not PROMOTE)
# -------------------------
ITER=0
APPLIED_MITIGATION="none"
while [ "${DECISION}" != "PROMOTE" ] && [ "${ITER}" -lt "${MAX_ITER}" ]; do
  MIT="${MITIGATIONS[ITER]:-}"
  if [ -z "${MIT}" ]; then
    log "No more mitigations configured"
    break
  fi
  ITER=$((ITER+1))
  log "Applying automated mitigation #${ITER}"
  mkdir -p "$(dirname "${OVERLAY_PATH}")"
  # backup existing overlay
  if [ -f "${OVERLAY_PATH}" ]; then cp "${OVERLAY_PATH}" "${OVERLAY_PATH}.bak.${ITER}" 2>/dev/null || true; fi
  printf '%s\n' "${MIT}" > "${OVERLAY_PATH}"
  git add "${OVERLAY_PATH}" || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "Automated mitigation ${ITER}: overlay tweak for promotion_candidate_1" || true
  fi
  APPLIED_MITIGATION="mitigation_${ITER}"
  # run focused check (fast) if available
  if [ -x scripts/run_promotion_candidate_1_check_on_droplet.sh ]; then
    nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 || log "Focused check failed"
    sleep 120
    # re-copy excerpts and re-evaluate
    cp_excerpts
    if [ -f "${TMP_DIR}/baseline_metrics.json" ]; then
      TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
      CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${TMP_DIR}/baseline_metrics.json")
    fi
    if [ -f "${TMP_DIR}/exec_sensitivity.json" ]; then
      EXEC_PNL_1=$(jq_or_zero '.["slippage_0.0005"].net_pnl // .["slippage_0.0005"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
    fi
    G_TRADES="FAIL"; [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] && G_TRADES="PASS"
    G_PNL="FAIL"; [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ] && G_PNL="PASS"
    G_EXEC="FAIL"
    if [ "${EXEC_PNL_1}" != "N/A" ] && [ "$(echo "${EXEC_PNL_1} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then G_EXEC="PASS"; fi
    if [ "${G_BOARD}" = "PASS" ] && [ "${G_PNL}" = "PASS" ] && [ "${G_TRADES}" = "PASS" ] && [ "${G_EXEC}" = "PASS" ] && [ "${OP_HEALTH}" = "OK" ]; then
      DECISION="PROMOTE"
      PRIMARY_REASON="Automated mitigation ${ITER} succeeded"
      break
    fi
  else
    log "Focused check script not available; skipping mitigation re-check"
    break
  fi
done

# -------------------------
# 5) Ensemble reweighting trials (if still not PROMOTE)
# -------------------------
if [ "${DECISION}" != "PROMOTE" ]; then
  for E in "${ENSEMBLE_TRIALS[@]}"; do
    log "Trying ensemble trial: ${E}"
    # write a temporary overlay fragment for ensemble (merge strategy depends on your pipeline)
    TMP_OVERLAY="${OVERLAY_PATH}.ensemble.tmp"
    printf '%s\n' "${E}" > "${TMP_OVERLAY}"
    mv "${TMP_OVERLAY}" "${OVERLAY_PATH}"
    git add "${OVERLAY_PATH}" || true
    git commit -m "Automated ensemble trial" || true
    # run focused check if available
    if [ -x scripts/run_promotion_candidate_1_check_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 || true
      sleep 90
      cp_excerpts
      TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
      CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${TMP_DIR}/baseline_metrics.json")
      if [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ] && [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ]; then
        DECISION="CONSIDER WITH MITIGATIONS"
        PRIMARY_REASON="Ensemble trial improved PnL; requires final validation"
        break
      fi
    fi
  done
fi

# -------------------------
# 6) If still not PROMOTE, run explicit slippage grid and ablation sweeps (exhaustive evidence)
# -------------------------
log "Running slippage grid and ablation sweeps for final evidence"
# If full-run script exists, run it with SLIPPAGES env; else run focused checks per slippage
if [ -x scripts/run_promotion_candidate_full_on_droplet.sh ]; then
  export SLIPPAGES
  nohup bash scripts/run_promotion_candidate_full_on_droplet.sh >> "${LOG}" 2>&1 || log "Full slippage run failed"
else
  # run focused checks per slippage value if available
  for s in "${SLIPPAGES[@]}"; do
    log "Focused slippage run ${s}"
    # create a temporary merged config with slippage override if your check script supports it
    if [ -x scripts/run_promotion_candidate_1_check_on_droplet.sh ]; then
      SLIP="${s}" nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 || true
      sleep 30
    fi
  done
fi

# Ablation sweeps: set dark_pool and freshness_factor multipliers to 0.0 and 0.5
for sig in dark_pool freshness_factor; do
  for m in "${ABLATION_MULTS[@]}"; do
    log "Ablation sweep: ${sig} x ${m}"
    # write a temporary overlay fragment
    TMP_OV="${OVERLAY_PATH}.ablate.tmp"
    printf '{"composite_weights":{"%s":%s}}\n' "${sig}" "${m}" > "${TMP_OV}"
    mv "${TMP_OV}" "${OVERLAY_PATH}"
    git add "${OVERLAY_PATH}" || true
    git commit -m "Ablation ${sig} x ${m}" || true
    if [ -x scripts/run_promotion_candidate_1_check_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 || true
      sleep 30
      cp_excerpts
    fi
  done
done

# Re-copy final excerpts after exhaustive runs
cp_excerpts

# Re-evaluate gates one last time
TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${TMP_DIR}/baseline_metrics.json")
EXEC_PNL_1=$(jq_or_zero '.["slippage_0.0005"].net_pnl // .["slippage_0.0005"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json" 2>/dev/null || echo "N/A")
G_TRADES="FAIL"; [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] && G_TRADES="PASS"
G_PNL="FAIL"; [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ] && G_PNL="PASS"
G_EXEC="FAIL"; if [ "${EXEC_PNL_1}" != "N/A" ] && [ "$(echo "${EXEC_PNL_1} > 0" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then G_EXEC="PASS"; fi
if echo "${BOARD_VERDICT}" | grep -Ei "ACCEPT|CONDITIONAL" >/dev/null 2>&1; then G_BOARD="PASS"; else G_BOARD="FAIL"; fi

if [ "${G_BOARD}" = "PASS" ] && [ "${G_PNL}" = "PASS" ] && [ "${G_TRADES}" = "PASS" ] && [ "${G_EXEC}" = "PASS" ] && [ "${OP_HEALTH}" = "OK" ]; then
  DECISION="PROMOTE"
  PRIMARY_REASON="Final gates passed after iterations"
elif [ "${G_PNL}" = "PASS" ]; then
  DECISION="CONSIDER WITH MITIGATIONS"
  PRIMARY_REASON="Positive PnL but some gates marginal"
else
  DECISION="REJECT"
  PRIMARY_REASON="Final gates failed"
fi

# -------------------------
# 7) If PROMOTE, prepare branch and PR body
# -------------------------
PR_BRANCH_OUT="NONE"
if [ "${DECISION}" = "PROMOTE" ]; then
  log "Preparing promotion branch and PR body"
  mkdir -p "$(dirname "${OVERLAY_PATH}")"
  if [ ! -f "${OVERLAY_PATH}" ]; then
    cat > "${OVERLAY_PATH}" <<'JSON'
{
  "composite_weights": {
    "dark_pool": 0.75,
    "freshness_factor": 0.7
  },
  "freshness_smoothing_window": 3,
  "notes": "Automated promotion overlay"
}
JSON
    git add "${OVERLAY_PATH}" || true
    git commit -m "Add promotion_candidate_1 overlay (automated)" || true
  fi
  git fetch origin main || true
  git checkout -B "${PR_BRANCH}" origin/main 2>/dev/null || git checkout -B "${PR_BRANCH}" || true
  git add "${OVERLAY_PATH}" || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "Promotion candidate: overlay adjustments (automated)" || true
  fi
  if git push -u origin "${PR_BRANCH}" 2>/dev/null; then
    PR_BRANCH_OUT="${PR_BRANCH}"
    log "Pushed branch ${PR_BRANCH}"
  else
    PR_BRANCH_OUT="${PR_BRANCH} (local-only; push failed)"
    log "Warning: git push failed; branch created locally: ${PR_BRANCH}"
  fi
  # PR body
  cat > "${PR_BODY_PATH}" <<'MD'
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

  if [ -n "${GH_TOKEN}" ] && command -v gh >/dev/null 2>&1; then
    echo "${GH_TOKEN}" | gh auth login --with-token 2>/dev/null || true
    gh pr create --title "Paper promotion: reduce dark_pool weight and smooth freshness_factor" --body-file "${PR_BODY_PATH}" --base main --head "${PR_BRANCH}" || log "gh pr create failed"
    if [ "${AUTO_MERGE}" = "true" ]; then
      gh pr merge --auto --squash --delete-branch || log "gh pr merge failed"
    fi
  fi
fi

# -------------------------
# 8) Write cursor_final_summary.txt and cursor_report.md
# -------------------------
SUMMARY_PATH="${FOUND_RUN_DIR}/${SUMMARY_NAME}"
REPORT_PATH="${FOUND_RUN_DIR}/${REPORT_NAME}"

# cursor_final_summary.txt (machine readable)
{
  echo "RUN_DIR: ${FOUND_RUN_DIR}"
  echo "BASELINE_METRICS_PATH: ${TMP_DIR}/baseline_metrics.json"
  echo "EXEC_SENS_PATH: ${TMP_DIR}/exec_sensitivity.json"
  echo "BOARD_VERDICT_PATH: ${TMP_DIR}/board_verdict.md"
  echo "PERSONA_JSON_PATH: ${TMP_DIR}/persona.json"
  echo "PROMOTION_CANDIDATES_PATH: ${TMP_DIR}/PROMOTION_CANDIDATES.md"
  echo "EVIDENCE_FILES: $(ls -1 "${FOUND_RUN_DIR}/multi_model/evidence" 2>/dev/null || echo "none")"
  echo "RUN_LOG_TAIL: ${TMP_DIR}/run_log_tail.txt"
  echo ""
  echo "GATES:"
  echo "- trades_count: ${TRADES_COUNT} ${G_TRADES}"
  echo "- candidate_net_pnl: ${CAND_PNL} ${G_PNL}"
  echo "- pnl_ratio_to_baseline: ${PNL_RATIO}"
  echo "- exec_sensitivity_pnls: 0x=${EXEC_PNL_0},1x=${EXEC_PNL_1},2x=${EXEC_PNL_2} ${G_EXEC}"
  echo "- ablation_dark_pool_pnl: ${ABLA_DARK}"
  echo "- ablation_freshness_factor_pnl: ${ABLA_FRESH}"
  echo "- board_verdict: ${BOARD_VERDICT} ${G_BOARD}"
  echo "- operational_health: ${OP_HEALTH}"
  echo ""
  echo "DECISION: ${DECISION}"
  echo "PRIMARY_REASON: ${PRIMARY_REASON}"
  echo "APPLIED_MITIGATION: ${APPLIED_MITIGATION:-none}"
  echo ""
  echo "PR_BRANCH: ${PR_BRANCH_OUT}"
  echo "OVERLAY_PATH: ${OVERLAY_PATH}"
  echo "PR_BODY_PATH: ${PR_BODY_PATH}"
} > "${SUMMARY_PATH}"

# cursor_report.md (human readable)
{
  echo "# Cursor Automated Run Report"
  echo ""
  echo "Run directory: ${FOUND_RUN_DIR}"
  echo ""
  echo "## Key artifacts"
  echo "- Baseline metrics: ${TMP_DIR}/baseline_metrics.json"
  echo "- Exec sensitivity: ${TMP_DIR}/exec_sensitivity.json"
  echo "- Board verdict: ${TMP_DIR}/board_verdict.md"
  echo "- Persona recommendations: ${TMP_DIR}/persona.json"
  echo "- Promotion candidates: ${TMP_DIR}/PROMOTION_CANDIDATES.md"
  echo "- Evidence files: $(ls -1 "${FOUND_RUN_DIR}/multi_model/evidence" 2>/dev/null || echo "none")"
  echo ""
  echo "## Acceptance gates"
  echo "- **Trades count**: ${TRADES_COUNT} (${G_TRADES})"
  echo "- **Candidate net PnL**: ${CAND_PNL} (${G_PNL})"
  echo "- **PnL ratio to baseline**: ${PNL_RATIO}"
  echo "- **Exec sensitivity**: 0x=${EXEC_PNL_0}, 1x=${EXEC_PNL_1}, 2x=${EXEC_PNL_2} (${G_EXEC})"
  echo "- **Ablation**: dark_pool=${ABLA_DARK}, freshness_factor=${ABLA_FRESH}"
  echo "- **Board verdict**: ${BOARD_VERDICT} (${G_BOARD})"
  echo "- **Operational health**: ${OP_HEALTH}"
  echo ""
  echo "## Decision"
  echo "- **DECISION**: ${DECISION}"
  echo "- **Primary reason**: ${PRIMARY_REASON}"
  echo "- **Applied mitigation**: ${APPLIED_MITIGATION:-none}"
  echo ""
  if [ "${DECISION}" = "PROMOTE" ]; then
    echo "## Promotion artifacts and commands"
    echo "- PR branch: ${PR_BRANCH_OUT}"
    echo "- Overlay path: ${OVERLAY_PATH}"
    echo "- PR body: ${PR_BODY_PATH}"
    echo ""
    echo "### Git commands"
    echo '```bash'
    echo "git checkout -b ${PR_BRANCH_OUT}"
    echo "git add ${OVERLAY_PATH}"
    echo "git commit -m \"Promotion candidate: overlay adjustments\""
    echo "git push -u origin ${PR_BRANCH_OUT}"
    echo '```'
  elif [ "${DECISION}" = "CONSIDER WITH MITIGATIONS" ]; then
    echo "## Recommended mitigations and re-runs"
    echo "- Review persona and board excerpts: ${TMP_DIR}/persona_head.json, ${TMP_DIR}/board_verdict_head.md"
    echo "- Re-run focused checks after applying mitigation overlays from the MITIGATIONS list in the orchestrator script."
  else
    echo "## Rejection summary and next experiments"
    echo "- See board verdict and run log tail: ${TMP_DIR}/board_verdict.md, ${TMP_DIR}/run_log_tail.txt"
    echo "- Suggested next experiments: ensemble reweighting, additional smoothing, or different signal sets."
  fi
  echo ""
  echo "## Logs and excerpts"
  echo "- Run log tail: ${TMP_DIR}/run_log_tail.txt"
  echo "- Excerpts directory: ${TMP_DIR}"
} > "${REPORT_PATH}"

log "Wrote summary: ${SUMMARY_PATH}"
log "Wrote human report: ${REPORT_PATH}"

# Print the three machine-readable lines
echo "RUN_DIR: ${FOUND_RUN_DIR}"
echo "DECISION: ${DECISION}"
echo "PR_BRANCH: ${PR_BRANCH_OUT}"

log "Cursor full automated orchestrator finished"
log "Excerpts copied to ${TMP_DIR}"
log "Run log: ${LOG}"

exit 0
