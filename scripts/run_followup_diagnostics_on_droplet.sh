#!/usr/bin/env bash
# RERUN MISSING DIAGNOSTICS + SMALL TUNING EXPERIMENTS (DROPLET)
# 1) Exec sensitivity (sequential, longer per-run)
# 2) Multi_model with correct --out and evidence
# 3) Exit sweep (full)
# 4) Three overlay experiments (config merge; simulation may not apply all overlay keys yet)
# 5) Comparison summary and artifact paths
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

BASE_RUN="alpaca_monday_final_20260222T174120Z"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="followup_diag_${TS}"
OUTDIR="reports/backtests/${RUN_ID}"
mkdir -p "${OUTDIR}"
echo "RUN_ID=${RUN_ID}" > "${OUTDIR}/run_meta.txt"

SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
BASE_CONFIG="configs/backtest_config.json"

# Snapshot fallback: use base run snapshot path if exact name missing
if [ ! -f "${SNAPSHOT}" ]; then
  ALT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -1)
  if [ -n "${ALT}" ]; then SNAPSHOT="${ALT}"; echo "Using snapshot: ${SNAPSHOT}"; fi
fi

# Helper: write temp config with modified slippage (value as decimal, e.g. 0.0005 = 0.05%)
write_slippage_config() {
  local out_path="$1"
  local slippage_val="$2"
  python3 - <<PY
import json
with open("${BASE_CONFIG}") as f:
    base = json.load(f)
base["slippage_model"] = {"type": "pct", "value": ${slippage_val}}
with open("${out_path}", "w") as f:
    json.dump(base, f, indent=2)
print("wrote", "${out_path}")
PY
}

# ---------- 1) Exec sensitivity (sequential) ----------
mkdir -p "${OUTDIR}/exec_sensitivity"
echo "Running exec sensitivity sequentially (slippage 0.0, 0.0005, 0.001)..."
exec_summary="${OUTDIR}/exec_sensitivity/exec_sensitivity.json"
echo "{" > "${exec_summary}"
first=true
for s in 0.0 0.0005 0.001; do
  TMP_CFG="/tmp/exec_sens_cfg_${RUN_ID}_${s}.json"
  write_slippage_config "${TMP_CFG}" "${s}"
  OUT_SUB="${OUTDIR}/exec_sensitivity/slippage_${s}"
  mkdir -p "${OUT_SUB}"
  echo "Running simulation for slippage ${s} -> ${OUT_SUB}..."
  python3 scripts/run_simulation_backtest_on_droplet.py \
    --bars "${SNAPSHOT}" \
    --config "${TMP_CFG}" \
    --out "${OUT_SUB}" \
    --lab-mode \
    --min-exec-score 1.8 || echo "WARN: simulation slippage ${s} failed" >> "${OUT_SUB}/ERROR.txt"
  MET="${OUT_SUB}/metrics.json"
  if [ -f "${MET}" ]; then
    PNL=$(jq -r '.net_pnl // .total_pnl_usd // null' "${MET}" 2>/dev/null || echo "null")
    TRADES=$(jq -r '.trades_count // .trades // null' "${MET}" 2>/dev/null || echo "null")
  else
    PNL=null
    TRADES=null
  fi
  if [ "${first}" = true ]; then first=false; else echo "," >> "${exec_summary}"; fi
  echo "  \"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TRADES}}" >> "${exec_summary}"
done
echo "" >> "${exec_summary}"
echo "}" >> "${exec_summary}"
# Remove trailing comma from last entry (we avoided it by first=true)
python3 -c "
import json
p=\"${exec_summary}\"
s=open(p).read()
# fix possible double comma
s=s.replace(',\n}', '\n}')
open(p,'w').write(s)
print('exec_sensitivity summary written to', p)
"

# ---------- 2) Multi_model with --out and evidence ----------
echo "Re-running multi_model with --out and evidence..."
MM_OUT="${OUTDIR}/multi_model"
mkdir -p "${MM_OUT}"
python3 scripts/multi_model_runner.py \
  --backtest_dir "reports/backtests/${BASE_RUN}" \
  --roles prosecutor,defender,sre,board \
  --evidence "reports/backtests/${BASE_RUN}/multi_model/evidence" \
  --out "${MM_OUT}" || echo "WARN: multi_model_runner non-zero" >> "${MM_OUT}/ERROR.txt"
