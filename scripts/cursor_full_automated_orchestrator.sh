#!/usr/bin/env bash
# cursor_full_automated_orchestrator.sh
# Single-block Cursor-run: run massive scenarios, multi-model adversarial review,
# automated mitigations + re-checks, and prepare PR if accepted.
# Designed to run on the droplet for truth (MEMORY_BANK §0.1: droplet as source of truth).
#
# Usage (on droplet):
#   cd /root/stock-bot && MODE=droplet MIN_TRADES=100 bash scripts/cursor_full_automated_orchestrator.sh
# Or parallel: MODE=parallel WORKERS="w1 w2 w3" GH_TOKEN="..." MAX_ITER=3 MIN_TRADES=100 bash scripts/cursor_full_automated_orchestrator.sh
set -euo pipefail

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# -------------------------
# Config (edit as needed)
# -------------------------
MODE="${MODE:-local}"
WORKERS="${WORKERS:-}"
REMOTE_USER="${REMOTE_USER:-root}"
REPO_PATH="${REPO_PATH:-$(pwd)}"
PARALLEL_JOBS="${PARALLEL_JOBS:-6}"
GH_TOKEN="${GH_TOKEN:-}"
AUTO_MERGE="${AUTO_MERGE:-false}"
RUN_BASE="${RUN_BASE:-${REPO_PATH}/reports/backtests}"
TIMEOUT_MIN="${TIMEOUT_MIN:-240}"
POLL_SEC="${POLL_SEC:-20}"
MAX_ITER="${MAX_ITER:-3}"
MIN_TRADES="${MIN_TRADES:-100}"
OVERLAY_PATH="configs/overlays/promotion_candidate_1.json"
PR_BRANCH="promote/promotion_candidate_1"
PR_BODY_PATH="/tmp/promotion_candidate_1_PR_BODY.md"
LOG="/tmp/cursor_full_run.log"
SUMMARY_NAME="cursor_final_summary.txt"

# Automated mitigation candidates (applied in order)
MITIGATIONS=(
  '{"composite_weights":{"dark_pool":0.75,"freshness_factor":0.7},"freshness_smoothing_window":3}'
  '{"composite_weights":{"dark_pool":0.65,"freshness_factor":0.6},"freshness_smoothing_window":5}'
  '{"composite_weights":{"dark_pool":0.5,"freshness_factor":0.5},"freshness_smoothing_window":7}'
)

# -------------------------
# Helpers
# -------------------------
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail() { log "ERROR: $*"; exit 1; }

mkdir -p "$(dirname "${LOG}")"
: > "${LOG}"
cd "${REPO_PATH}" || fail "Repo path ${REPO_PATH} not found"

