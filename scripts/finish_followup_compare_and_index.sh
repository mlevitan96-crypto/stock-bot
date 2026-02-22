#!/usr/bin/env bash
# Generate compare_summary.md and ARTIFACT_INDEX.md for an existing followup run.
# Usage: RUN_ID=followup_diag_20260222T225611Z bash scripts/finish_followup_compare_and_index.sh
# Or:   bash scripts/finish_followup_compare_and_index.sh followup_diag_20260222T225611Z
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

RUN_ID="${1:-${RUN_ID:-}}"
if [ -z "${RUN_ID}" ]; then
  echo "Usage: RUN_ID=... bash $0   OR   bash $0 <RUN_ID>"
  exit 1
fi

BASE_RUN="${BASE_RUN:-alpaca_monday_final_20260222T174120Z}"
OUTDIR="reports/backtests/${RUN_ID}"
EXPERIMENTS=(tune_dark_pool_minus25 tune_freshness_smooth tune_exit_trail)

if [ ! -d "${OUTDIR}" ]; then
  echo "Run dir not found: ${OUTDIR}"
  exit 1
fi

# Compare summary
CMP="${OUTDIR}/experiments/compare_summary.md"
mkdir -p "${OUTDIR}/experiments"
echo "# Quick experiment comparison for ${RUN_ID}" > "${CMP}"
echo "" >> "${CMP}"
BASE_MET="reports/backtests/${BASE_RUN}/baseline/metrics.json"
if [ -f "${BASE_MET}" ]; then
  echo "## Baseline (${BASE_RUN})" >> "${CMP}"
  jq '{net_pnl, trades_count, win_rate_pct}' "${BASE_MET}" >> "${CMP}" 2>/dev/null || cat "${BASE_MET}" >> "${CMP}"
else
  echo "Baseline metrics not found for ${BASE_RUN}" >> "${CMP}"
fi
for e in "${EXPERIMENTS[@]}"; do
  EMET="${OUTDIR}/experiments/${e}/metrics.json"
  echo "" >> "${CMP}"
  echo "## Experiment ${e}" >> "${CMP}"
  if [ -f "${EMET}" ]; then
    jq '{net_pnl, trades_count, win_rate_pct}' "${EMET}" >> "${CMP}" 2>/dev/null || cat "${EMET}" >> "${CMP}"
  else
    echo "metrics.json missing for ${e}" >> "${CMP}"
  fi
done
echo "Wrote ${CMP}"

# Artifact index
INDEX="${OUTDIR}/ARTIFACT_INDEX.md"
echo "# Artifact index for ${RUN_ID}" > "${INDEX}"
echo "" >> "${INDEX}"
echo "Base run: reports/backtests/${BASE_RUN}" >> "${INDEX}"
echo "Follow-up dir: ${OUTDIR}" >> "${INDEX}"
echo "" >> "${INDEX}"
echo "| Artifact | Path |" >> "${INDEX}"
echo "|----------|------|" >> "${INDEX}"
echo "| Exec sensitivity | ${OUTDIR}/exec_sensitivity/exec_sensitivity.json |" >> "${INDEX}"
echo "| Multi-model | ${OUTDIR}/multi_model/ (board_verdict.md, board_verdict.json) |" >> "${INDEX}"
echo "| Exit sweep | ${OUTDIR}/exit_sweep/exit_sweep_summary.json |" >> "${INDEX}"
echo "| Experiments compare | ${OUTDIR}/experiments/compare_summary.md |" >> "${INDEX}"
echo "| Base attribution | reports/backtests/${BASE_RUN}/attribution/per_signal_pnl.json |" >> "${INDEX}"
echo "| Base ablation | reports/backtests/${BASE_RUN}/ablation/ablation_summary.json |" >> "${INDEX}"
echo "| Base metrics | reports/backtests/${BASE_RUN}/baseline/metrics.json |" >> "${INDEX}"
echo "" >> "${INDEX}"
echo "Tail of /tmp/followup_diag.log (last 50 lines):" >> "${INDEX}"
tail -n 50 /tmp/followup_diag.log >> "${INDEX}" 2>/dev/null || echo "(log not found)" >> "${INDEX}"
echo "Wrote ${INDEX}"
exit 0
