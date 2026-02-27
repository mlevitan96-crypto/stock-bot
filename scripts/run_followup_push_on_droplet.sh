#!/usr/bin/env bash
# APPLY OVERLAY SUPPORT, RERUN DIAGNOSTICS, EXIT SWEEP, EXPERIMENTS, MULTI-MODEL (DROPLET)
# 1) Overlay support: merge overlay JSON into base config (simulation applies composite_weights + exit).
# 2) Exec sensitivity (sequential, no wrapper timeout).
# 3) Exit sweep (full; current implementation may be stub).
# 4) Three overlay experiments (dark_pool -25%, freshness -30%, tighten exit trail).
# 5) Multi-model adversarial with full evidence and --out.
# 6) compare_summary, ARTIFACT_INDEX, and key artifacts under one follow-up dir.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

# ---------- Configurable variables ----------
BASE_RUN="alpaca_monday_final_20260222T174120Z"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="followup_push_${TS}"
OUTDIR="reports/backtests/${RUN_ID}"
mkdir -p "${OUTDIR}"
echo "RUN_ID=${RUN_ID}" > "${OUTDIR}/run_meta.txt"

SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
BASE_CONFIG="configs/backtest_config.json"
EVIDENCE_DIR="reports/backtests/${BASE_RUN}/multi_model/evidence"
MM_BASE_DIR="reports/backtests/${BASE_RUN}"

if [ ! -f "${SNAPSHOT}" ]; then
  ALT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -1)
  [ -n "${ALT}" ] && SNAPSHOT="${ALT}" && echo "Using snapshot: ${SNAPSHOT}"
fi

# ---------- Helper: merge overlay into base config and write temp config ----------
write_merged_config() {
  local overlay="$1"
  local outcfg="$2"
  python3 - "${BASE_CONFIG}" "${overlay}" "${outcfg}" <<'PY'
import json, sys
base_path, ov_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
base = json.load(open(base_path))
try:
    ov = json.load(open(ov_path))
except Exception:
    ov = {}
for k, v in ov.items():
    if k == "composite_weights":
        base.setdefault("composite_weights", {}).update(v)
    elif k == "exit":
        base.setdefault("exit", {}).update(v)
    elif k != "notes":
        base[k] = v
with open(out_path, "w") as f:
    json.dump(base, f, indent=2)
print("wrote merged config to", out_path)
PY
}

# ---------- 1) Ensure overlay files exist ----------
mkdir -p configs/overlays
cat > configs/overlays/tune_dark_pool_minus25.json <<'JSON'
{
  "composite_weights": {"dark_pool": 0.75},
  "notes": "Reduce dark_pool weight by 25% for robustness test"
}
JSON
cat > configs/overlays/tune_freshness_smooth.json <<'JSON'
{
  "composite_weights": {"freshness_factor": 0.7},
  "freshness_smoothing_window": 3,
  "notes": "Lower freshness weight and add 3-sample smoothing"
}
JSON
cat > configs/overlays/tune_exit_trail.json <<'JSON'
{
  "exit": {
    "profit_acceleration_trailing_stop_pct": 0.01,
    "profit_acceleration_delay_minutes": 30
  },
  "notes": "Tighten trailing stop on accelerated profits"
}
JSON

# ---------- 2) Exec sensitivity: sequential slippage scenarios ----------
mkdir -p "${OUTDIR}/exec_sensitivity"
echo "Running exec sensitivity sequentially..."
exec_summary="${OUTDIR}/exec_sensitivity/exec_sensitivity.json"
echo "{" > "${exec_summary}"
first=true
for s in 0.0 0.0005 0.001; do
  TMP_CFG="/tmp/${RUN_ID}_exec_cfg_${s}.json"
  python3 - <<PY
import json
base = json.load(open("${BASE_CONFIG}"))
base["slippage_model"] = {"type": "pct", "value": ${s}}
with open("${TMP_CFG}", "w") as f:
    json.dump(base, f, indent=2)