# Copy evidence into this run for traceability
mkdir -p "${OUTDIR}/multi_model/evidence"
cp -v "reports/backtests/${BASE_RUN}/multi_model/evidence/"* "${OUTDIR}/multi_model/evidence/" 2>/dev/null || true

# ---------- 3) Exit sweep ----------
echo "Running exit sweep..."
mkdir -p "${OUTDIR}/exit_sweep"
python3 scripts/run_exit_optimization_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config "${BASE_CONFIG}" \
  --out "${OUTDIR}/exit_sweep" || echo "WARN: exit sweep non-zero" >> "${OUTDIR}/exit_sweep/ERROR.txt"

# ---------- 4) Overlay experiments (merge overlay into config; run simulation) ----------
mkdir -p configs/overlays
# A: dark_pool -25% (note: simulation may not read composite_weights from config; overlay saved for traceability)
cat > configs/overlays/tune_dark_pool_minus25.json <<'JSON'
{"overlay": {"composite_weights": {"dark_pool": 0.75}}, "notes": "Reduce dark_pool weight by 25%"}
JSON
# B: freshness -30%
cat > configs/overlays/tune_freshness_smooth.json <<'JSON'
{"overlay": {"composite_weights": {"freshness_factor": 0.7}, "freshness_smoothing_window": 3}, "notes": "Lower freshness weight and smoothing"}
JSON
# C: exit tightening
cat > configs/overlays/tune_exit_trail.json <<'JSON'
{"overlay": {"exit": {"profit_acceleration_trailing_stop_pct": 0.01, "profit_acceleration_delay_minutes": 30}}, "notes": "Tighten trailing stop on profits"}
JSON

EXPERIMENTS=("tune_dark_pool_minus25" "tune_freshness_smooth" "tune_exit_trail")
for e in "${EXPERIMENTS[@]}"; do
  OVERLAY="configs/overlays/${e}.json"
  OUT_EXP="${OUTDIR}/experiments/${e}"
  mkdir -p "${OUT_EXP}"
  echo "Running experiment ${e} -> ${OUT_EXP} (config merge; simulation uses base config if overlay not supported)..."
  # Merge base config with overlay for traceability; simulation may only use base keys
  TMP_CFG="/tmp/exp_cfg_${RUN_ID}_${e}.json"
  python3 - <<PY
import json
with open("${BASE_CONFIG}") as f:
    base = json.load(f)
with open("${OVERLAY}") as f:
    ov = json.load(f)
base["_overlay"] = ov.get("overlay", ov)
base["_overlay_notes"] = ov.get("notes", "")
with open("${TMP_CFG}", "w") as f:
    json.dump(base, f, indent=2)
PY
  python3 scripts/run_simulation_backtest_on_droplet.py \
    --bars "${SNAPSHOT}" \
    --config "${TMP_CFG}" \
    --out "${OUT_EXP}" \
    --lab-mode \
    --min-exec-score 1.8 || echo "WARN: experiment ${e} failed" >> "${OUT_EXP}/ERROR.txt"
  [ -f scripts/generate_backtest_summary.py ] && python3 scripts/generate_backtest_summary.py --dir "${OUT_EXP}" --out "${OUT_EXP}/summary" 2>/dev/null || true
done

# ---------- 5) Compare summary ----------
CMP="${OUTDIR}/experiments/compare_summary.md"
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

# ---------- 6) Artifact index ----------
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
echo "Tail of /tmp/monday_final.log (last 50 lines):" >> "${INDEX}"
tail -n 50 /tmp/monday_final.log >> "${INDEX}" 2>/dev/null || echo "(log not found)" >> "${INDEX}"

echo "DONE. Key artifacts:"
echo "  Exec sensitivity: ${OUTDIR}/exec_sensitivity/exec_sensitivity.json"
echo "  Multi-model: ${OUTDIR}/multi_model/"
echo "  Exit sweep: ${OUTDIR}/exit_sweep/"
echo "  Experiments: ${OUTDIR}/experiments/compare_summary.md"
echo "  Index: ${INDEX}"
exit 0
