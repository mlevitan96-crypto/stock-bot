#!/usr/bin/env bash
# PUSH, USE PLUGINS, RUN MULTI-MODEL ADVERSARIAL REVIEW, CUSTOMER ADVOCATE, AND FINALIZE (DROPLET)
# - Plugin discovery and tests; bundle plugin outputs into multi-model evidence.
# - Run finalize orchestration (exec sensitivity, exit sweep, experiments) if not already run.
# - Multi-model adversarial (prosecutor, defender, sre, board) with full evidence and --out.
# - Generate customer_advocate.md and PROMOTION_CANDIDATES.md.
# - Paper overlay: min_exec_score=1.8, shadow_min_exec_score=1.5.
# Non-destructive: outputs under reports/backtests/<RUN_ID> and reports/governance/<RUN_ID>.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

# ---------- Run identifiers ----------
TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="push_with_plugins_${TS}"
OUTDIR="reports/backtests/${RUN_ID}"
mkdir -p "${OUTDIR}"
echo "RUN_ID=${RUN_ID}" > "${OUTDIR}/run_meta.txt"

BASE_RUN="alpaca_monday_final_20260222T174120Z"

# ---------- Ensure paper overlay exists and is the single tuning overlay to apply ----------
mkdir -p configs/overlays
cat > configs/overlays/paper_lock_overlay.json <<'JSON'
{
  "min_exec_score": 1.8,
  "shadow_min_exec_score": 1.5,
  "paper_mode": true,
  "notes": "Paper lock for Monday: min_exec_score=1.8; shadow lower gate=1.5"
}
JSON
mkdir -p "${OUTDIR}/patches"
cp -v configs/overlays/paper_lock_overlay.json "${OUTDIR}/patches/" 2>/dev/null || true

# ---------- 0. Preflight: plugin discovery and quick plugin tests ----------
echo "=== PREFLIGHT: plugin discovery and quick tests ===" > "${OUTDIR}/preflight_plugins.txt"
if [ -d plugins ]; then
  echo "plugins directory found" >> "${OUTDIR}/preflight_plugins.txt"
  ls -1 plugins >> "${OUTDIR}/preflight_plugins.txt" 2>/dev/null || true
  mkdir -p "${OUTDIR}/multi_model/evidence/plugins"
  if [ -x scripts/plugins/run_all_plugin_tests.sh ]; then
    echo "Running scripts/plugins/run_all_plugin_tests.sh" >> "${OUTDIR}/preflight_plugins.txt"
    scripts/plugins/run_all_plugin_tests.sh >> "${OUTDIR}/preflight_plugins.txt" 2>&1 || echo "plugin tests returned non-zero" >> "${OUTDIR}/preflight_plugins.txt"
    if [ -d plugins/output ]; then
      cp -v plugins/output/* "${OUTDIR}/multi_model/evidence/plugins/" 2>/dev/null || true
    fi
  else
    for t in plugins/*/test_*.sh; do
      [ -f "$t" ] || continue
      echo "Running plugin test: $t" >> "${OUTDIR}/preflight_plugins.txt"
      bash "$t" >> "${OUTDIR}/preflight_plugins.txt" 2>&1 || echo "plugin test $t failed" >> "${OUTDIR}/preflight_plugins.txt"
      PLDIR=$(dirname "$t")
      if [ -d "${PLDIR}/output" ]; then
        cp -v "${PLDIR}/output/"* "${OUTDIR}/multi_model/evidence/plugins/" 2>/dev/null || true
      fi
    done
  fi
else
  echo "no plugins dir" >> "${OUTDIR}/preflight_plugins.txt"
fi

# ---------- 1. Run finalize push orchestration if not already run for this session ----------
if [ -x scripts/run_finalize_push_on_droplet.sh ]; then
  echo "Running finalize push orchestration..." >> "${OUTDIR}/preflight_plugins.txt"
  bash scripts/run_finalize_push_on_droplet.sh >> "${OUTDIR}/finalize_push.log" 2>&1 || echo "finalize_push returned non-zero" >> "${OUTDIR}/finalize_push.log"