print("wrote ${TMP_CFG}")
PY
  OUT_SUB="${OUTDIR}/exec_sensitivity/slippage_${s}"
  mkdir -p "${OUT_SUB}"
  echo "Simulating slippage ${s} -> ${OUT_SUB} ..."
  python3 scripts/run_simulation_backtest_on_droplet.py \
    --bars "${SNAPSHOT}" \
    --config "${TMP_CFG}" \
    --out "${OUT_SUB}" \
    --lab-mode \
    --min-exec-score 1.8 || echo "WARN: simulation for slippage ${s} failed" > "${OUT_SUB}/ERROR.txt"
  MET="${OUT_SUB}/metrics.json"
  [ ! -f "${MET}" ] && MET="${OUT_SUB}/baseline/metrics.json"
  if [ -f "${MET}" ]; then
    PNL=$(jq -r '.net_pnl // .total_pnl_usd // "null"' "${MET}" 2>/dev/null || echo "null")
    TRADES=$(jq -r '.trades_count // .trades // "null"' "${MET}" 2>/dev/null || echo "null")
  else
    PNL=null
    TRADES=null
  fi
  if [ "${first}" = true ]; then
    first=false
    echo "  \"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TRADES}}" >> "${exec_summary}"
  else
    echo "  ,\"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TRADES}}" >> "${exec_summary}"
  fi
done
echo "}" >> "${exec_summary}"
echo "Exec sensitivity summary written to ${exec_summary}"

# ---------- 3) Exit sweep ----------
mkdir -p "${OUTDIR}/exit_sweep"
echo "Running exit sweep ..."
python3 scripts/run_exit_optimization_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config "${BASE_CONFIG}" \
  --out "${OUTDIR}/exit_sweep" || echo "WARN: exit sweep non-zero" > "${OUTDIR}/exit_sweep/ERROR.txt"

# ---------- 4) Overlay experiments (merged config) ----------
mkdir -p "${OUTDIR}/experiments"
EXPS=(tune_dark_pool_minus25 tune_freshness_smooth tune_exit_trail)
for e in "${EXPS[@]}"; do
  OVERLAY="configs/overlays/${e}.json"
  MERGED_CFG="/tmp/${RUN_ID}_${e}_cfg.json"
  write_merged_config "${OVERLAY}" "${MERGED_CFG}"
  OUT_EXP="${OUTDIR}/experiments/${e}"
  mkdir -p "${OUT_EXP}"
  echo "Running experiment ${e} -> ${OUT_EXP}"
  python3 scripts/run_simulation_backtest_on_droplet.py \
    --bars "${SNAPSHOT}" \
    --config "${MERGED_CFG}" \
    --out "${OUT_EXP}" \
    --lab-mode \
    --min-exec-score 1.8 || echo "WARN: experiment ${e} failed" > "${OUT_EXP}/ERROR.txt"
  if [ -f "${OUT_EXP}/baseline/metrics.json" ] && [ ! -f "${OUT_EXP}/metrics.json" ]; then
    cp -v "${OUT_EXP}/baseline/metrics.json" "${OUT_EXP}/metrics.json" || true
  fi
done

# ---------- 5) Compare summary and ARTIFACT_INDEX ----------
CMP="${OUTDIR}/experiments/compare_summary.md"
echo "# Experiments compare for ${RUN_ID}" > "${CMP}"
echo "" >> "${CMP}"
echo "Baseline run: ${MM_BASE_DIR}" >> "${CMP}"
echo "" >> "${CMP}"
BASE_MET="${MM_BASE_DIR}/baseline/metrics.json"
if [ -f "${BASE_MET}" ]; then
  echo "## Baseline metrics" >> "${CMP}"
  jq '{net_pnl, trades_count, win_rate_pct}' "${BASE_MET}" >> "${CMP}" 2>/dev/null || cat "${BASE_MET}" >> "${CMP}"
else
  echo "Baseline metrics not found at ${BASE_MET}" >> "${CMP}"
