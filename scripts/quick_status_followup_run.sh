#!/usr/bin/env bash
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

RUN_ID="followup_diag_20260222T225611Z"
RUN_DIR="reports/backtests/${RUN_ID}"
LOG="/tmp/followup_diag.log"

echo "=== Quick status for ${RUN_ID} ==="
echo "Run dir: ${RUN_DIR}"
echo ""

# 1. Tail orchestration log (last 200 lines)
echo "---- Orchestration log (last 200 lines) ----"
if [ -f "${LOG}" ]; then
  tail -n 200 "${LOG}"
else
  echo "Log ${LOG} not found"
fi
echo ""

# 2. FINAL_VERDICT
echo "---- FINAL_VERDICT ----"
if [ -f "${RUN_DIR}/FINAL_VERDICT.txt" ]; then
  cat "${RUN_DIR}/FINAL_VERDICT.txt"
else
  echo "FINAL_VERDICT.txt missing"
fi
echo ""

# 3. List top-level artifacts
echo "---- Top-level artifact list ----"
ls -la "${RUN_DIR}" 2>/dev/null || { echo "Run dir missing"; exit 1; }
echo ""

# 4. Check key artifact presence and print quick contents
check_and_print() {
  local path="$1"
  local label="$2"
  if [ -f "${path}" ]; then
    echo "+++ ${label}: ${path} (first 40 lines) +++"
    head -n 40 "${path}" || true
  elif [ -d "${path}" ]; then
    echo "+++ ${label}: ${path} (listing) +++"
    ls -la "${path}" | sed -n '1,40p' || true
  else
    echo "+++ ${label}: MISSING (${path}) +++"
  fi
  echo ""
}

# Baseline metrics
check_and_print "${RUN_DIR}/baseline/metrics.json" "Baseline metrics"

# Exec sensitivity summary (may be per-run subdirs)
if [ -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  check_and_print "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" "Exec sensitivity summary"
else
  echo "Exec sensitivity summary missing; listing exec_sensitivity dir:"
  ls -la "${RUN_DIR}/exec_sensitivity" 2>/dev/null || echo "exec_sensitivity dir missing"
  echo ""
fi

# Multi-model outputs
check_and_print "${RUN_DIR}/multi_model" "Multi-model outputs (dir)"

# Exit sweep summary
check_and_print "${RUN_DIR}/exit_sweep/exit_sweep_summary.json" "Exit sweep summary"

# Experiments compare summary
check_and_print "${RUN_DIR}/experiments/compare_summary.md" "Experiments compare summary"

# ARTIFACT_INDEX or ARTIFACT manifest
check_and_print "${RUN_DIR}/ARTIFACT_INDEX.md" "Artifact index"

# Attribution and ablation from base run (source of truth)
check_and_print "reports/backtests/alpaca_monday_final_20260222T174120Z/attribution/per_signal_pnl.json" "Base run per-signal attribution"
check_and_print "reports/backtests/alpaca_monday_final_20260222T174120Z/ablation/ablation_summary.json" "Base run ablation summary"

# 5. Summarize missing critical items and provide re-run commands
echo "---- Missing-critical-items and re-run commands ----"
MISSING=0

if [ ! -f "${RUN_DIR}/exec_sensitivity/exec_sensitivity.json" ]; then
  echo "Exec sensitivity summary missing."
  echo "Re-run exec sensitivity (sequential):"
  echo "python3 scripts/run_exec_sensitivity.py --bars ${RUN_DIR}/data_snapshot.txt --config configs/backtest_config.json --slippage-multipliers 0.0,1.0,2.0 --out ${RUN_DIR}/exec_sensitivity"
  MISSING=1
fi

if [ ! -d "${RUN_DIR}/multi_model" ] || [ -z "$(ls -A ${RUN_DIR}/multi_model 2>/dev/null || true)" ]; then
  echo "Multi-model outputs missing or empty."
  echo "Re-run multi-model with explicit out and evidence:"
  echo "python3 scripts/multi_model_runner.py --backtest_dir reports/backtests/alpaca_monday_final_20260222T174120Z --roles prosecutor,defender,sre,board --evidence reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence --out ${RUN_DIR}/multi_model/out"
  MISSING=1
fi

if [ ! -f "${RUN_DIR}/exit_sweep/exit_sweep_summary.json" ]; then
  echo "Exit sweep summary missing or stubbed."
  echo "Re-run exit sweep:"
  echo "python3 scripts/run_exit_optimization_on_droplet.py --bars ${RUN_DIR}/data_snapshot.txt --config configs/backtest_config.json --out ${RUN_DIR}/exit_sweep"
  MISSING=1
fi

if [ ! -f "${RUN_DIR}/experiments/compare_summary.md" ]; then
  echo "Experiments compare summary missing."
  echo "Check per-experiment metrics under ${RUN_DIR}/experiments/*/metrics.json and re-run compare generation if needed."
  MISSING=1
fi

if [ "${MISSING}" -eq 0 ]; then
  echo "All critical follow-up artifacts appear present (or partial outputs exist)."
else
  echo "One or more follow-up artifacts are missing. Use the commands above to re-run the specific steps."
fi
echo ""

# 6. Quick guidance: next immediate action
echo "---- Next immediate action ----"
echo "1) If exec_sensitivity timed out previously, run it sequentially (no wrapper timeout) as shown above."
echo "2) Re-run multi_model with --out to produce board verdicts and ensure evidence dir is passed."
echo "3) Run exit_sweep to get MFE/MAE and exit candidates."
echo "4) If experiments metrics are missing, re-run the specific experiment runs and then regenerate compare_summary.md."
echo ""
echo "When done, paste the top sections of the generated summary (baseline metrics, exec_sensitivity results, multi_model/board_verdict.md, exit_sweep_summary, experiments compare) here and I will synthesize the prioritized remediation and promotion plan."

exit 0