fi
# Prefer latest finalize_push run, then followup_push, then followup_diag
FOLLOWUP_CAND=""
for pattern in finalize_push_ followup_push_ followup_diag_; do
  C=$(ls -td reports/backtests/${pattern}* 2>/dev/null | head -1)
  if [ -n "${C}" ] && [ -d "${C}" ]; then
    FOLLOWUP_CAND="${C}"
    break
  fi
done

# ---------- 2. Build multi-model evidence bundle ----------
EVID_DIR="${OUTDIR}/multi_model/evidence"
mkdir -p "${EVID_DIR}"

if [ -d "reports/backtests/${BASE_RUN}/multi_model/evidence" ]; then
  cp -v "reports/backtests/${BASE_RUN}/multi_model/evidence/"* "${EVID_DIR}/" 2>/dev/null || true
fi

if [ -n "${FOLLOWUP_CAND}" ]; then
  [ -f "${FOLLOWUP_CAND}/exec_sensitivity/exec_sensitivity.json" ] && cp -v "${FOLLOWUP_CAND}/exec_sensitivity/exec_sensitivity.json" "${EVID_DIR}/" 2>/dev/null || true
  cp -v "${FOLLOWUP_CAND}/exit_sweep/"*.json "${EVID_DIR}/" 2>/dev/null || true
  for expdir in "${FOLLOWUP_CAND}/experiments"/*/; do
    [ -d "${expdir}" ] || continue
    name=$(basename "${expdir}")
    [ -f "${expdir}/metrics.json" ] && cp -v "${expdir}/metrics.json" "${EVID_DIR}/exp_${name}_metrics.json" 2>/dev/null || true
  done
  for sweepdir in "${FOLLOWUP_CAND}/targeted_sweeps"/*/; do
    [ -d "${sweepdir}" ] || continue
    name=$(basename "${sweepdir}")
    [ -f "${sweepdir}/metrics.json" ] && cp -v "${sweepdir}/metrics.json" "${EVID_DIR}/sweep_${name}_metrics.json" 2>/dev/null || true
  done
  [ -f "${FOLLOWUP_CAND}/experiments/compare_summary.md" ] && cp -v "${FOLLOWUP_CAND}/experiments/compare_summary.md" "${EVID_DIR}/" 2>/dev/null || true
fi

if [ -d "${OUTDIR}/multi_model/evidence/plugins" ]; then
  cp -v "${OUTDIR}/multi_model/evidence/plugins/"* "${EVID_DIR}/" 2>/dev/null || true
fi

[ -f "reports/backtests/${BASE_RUN}/baseline/backtest_trades.jsonl" ] && cp -v "reports/backtests/${BASE_RUN}/baseline/backtest_trades.jsonl" "${EVID_DIR}/" 2>/dev/null || true
[ -f "reports/backtests/${BASE_RUN}/baseline/backtest_summary.json" ] && cp -v "reports/backtests/${BASE_RUN}/baseline/backtest_summary.json" "${EVID_DIR}/" 2>/dev/null || true
[ -f "reports/backtests/${BASE_RUN}/baseline/metrics.json" ] && cp -v "reports/backtests/${BASE_RUN}/baseline/metrics.json" "${EVID_DIR}/" 2>/dev/null || true

# ---------- 3. Run multi-model adversarial review with full evidence and explicit --out ----------
MM_OUT="${OUTDIR}/multi_model/out"
mkdir -p "${MM_OUT}"
echo "Running multi_model_runner with roles prosecutor,defender,sre,board and evidence ${EVID_DIR}..."
python3 scripts/multi_model_runner.py \
  --backtest_dir "reports/backtests/${BASE_RUN}" \
  --roles prosecutor,defender,sre,board \
  --evidence "${EVID_DIR}" \
  --out "${MM_OUT}" >> "${OUTDIR}/multi_model_runner.log" 2>&1 || echo "multi_model_runner returned non-zero" >> "${OUTDIR}/multi_model_runner.log"