fi
for e in "${EXPS[@]}"; do
  EMET="${OUTDIR}/experiments/${e}/metrics.json"
  echo "" >> "${CMP}"
  echo "## Experiment ${e}" >> "${CMP}"
  if [ -f "${EMET}" ]; then
    jq '{net_pnl, trades_count, win_rate_pct}' "${EMET}" >> "${CMP}" 2>/dev/null || cat "${EMET}" >> "${CMP}"
  else
    echo "metrics.json missing for ${e}" >> "${CMP}"
  fi
done

ART="${OUTDIR}/ARTIFACT_INDEX.md"
cat > "${ART}" <<TXT
# Artifact index for ${RUN_ID}

- Exec sensitivity: ${OUTDIR}/exec_sensitivity/
- Exit sweep: ${OUTDIR}/exit_sweep/
- Experiments: ${OUTDIR}/experiments/
- Multi-model evidence: ${OUTDIR}/multi_model/evidence/
- Multi-model outputs: ${OUTDIR}/multi_model/
- Compare summary: ${CMP}
TXT

# ---------- 6) Multi-model with full evidence and --out ----------
EVID="${OUTDIR}/multi_model/evidence"
mkdir -p "${EVID}"
cp -v "${EVIDENCE_DIR}/"* "${EVID}/" 2>/dev/null || true
cp -v "${OUTDIR}/exec_sensitivity/exec_sensitivity.json" "${EVID}/" 2>/dev/null || true
cp -v "${OUTDIR}/exit_sweep/"*.json "${EVID}/" 2>/dev/null || true
for e in "${EXPS[@]}"; do
  [ -f "${OUTDIR}/experiments/${e}/metrics.json" ] && cp -v "${OUTDIR}/experiments/${e}/metrics.json" "${EVID}/exp_${e}_metrics.json" 2>/dev/null || true
done
[ -f "${MM_BASE_DIR}/baseline/backtest_trades.jsonl" ] && cp -v "${MM_BASE_DIR}/baseline/backtest_trades.jsonl" "${EVID}/" 2>/dev/null || true
[ -f "${MM_BASE_DIR}/baseline/backtest_summary.json" ] && cp -v "${MM_BASE_DIR}/baseline/backtest_summary.json" "${EVID}/" 2>/dev/null || true

MM_OUT="${OUTDIR}/multi_model/out"
mkdir -p "${MM_OUT}"
echo "Running multi_model_runner with evidence -> ${MM_OUT} ..."
python3 scripts/multi_model_runner.py \
  --backtest_dir "${MM_BASE_DIR}" \
  --roles prosecutor,defender,sre,board \
  --evidence "${EVID}" \
  --out "${MM_OUT}" || echo "WARN: multi_model_runner non-zero" > "${MM_OUT}/ERROR.txt"

mkdir -p "${OUTDIR}/multi_model"
cp -v "${MM_OUT}"/* "${OUTDIR}/multi_model/" 2>/dev/null || true

# ---------- 7) Summary ----------
echo "Follow-up push run complete. Key artifacts:"
echo "  Run dir: ${OUTDIR}"
echo "  Exec sensitivity: ${OUTDIR}/exec_sensitivity/"
echo "  Exit sweep: ${OUTDIR}/exit_sweep/"
echo "  Experiments compare: ${CMP}"
echo "  Multi-model: ${OUTDIR}/multi_model/"
echo "  Artifact index: ${ART}"
echo ""
echo "Tail of log (last 100 lines):"
tail -n 100 /tmp/followup_diag.log 2>/dev/null || true
echo ""
echo "DONE. Paste for synthesis:"
echo "  - ${OUTDIR}/exec_sensitivity/exec_sensitivity.json"
echo "  - ${OUTDIR}/exit_sweep/exit_sweep_summary.json"
echo "  - ${OUTDIR}/experiments/compare_summary.md"
echo "  - ${OUTDIR}/multi_model/board_verdict.md"
echo "  - ${MM_BASE_DIR}/attribution/per_signal_pnl.json"
echo "  - ${MM_BASE_DIR}/ablation/ablation_summary.json"
echo "  - ${MM_BASE_DIR}/baseline/metrics.json"
exit 0
