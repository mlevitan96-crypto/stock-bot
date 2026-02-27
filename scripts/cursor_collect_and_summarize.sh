#!/usr/bin/env bash
# cursor_collect_and_summarize.sh
# After the orchestrator completes: collect excerpts to /tmp, parse artifacts,
# and write a structured cursor_final_summary.txt for Cursor/governance.
#
# Typical flow:
#   1) Start orchestrator: MODE=parallel WORKERS="w1 w2" GH_TOKEN="..." bash scripts/cursor_run_and_review.sh
#   2) Wait for completion (or use cursor_launch_and_request_review.sh which does wait + excerpts).
#   3) Collect and summarize: bash scripts/cursor_collect_and_summarize.sh [RUN_DIR]
#
# Usage:
#   bash scripts/cursor_collect_and_summarize.sh [RUN_DIR]
#   If RUN_DIR is omitted, uses the latest reports/backtests/promotion_candidate_*
#
# Optional: BASELINE_METRICS_PATH=/path/to/previous/baseline/metrics.json for pnl_ratio gate.
# Optional: MIN_TRADES=100 to override default 30.
set -euo pipefail

REPO_PATH="${REPO_PATH:-$(pwd)}"
RUN_BASE="${RUN_BASE:-${REPO_PATH}/reports/backtests}"

if [ -n "${1:-}" ]; then
  RUN_DIR="$1"
else
  RUN_DIR=$(ls -td "${RUN_BASE}"/promotion_candidate_full_* "${RUN_BASE}"/promotion_candidate_parallel_* "${RUN_BASE}"/promotion_candidate_run_* "${RUN_BASE}"/promotion_candidate_1_check 2>/dev/null | head -n1 || true)
fi

if [ -z "${RUN_DIR}" ] || [ ! -d "${RUN_DIR}" ]; then
  echo "No run directory found. Specify RUN_DIR or ensure ${RUN_BASE}/promotion_candidate_* exists."
  exit 1
fi

# Resolve to absolute path
RUN_DIR=$(cd "${RUN_DIR}" && pwd)
OVERLAY="configs/overlays/promotion_candidate_1.json"

# -------------------------
# 1) Collect excerpts to /tmp
# -------------------------
if [ -f "${RUN_DIR}/baseline/metrics.json" ]; then
  head -n 20 "${RUN_DIR}/baseline/metrics.json" > /tmp/baseline_head.txt
elif [ -f "${RUN_DIR}/metrics.json" ]; then
  head -n 20 "${RUN_DIR}/metrics.json" > /tmp/baseline_head.txt
else
  echo "metrics.json not found" > /tmp/baseline_head.txt
fi

if [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  jq '.' "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" 2>/dev/null > /tmp/exec_sens.json || cp "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" /tmp/exec_sens.json
elif [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
  jq '.' "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" 2>/dev/null > /tmp/exec_sens.json || cp "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" /tmp/exec_sens.json
else
  echo "{}" > /tmp/exec_sens.json
fi

if [ -f "${RUN_DIR}/multi_model/out/board_verdict.md" ]; then
  head -n 40 "${RUN_DIR}/multi_model/out/board_verdict.md" > /tmp/board_verdict_head.md
else
  echo "board_verdict.md not found" > /tmp/board_verdict_head.md
fi

if [ -f "${RUN_DIR}/multi_model/out/persona_recommendations.json" ]; then
  head -n 40 "${RUN_DIR}/multi_model/out/persona_recommendations.json" > /tmp/persona_head.json
else
  echo "[]" > /tmp/persona_head.json
fi

if [ -f "${RUN_DIR}/PROMOTION_CANDIDATES.md" ]; then
  head -n 40 "${RUN_DIR}/PROMOTION_CANDIDATES.md" > /tmp/promotion_candidates_head.md
else
  echo "PROMOTION_CANDIDATES.md not found" > /tmp/promotion_candidates_head.md
fi

tail -n 200 /tmp/cursor_orchestrator_run.log 2>/dev/null > /tmp/run_log_tail.txt || echo "Log not found" > /tmp/run_log_tail.txt

# -------------------------
# 2) Parse acceptance gates
# -------------------------
MET="${RUN_DIR}/baseline/metrics.json"
[ ! -f "${MET}" ] && MET="${RUN_DIR}/metrics.json"

TRADES_COUNT="N/A"
CANDIDATE_NET_PNL="N/A"
if [ -f "${MET}" ]; then
  TRADES_COUNT=$(jq -r '.trades_count // .trades // "N/A"' "${MET}" 2>/dev/null || echo "N/A")
  CANDIDATE_NET_PNL=$(jq -r '.net_pnl // .netPnL // .netPnLUsd // .net_pnl_usd // "N/A"' "${MET}" 2>/dev/null || echo "N/A")
fi

MIN_TRADES="${MIN_TRADES:-30}"
TRADES_PASS="FAIL"
if [ "${TRADES_COUNT}" != "N/A" ] && [ "${TRADES_COUNT}" -ge "${MIN_TRADES}" ] 2>/dev/null; then
  TRADES_PASS="PASS"
fi

PNL_PASS="FAIL"
if [ "${CANDIDATE_NET_PNL}" != "N/A" ]; then
  if command -v bc >/dev/null 2>&1; then
    if [ "$(echo "${CANDIDATE_NET_PNL} > 0" | bc -l 2>/dev/null)" = "1" ]; then PNL_PASS="PASS"; fi
  else
    case "${CANDIDATE_NET_PNL}" in 0|0.0|0.00) ;; *) PNL_PASS="PASS"; ;; esac
  fi