[ "${MODE}" = "parallel" ] && [ ! -f scripts/run_promotion_candidate_parallel_orchestrator.sh ] && fail "scripts/run_promotion_candidate_parallel_orchestrator.sh missing for MODE=parallel"
[ "${MODE}" = "local" ] && [ ! -x scripts/run_promotion_candidate_full_on_droplet.sh ] && fail "scripts/run_promotion_candidate_full_on_droplet.sh missing or not executable for MODE=local"
chmod +x scripts/*.sh 2>/dev/null || true

# Start orchestrator according to MODE
log "Starting orchestrator MODE=${MODE}"
case "${MODE}" in
  local)
    nohup bash scripts/run_promotion_candidate_full_on_droplet.sh >> "${LOG}" 2>&1 &
    ORCH_PID=$!
    ;;
  droplet)
    if [ -x scripts/run_promotion_candidate_full_oneshot_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_full_oneshot_on_droplet.sh >> "${LOG}" 2>&1 &
    elif [ -x scripts/run_promotion_candidate_1_single_run_on_droplet.sh ]; then
      nohup bash scripts/run_promotion_candidate_1_single_run_on_droplet.sh >> "${LOG}" 2>&1 &
    else
      fail "No droplet run script found"
    fi
    ORCH_PID=$!
    ;;
  parallel)
    if [ -z "${WORKERS}" ]; then fail "WORKERS must be set for parallel mode"; fi
    export WORKERS REMOTE_USER PARALLEL_JOBS GH_TOKEN AUTO_MERGE
    nohup bash scripts/run_promotion_candidate_parallel_orchestrator.sh >> "${LOG}" 2>&1 &
    ORCH_PID=$!
    ;;
  *)
    fail "Unknown MODE: ${MODE}"
    ;;
esac
log "Orchestrator started (PID ${ORCH_PID}); log -> ${LOG}"

tail -n 200 -f "${LOG}" & TAIL_PID=$!

END_TIME=$(( $(date +%s) + TIMEOUT_MIN*60 ))
FOUND_RUN_DIR=""
while [ "$(date +%s)" -lt "${END_TIME}" ]; do
  FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
  if [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ]; then
    if [ -f "${FOUND_RUN_DIR}/multi_model/out/board_verdict.md" ] && [ -f "${FOUND_RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
      log "Detected artifacts in ${FOUND_RUN_DIR}"
      break
    fi
  fi
  sleep "${POLL_SEC}"
done

kill "${TAIL_PID}" 2>/dev/null || true
wait "${TAIL_PID}" 2>/dev/null || true

if [ -z "${FOUND_RUN_DIR}" ] || [ ! -d "${FOUND_RUN_DIR}" ]; then
  log "No run directory found within ${TIMEOUT_MIN} minutes. Exiting."
  exit 2
fi

log "Run dir: ${FOUND_RUN_DIR}"

# -------------------------
# Collection helper
# -------------------------
TMP_DIR="/tmp/cursor_run_excerpts_$(date -u +%s)"
mkdir -p "${TMP_DIR}"
cp_excerpts() {
  local run_dir="${1:-${FOUND_RUN_DIR}}"
  if [ -f "${run_dir}/baseline/metrics.json" ]; then
    head -n 20 "${run_dir}/baseline/metrics.json" > "${TMP_DIR}/baseline_head.txt" 2>/dev/null || true
    cp "${run_dir}/baseline/metrics.json" "${TMP_DIR}/baseline_metrics.json" 2>/dev/null || true
  elif [ -f "${run_dir}/metrics.json" ]; then
    head -n 20 "${run_dir}/metrics.json" > "${TMP_DIR}/baseline_head.txt" 2>/dev/null || true
    cp "${run_dir}/metrics.json" "${TMP_DIR}/baseline_metrics.json" 2>/dev/null || true
  fi
  if [ -f "${run_dir}/exec_sensitivity/exec_sensitivity.json" ]; then
    cp "${run_dir}/exec_sensitivity/exec_sensitivity.json" "${TMP_DIR}/exec_sensitivity.json" 2>/dev/null || true
  elif [ -f "${run_dir}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
    cp "${run_dir}/exec_sensitivity/exec_sensitivity_recheck.json" "${TMP_DIR}/exec_sensitivity.json" 2>/dev/null || true
  fi
  if [ -f "${run_dir}/multi_model/out/board_verdict.md" ]; then
    head -n 40 "${run_dir}/multi_model/out/board_verdict.md" > "${TMP_DIR}/board_verdict_head.md" 2>/dev/null || true
    cp "${run_dir}/multi_model/out/board_verdict.md" "${TMP_DIR}/board_verdict.md" 2>/dev/null || true
  fi
  if [ -f "${run_dir}/multi_model/out/persona_recommendations.json" ]; then
    head -n 40 "${run_dir}/multi_model/out/persona_recommendations.json" > "${TMP_DIR}/persona_head.json" 2>/dev/null || true
    cp "${run_dir}/multi_model/out/persona_recommendations.json" "${TMP_DIR}/persona.json" 2>/dev/null || true
  fi
  if [ -f "${run_dir}/PROMOTION_CANDIDATES.md" ]; then
    head -n 40 "${run_dir}/PROMOTION_CANDIDATES.md" > "${TMP_DIR}/promotion_candidates_head.md" 2>/dev/null || true
    cp "${run_dir}/PROMOTION_CANDIDATES.md" "${TMP_DIR}/PROMOTION_CANDIDATES.md" 2>/dev/null || true
  fi
  tail -n 200 "${LOG}" > "${TMP_DIR}/run_log_tail.txt" 2>/dev/null || true
  if [ -d "${run_dir}/multi_model/evidence" ]; then
    ls -1 "${run_dir}/multi_model/evidence" > "${TMP_DIR}/evidence_listing.txt" 2>/dev/null || true
  fi
}
cp_excerpts

# -------------------------
# Gate parsing
# -------------------------
jq_or_zero() { jq -r "$1" "$2" 2>/dev/null || echo "0"; }

TRADES_COUNT=0
CAND_PNL=0
if [ -f "${TMP_DIR}/baseline_metrics.json" ]; then
  TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
  CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // .net_pnl_usd // 0' "${TMP_DIR}/baseline_metrics.json")
fi

EXEC_PNL_0="N/A"; EXEC_PNL_1="N/A"; EXEC_PNL_2="N/A"
if [ -f "${TMP_DIR}/exec_sensitivity.json" ]; then
  EXEC_PNL_0=$(jq_or_zero '.["slippage_0.0"].net_pnl // .["slippage_0.0"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
  EXEC_PNL_1=$(jq_or_zero '.["slippage_0.0005"].net_pnl // .["slippage_0.0005"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
  EXEC_PNL_2=$(jq_or_zero '.["slippage_0.001"].net_pnl // .["slippage_0.001"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
fi

BOARD_VERDICT="UNKNOWN"
if [ -f "${TMP_DIR}/board_verdict.md" ]; then
  BOARD_VERDICT=$(head -n 5 "${TMP_DIR}/board_verdict.md" | tr '\n' ' ' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')
fi

ABLA_DARK="N/A"; ABLA_FRESH="N/A"
DDIR=$(ls -d "${FOUND_RUN_DIR}"/sweep_dark_pool_x_* 2>/dev/null | head -n1 || true)
if [ -n "${DDIR}" ] && [ -f "${DDIR}/metrics.json" ]; then
  ABLA_DARK=$(jq_or_zero '.net_pnl // .netPnL // 0' "${DDIR}/metrics.json")
fi
FDIR=$(ls -d "${FOUND_RUN_DIR}"/sweep_freshness_factor_x_* 2>/dev/null | head -n1 || true)
if [ -n "${FDIR}" ] && [ -f "${FDIR}/metrics.json" ]; then
  ABLA_FRESH=$(jq_or_zero '.net_pnl // .netPnL // 0' "${FDIR}/metrics.json")
fi

OP_HEALTH="OK"
if [ -f "${TMP_DIR}/run_log_tail.txt" ] && grep -Ei "ERROR|failed|FAIL|exception|OOM|out of memory|swap" "${TMP_DIR}/run_log_tail.txt" >/dev/null 2>&1; then
  OP_HEALTH="ISSUES: check run log"
fi

PNL_RATIO="N/A"
if [ -n "${BASELINE_METRICS_PATH:-}" ] && [ -f "${BASELINE_METRICS_PATH}" ]; then
  BASE_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${BASELINE_METRICS_PATH}")
  if command -v bc >/dev/null 2>&1 && [ "$(echo "${BASE_PNL} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    PNL_RATIO=$(awk "BEGIN{printf \"%.3f\", (${CAND_PNL}/${BASE_PNL})}" 2>/dev/null || echo "N/A")
  fi
fi

G_TRADES="FAIL"; [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] 2>/dev/null && G_TRADES="PASS"
G_PNL="FAIL"; [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ] && G_PNL="PASS"
G_EXEC="FAIL"
if [ "${EXEC_PNL_1}" != "N/A" ] && [ "$(echo "${EXEC_PNL_1} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then G_EXEC="PASS"; fi
G_BOARD="FAIL"
echo "${BOARD_VERDICT}" | grep -Ei "ACCEPT|CONDITIONAL" >/dev/null 2>&1 && G_BOARD="PASS"

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
# Automated mitigations loop
# -------------------------
ITER=0
APPLIED_MITIGATION=""
while [ "${DECISION}" != "PROMOTE" ] && [ "${ITER}" -lt "${MAX_ITER}" ]; do
  MIT="${MITIGATIONS[ITER]:-}"
  if [ -z "${MIT}" ]; then
    log "No more automated mitigations configured"
    break
  fi
  ITER=$((ITER+1))
  log "Attempting automated mitigation #${ITER}: merging overlay fragment"
  mkdir -p "${REPO_PATH}/$(dirname "${OVERLAY_PATH}")"
  if [ -f "${REPO_PATH}/${OVERLAY_PATH}" ]; then
    cp "${REPO_PATH}/${OVERLAY_PATH}" "${REPO_PATH}/${OVERLAY_PATH}.bak.${TIMESTAMP}" 2>/dev/null || true
  fi
  printf '%s' "${MIT}" > "${REPO_PATH}/${OVERLAY_PATH}"
  git add "${OVERLAY_PATH}" 2>/dev/null || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "Automated mitigation ${ITER}: apply overlay tweak for promotion_candidate_1" || true
  fi
  log "Re-running focused checks (single-run) after mitigation ${ITER}"
  nohup bash scripts/run_promotion_candidate_1_check_on_droplet.sh >> "${LOG}" 2>&1 &
  sleep 120
  FOUND_RUN_DIR="${RUN_BASE}/promotion_candidate_1_check"
  if [ ! -d "${FOUND_RUN_DIR}" ]; then
    FOUND_RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_* 2>/dev/null | head -n1 || true)
  fi
  [ -n "${FOUND_RUN_DIR}" ] && [ -d "${FOUND_RUN_DIR}" ] && cp_excerpts "${FOUND_RUN_DIR}"
  if [ -f "${TMP_DIR}/baseline_metrics.json" ]; then
    TRADES_COUNT=$(jq_or_zero '.trades_count // .trades // 0' "${TMP_DIR}/baseline_metrics.json")
    CAND_PNL=$(jq_or_zero '.net_pnl // .netPnL // 0' "${TMP_DIR}/baseline_metrics.json")
  fi
  if [ -f "${TMP_DIR}/exec_sensitivity.json" ]; then
    EXEC_PNL_1=$(jq_or_zero '.["slippage_0.0005"].net_pnl // .["slippage_0.0005"].netPnL // 0' "${TMP_DIR}/exec_sensitivity.json")
  fi
  if [ -f "${TMP_DIR}/board_verdict.md" ]; then
    BOARD_VERDICT=$(head -n 5 "${TMP_DIR}/board_verdict.md" | tr '\n' ' ' | sed 's/  */ /g')
    G_BOARD="FAIL"
    echo "${BOARD_VERDICT}" | grep -Ei "ACCEPT|CONDITIONAL" >/dev/null 2>&1 && G_BOARD="PASS"
  fi
  G_TRADES="FAIL"; [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] 2>/dev/null && G_TRADES="PASS"
  G_PNL="FAIL"; [ "$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ] && G_PNL="PASS"
  G_EXEC="FAIL"
  if [ "${EXEC_PNL_1}" != "N/A" ] && [ "$(echo "${EXEC_PNL_1} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then G_EXEC="PASS"; fi
  if [ "${G_BOARD}" = "PASS" ] && [ "${G_PNL}" = "PASS" ] && [ "${G_TRADES}" = "PASS" ] && [ "${G_EXEC}" = "PASS" ] && [ "${OP_HEALTH}" = "OK" ]; then
    DECISION="PROMOTE"
    PRIMARY_REASON="Automated mitigation ${ITER} succeeded"
    APPLIED_MITIGATION="mitigation_${ITER}"
    break
  else
    log "Mitigation ${ITER} did not satisfy gates; continuing"
  fi
done

# -------------------------
# If PROMOTE, prepare PR
# -------------------------
PR_BRANCH_OUT="NONE"
if [ "${DECISION}" = "PROMOTE" ]; then
  log "Decision PROMOTE — preparing branch and PR body"
  if [ ! -f "${REPO_PATH}/${OVERLAY_PATH}" ]; then
    mkdir -p "${REPO_PATH}/$(dirname "${OVERLAY_PATH}")"
    cat > "${REPO_PATH}/${OVERLAY_PATH}" <<'JSON'
{
  "composite_weights": {
    "dark_pool": 0.75,
    "freshness_factor": 0.7
  },
  "freshness_smoothing_window": 3,
  "notes": "Automated promotion candidate overlay"
}
JSON
    git add "${OVERLAY_PATH}" 2>/dev/null || true
    git commit -m "Add promotion_candidate_1 overlay (automated)" || true
  fi
  git fetch origin main 2>/dev/null || true
  git checkout -B "${PR_BRANCH}" origin/main 2>/dev/null || git checkout -B "${PR_BRANCH}" || true
  git add "${OVERLAY_PATH}" 2>/dev/null || true
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
    gh pr create --title "Paper promotion: reduce dark_pool weight and smooth freshness_factor" --body-file "${PR_BODY_PATH}" --base main --head "${PR_BRANCH}" 2>/dev/null || log "gh pr create failed"
    if [ "${AUTO_MERGE}" = "true" ]; then
      gh pr merge --auto --squash --delete-branch 2>/dev/null || log "gh pr merge failed"
    fi
  fi
fi

# -------------------------
# PNL_RATIO gate (for summary)
# -------------------------
PNL_RATIO_GATE="N/A"
if [ "${PNL_RATIO}" != "N/A" ] && command -v bc >/dev/null 2>&1; then
  [ "$(echo "${PNL_RATIO} >= 0.90" | bc -l 2>/dev/null || echo 0)" = "1" ] && PNL_RATIO_GATE="PASS" || PNL_RATIO_GATE="FAIL"
fi

# -------------------------
# Write cursor_final_summary.txt
# -------------------------
SUMMARY_PATH="${FOUND_RUN_DIR}/${SUMMARY_NAME}"
EVIDENCE_LISTING="none"
[ -d "${FOUND_RUN_DIR}/multi_model/evidence" ] && EVIDENCE_LISTING=$(ls -1 "${FOUND_RUN_DIR}/multi_model/evidence" 2>/dev/null | tr '\n' ' ' || echo "none")

{
  echo "RUN_DIR: ${FOUND_RUN_DIR}"
  echo "BASELINE_METRICS_PATH: ${TMP_DIR}/baseline_metrics.json"
  echo "EXEC_SENS_PATH: ${TMP_DIR}/exec_sensitivity.json"
  echo "BOARD_VERDICT_PATH: ${TMP_DIR}/board_verdict.md"
  echo "PERSONA_JSON_PATH: ${TMP_DIR}/persona.json"
  echo "PROMOTION_CANDIDATES_PATH: ${TMP_DIR}/PROMOTION_CANDIDATES.md"
  echo "EVIDENCE_FILES: ${EVIDENCE_LISTING}"
  echo "RUN_LOG_TAIL: ${TMP_DIR}/run_log_tail.txt"
  echo ""
  echo "GATES:"
  echo "- trades_count: ${TRADES_COUNT} ${G_TRADES}"
  echo "- candidate_net_pnl: ${CAND_PNL} ${G_PNL}"
  echo "- pnl_ratio_to_baseline: ${PNL_RATIO} ${PNL_RATIO_GATE}"
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
  echo ""
  echo "If PROMOTE:"
  echo "  git checkout -b ${PR_BRANCH}"
  echo "  git add ${OVERLAY_PATH}"
  echo "  git commit -m \"Promotion candidate: overlay adjustments\""
  echo "  git push -u origin ${PR_BRANCH}"
  echo "  # then create PR with gh or GitHub UI using ${PR_BODY_PATH}"
  echo ""
  echo "If CONSIDER WITH MITIGATIONS:"
  echo "  Review ${TMP_DIR}/promotion_candidates_head.md and ${TMP_DIR}/persona_head.json for required mitigations."
  echo ""
  echo "If REJECT:"
  echo "  See ${TMP_DIR}/board_verdict.md and ${TMP_DIR}/run_log_tail.txt for failure reasons and next experiments."
} > "${SUMMARY_PATH}"

log "Wrote final summary to ${SUMMARY_PATH}"
echo "RUN_DIR: ${FOUND_RUN_DIR}"
echo "DECISION: ${DECISION}"
echo "PR_BRANCH: ${PR_BRANCH_OUT}"

log "Cursor full orchestrator finished. Summary: ${SUMMARY_PATH}"
log "Excerpts: ${TMP_DIR}"
log "Run log: ${LOG}"
exit 0