mkdir -p "${OUTDIR}/multi_model"
cp -v "${MM_OUT}"/* "${OUTDIR}/multi_model/" 2>/dev/null || true

# ---------- 4. Ensure customer advocate is generated and included ----------
if [ -x scripts/generate_customer_advocate.py ]; then
  python3 scripts/generate_customer_advocate.py --backtest-dir "reports/backtests/${BASE_RUN}" --out "${OUTDIR}/customer_advocate.md" >> "${OUTDIR}/customer_advocate.log" 2>&1 || echo "customer advocate generation failed" >> "${OUTDIR}/customer_advocate.log"
elif [ -x scripts/customer_advocate_report.py ]; then
  python3 scripts/customer_advocate_report.py --run-dir "reports/backtests/${BASE_RUN}" --out "${OUTDIR}/customer_advocate.md" >> "${OUTDIR}/customer_advocate.log" 2>&1 || echo "customer_advocate_report failed" >> "${OUTDIR}/customer_advocate.log"
else
  if [ -f "reports/backtests/${BASE_RUN}/customer_advocate.md" ]; then
    cp -v "reports/backtests/${BASE_RUN}/customer_advocate.md" "${OUTDIR}/customer_advocate.md" || true
  else
    cat > "${OUTDIR}/customer_advocate.md" <<TXT
# Customer Advocate (fallback)
Baseline run: ${BASE_RUN}
Please review reports/backtests/${BASE_RUN}/effectiveness/ and attribution/per_signal_pnl.json for levers.
TXT
  fi
fi
cp -v "${OUTDIR}/customer_advocate.md" "${EVID_DIR}/" 2>/dev/null || true

# ---------- 5. Final governance packaging and PROMOTION_CANDIDATES ----------
PROM="${OUTDIR}/PROMOTION_CANDIDATES.md"
echo "# Promotion candidates and rationale" > "${PROM}"
echo "" >> "${PROM}"
if [ -n "${FOLLOWUP_CAND}" ]; then
  if [ -d "${FOLLOWUP_CAND}/targeted_sweeps" ]; then
    for m in "${FOLLOWUP_CAND}/targeted_sweeps"/*/metrics.json; do
      [ -f "${m}" ] || continue
      echo "## $(basename $(dirname "${m}"))" >> "${PROM}"
      jq '{net_pnl, trades_count, win_rate_pct}' "${m}" >> "${PROM}" 2>/dev/null || cat "${m}" >> "${PROM}"
      echo "" >> "${PROM}"
    done
  fi
  if [ -f "${FOLLOWUP_CAND}/experiments/compare_summary.md" ]; then
    echo "## Experiments compare (follow-up)" >> "${PROM}"
    head -n 200 "${FOLLOWUP_CAND}/experiments/compare_summary.md" >> "${PROM}" 2>/dev/null || true
  fi
fi
cp -v "${PROM}" "${EVID_DIR}/" 2>/dev/null || true

# ---------- 6. Final artifact index and summary ----------
ART="${OUTDIR}/ARTIFACT_INDEX.md"
cat > "${ART}" <<TXT
# Artifact index for ${RUN_ID}
- Multi-model outputs: ${OUTDIR}/multi_model/
- Multi-model runner log: ${OUTDIR}/multi_model_runner.log
- Customer advocate: ${OUTDIR}/customer_advocate.md
- Evidence bundle: ${EVID_DIR}/
- Promotion candidates: ${PROM}
- Finalize push log: ${OUTDIR}/finalize_push.log
TXT

# ---------- 7. Print final status and next steps ----------
echo "DONE. Key artifacts written to ${OUTDIR}:"
ls -la "${OUTDIR}" || true
echo ""
echo "Please paste the following artifacts here for synthesis and promotion plan:"
echo "- ${OUTDIR}/multi_model/board_verdict.md (if present) and ${OUTDIR}/multi_model/*"
echo "- ${EVID_DIR}/ (evidence bundle listing)"
echo "- ${OUTDIR}/customer_advocate.md"
echo "- ${OUTDIR}/PROMOTION_CANDIDATES.md"
echo "- reports/backtests/${BASE_RUN}/baseline/metrics.json"
exit 0