fi

PNL_RATIO="N/A"
PNL_RATIO_PASS="N/A"
# Optional: compare to a previous baseline path if provided
if [ -n "${BASELINE_METRICS_PATH:-}" ] && [ -f "${BASELINE_METRICS_PATH}" ] && [ -f "${MET}" ]; then
  BASE_PNL=$(jq -r '.net_pnl // .netPnL // .net_pnl_usd // 0' "${BASELINE_METRICS_PATH}" 2>/dev/null || echo "0")
  CAND_PNL_NUM=$(jq -r '.net_pnl // .netPnL // .net_pnl_usd // 0' "${MET}" 2>/dev/null || echo "0")
  if command -v bc >/dev/null 2>&1 && [ "${BASE_PNL}" != "0" ]; then
    PNL_RATIO=$(echo "scale=4; ${CAND_PNL_NUM} / ${BASE_PNL}" | bc 2>/dev/null || echo "N/A")
    if [ "${PNL_RATIO}" != "N/A" ] && [ "$(echo "${PNL_RATIO} >= 0.90" | bc -l 2>/dev/null)" = "1" ]; then PNL_RATIO_PASS="PASS"; else PNL_RATIO_PASS="FAIL"; fi
  fi
fi

# Exec sensitivity: 0x, 1x, 2x PnLs
ES_0x="N/A"; ES_1x="N/A"; ES_2x="N/A"; ES_PASS="N/A"
if [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ] || [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json" ]; then
  ES_FILE="${RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
  [ ! -f "${ES_FILE}" ] && ES_FILE="${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json"
  ES_0x=$(jq -r '.["slippage_0"] // .["slippage_0.0"] | .net_pnl // .netPnL // "N/A"' "${ES_FILE}" 2>/dev/null || echo "N/A")
  ES_1x=$(jq -r '.["slippage_0.0005"] | .net_pnl // .netPnL // "N/A"' "${ES_FILE}" 2>/dev/null || echo "N/A")
  ES_2x=$(jq -r '.["slippage_0.001"] // .["slippage_0.002"] | .net_pnl // .netPnL // "N/A"' "${ES_FILE}" 2>/dev/null || echo "N/A")
  ES_PASS="PASS"
  for v in "${ES_0x}" "${ES_1x}" "${ES_2x}"; do
    if [ "${v}" = "N/A" ] || [ "${v}" = "null" ]; then ES_PASS="N/A"; break; fi
    if command -v bc >/dev/null 2>&1 && [ "$(echo "${v} < 0" | bc -l 2>/dev/null)" = "1" ]; then ES_PASS="FAIL"; break; fi
  done
fi

# Ablation PnLs (sweep dirs)
ABL_DP="N/A"; ABL_FF="N/A"
for d in "${RUN_DIR}"/sweep_dark_pool_x_*; do
  [ -d "${d}" ] && [ -f "${d}/metrics.json" ] && ABL_DP=$(jq -r '.net_pnl // .netPnL // "N/A"' "${d}/metrics.json" 2>/dev/null) && break
done
for d in "${RUN_DIR}"/sweep_freshness_factor_x_*; do
  [ -d "${d}" ] && [ -f "${d}/metrics.json" ] && ABL_FF=$(jq -r '.net_pnl // .netPnL // "N/A"' "${d}/metrics.json" 2>/dev/null) && break
done

# Board verdict
BOARD_VERDICT="N/A"
BOARD_PASS="FAIL"
if [ -f "${RUN_DIR}/multi_model/out/board_verdict.md" ]; then
  if grep -qi "ACCEPT" "${RUN_DIR}/multi_model/out/board_verdict.md" 2>/dev/null; then
    BOARD_VERDICT="ACCEPT"; BOARD_PASS="PASS"
  elif grep -qi "CONDITIONAL" "${RUN_DIR}/multi_model/out/board_verdict.md" 2>/dev/null; then
    BOARD_VERDICT="CONDITIONAL"; BOARD_PASS="CONSIDER"
  elif grep -qi "REJECT" "${RUN_DIR}/multi_model/out/board_verdict.md" 2>/dev/null; then
    BOARD_VERDICT="REJECT"
  fi
fi

# Operational health: check log for errors
OPERATIONAL_HEALTH="OK"
if [ -f /tmp/cursor_orchestrator_run.log ]; then
  if grep -qi "ERROR\|failed\|FAIL\|exception" /tmp/cursor_orchestrator_run.log 2>/dev/null; then
    OPERATIONAL_HEALTH="Check log for errors/exceptions"
  fi
fi

# -------------------------
# 3) Overall decision
# -------------------------
OVERALL="REJECT"
PRIMARY_REASON="Insufficient data or gates not met."

if [ "${BOARD_PASS}" = "PASS" ] && [ "${TRADES_PASS}" = "PASS" ] && [ "${PNL_PASS}" = "PASS" ]; then
  OVERALL="PROMOTE"
  PRIMARY_REASON="Board ACCEPT, sufficient trades, positive candidate PnL."
elif [ "${BOARD_PASS}" = "CONSIDER" ] || [ "${BOARD_VERDICT}" = "CONDITIONAL" ]; then
  OVERALL="CONSIDER WITH MITIGATIONS"
  PRIMARY_REASON="Board conditional; apply mitigations and re-validate before promotion."
elif [ "${BOARD_VERDICT}" = "REJECT" ]; then
  OVERALL="REJECT"
  PRIMARY_REASON="Board verdict REJECT."
else
  if [ "${TRADES_PASS}" = "FAIL" ]; then PRIMARY_REASON="Trades count below threshold (${MIN_TRADES})."; fi
  if [ "${PNL_PASS}" = "FAIL" ] && [ "${CANDIDATE_NET_PNL}" != "N/A" ]; then PRIMARY_REASON="Candidate net PnL not positive."; fi
fi

# Evidence listing
EVIDENCE_LIST=""
if [ -d "${RUN_DIR}/multi_model/evidence" ]; then
  EVIDENCE_LIST=$(ls -1 "${RUN_DIR}/multi_model/evidence" 2>/dev/null | tr '\n' ' ' || echo "(none)")
fi

# -------------------------
# 4) Write cursor_final_summary.txt
# -------------------------
SUMMARY_FILE="${RUN_DIR}/cursor_final_summary.txt"
{
  echo "Run directory: ${RUN_DIR}"
  echo "Baseline metrics excerpt: /tmp/baseline_head.txt"
  echo "Exec sensitivity excerpt: /tmp/exec_sens.json"
  echo "Board verdict excerpt: /tmp/board_verdict_head.md"
  echo "Persona JSON excerpt: /tmp/persona_head.json"
  echo "Promotion candidates excerpt: /tmp/promotion_candidates_head.md"
  echo "Run log tail: /tmp/run_log_tail.txt"
  echo "Evidence files: ${EVIDENCE_LIST}"
  echo "Review bundle: ${RUN_DIR}/cursor_review_bundle.txt"
  echo ""
  echo "Acceptance gates:"
  echo "- trades_count: ${TRADES_COUNT}  ${TRADES_PASS}"
  echo "- candidate_net_pnl: ${CANDIDATE_NET_PNL}  ${PNL_PASS}"
  echo "- pnl_ratio_to_baseline: ${PNL_RATIO}  ${PNL_RATIO_PASS}"
  echo "- exec_sensitivity_pnls: 0x=${ES_0x}, 1x=${ES_1x}, 2x=${ES_2x}  ${ES_PASS}"
  echo "- ablation_dark_pool_pnl: ${ABL_DP}  (informational)"
  echo "- ablation_freshness_factor_pnl: ${ABL_FF}  (informational)"
  echo "- board_verdict: ${BOARD_VERDICT}  ${BOARD_PASS}"
  echo "- operational_health: ${OPERATIONAL_HEALTH}"
  echo ""
  echo "Overall decision: ${OVERALL}"
  echo "Primary reason: ${PRIMARY_REASON}"
  echo ""
  if [ "${OVERALL}" = "PROMOTE" ]; then
    echo "If PROMOTE:"
    echo "- Branch: promote/promotion_candidate_1"
    echo "- Overlay path: ${OVERLAY}"
    echo "- PR body path: ${RUN_DIR}/PR_BODY.md"
    echo "- Git commands to run:"
    echo "  git checkout -b promote/promotion_candidate_1"
    echo "  git add ${OVERLAY}"
    echo "  git commit -m \"Promotion candidate: reduce dark_pool and smooth freshness_factor (promotion_candidate_1)\""
    echo "  git push -u origin promote/promotion_candidate_1"
    echo "  gh pr create --title \"Paper promotion: reduce dark_pool weight and smooth freshness_factor\" --body-file ${RUN_DIR}/PR_BODY.md"
  fi
  if [ "${OVERALL}" = "CONSIDER WITH MITIGATIONS" ]; then
    echo "If CONSIDER WITH MITIGATIONS:"
    echo "- List required mitigations from board_verdict.md and persona_recommendations.json."
    echo "- Re-run focused checks after mitigations; then re-run this summary."
  fi
  if [ "${OVERALL}" = "REJECT" ]; then
    echo "If REJECT:"
    echo "- Review board_verdict.md and persona recommendations for reasons."
    echo "- Suggested next experiments: adjust overlay weights, re-run exec sensitivity and sweeps, then re-run full promotion flow."
  fi
} > "${SUMMARY_FILE}"

echo "Wrote ${SUMMARY_FILE}"
echo "Excerpts: /tmp/baseline_head.txt /tmp/exec_sens.json /tmp/board_verdict_head.md /tmp/persona_head.json /tmp/promotion_candidates_head.md /tmp/run_log_tail.txt"
echo "Overall decision: ${OVERALL}"
