#!/usr/bin/env bash
# COMPLETE DIAGNOSTICS, TARGETED SWEEPS, AND MULTI-MODEL REVIEW (DROPLET)
# 1) Exec sensitivity: inspect existing or re-run sequentially if slippage not applied
# 2) Exit sweep
# 3) Overlay experiments (merged config)
# 4) Compare summary and ARTIFACT_INDEX
# 5) Multi-model with full evidence and --out
set -euo pipefail
cd /root/stock-bot || { echo "Repo root missing"; exit 1; }

# Config
BASE_RUN="alpaca_monday_final_20260222T174120Z"
FOLLOWUP_BASE="followup_diag_20260222T225611Z"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="finalize_push_${TS}"
OUTDIR="reports/backtests/${RUN_ID}"
mkdir -p "${OUTDIR}"
echo "RUN_ID=${RUN_ID}" > "${OUTDIR}/run_meta.txt"

SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
BASE_CONFIG="configs/backtest_config.json"
EVID_BASE="reports/backtests/${BASE_RUN}/multi_model/evidence"
MM_BASE_DIR="reports/backtests/${BASE_RUN}"

if [ ! -f "${SNAPSHOT}" ]; then
  ALT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -1)
  [ -n "${ALT}" ] && SNAPSHOT="${ALT}" && echo "Using snapshot: ${SNAPSHOT}"
fi

# 1) Inspect existing exec_sensitivity artifact and re-run if slippage not applied
ESRC="reports/followup_diag_artifacts/exec_sensitivity/exec_sensitivity.json"
[ ! -f "${ESRC}" ] && ESRC="reports/backtests/${FOLLOWUP_BASE}/exec_sensitivity/exec_sensitivity.json"
ESOUT="${OUTDIR}/exec_sensitivity"
mkdir -p "${ESOUT}"
if [ -f "${ESRC}" ]; then
  echo "Found exec_sensitivity at ${ESRC}; copying to run dir."
  cp -v "${ESRC}" "${ESOUT}/exec_sensitivity.json" || true
  python3 - <<PY
import json
p="${ESOUT}/exec_sensitivity.json"
try:
    d=json.load(open(p))
    vals=[v.get("net_pnl") for v in d.values() if isinstance(v, dict)]
    if vals and len(set(vals))==1:
        print("SLIPPAGE_NOT_APPLIED")
    else:
        print("SLIPPAGE_APPLIED")
except Exception as e:
    print("ESRC_INVALID", e)
PY
  if python3 - <<PY
import json
p="${ESOUT}/exec_sensitivity.json"
d=json.load(open(p))
vals=[v.get("net_pnl") for v in d.values() if isinstance(v, dict)]
print(len(vals) > 0 and len(set(vals))==1)
PY 2>/dev/null | grep -q True; then
    echo "Re-running exec sensitivity sequentially to ensure slippage applied..."
    SLIPPAGES=(0.0 0.0005 0.001)
    echo "{" > "${ESOUT}/exec_sensitivity.json"
    first=true
    for s in "${SLIPPAGES[@]}"; do
      TMP_CFG="/tmp/${RUN_ID}_exec_${s}.json"
      python3 - <<PY
import json
base=json.load(open("${BASE_CONFIG}"))
base["slippage_model"]={"type":"pct","value":${s}}
with open("${TMP_CFG}","w") as f:
    json.dump(base,f,indent=2)
print("wrote", "${TMP_CFG}")
PY
      OUT_SUB="${ESOUT}/slippage_${s}"
      mkdir -p "${OUT_SUB}"
      python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${TMP_CFG}" --out "${OUT_SUB}" --lab-mode --min-exec-score 1.8 || echo "WARN: slippage ${s} run failed" > "${OUT_SUB}/ERROR.txt"
      MET="${OUT_SUB}/metrics.json"
      [ ! -f "${MET}" ] && MET="${OUT_SUB}/baseline/metrics.json"
      if [ -f "${MET}" ]; then
        PNL=$(jq -r '.net_pnl // .total_pnl_usd // "null"' "${MET}" 2>/dev/null || echo "null")
        TR=$(jq -r '.trades_count // .trades // "null"' "${MET}" 2>/dev/null || echo "null")
      else
        PNL=null; TR=null
      fi
      if [ "${first}" = true ]; then
        first=false
        echo "  \"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${ESOUT}/exec_sensitivity.json"
      else
        echo "  ,\"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${ESOUT}/exec_sensitivity.json"
      fi
    done
    echo "}" >> "${ESOUT}/exec_sensitivity.json"
  fi
else
  echo "No exec_sensitivity artifact found; running sequential slippage runs..."
  SLIPPAGES=(0.0 0.0005 0.001)
  echo "{" > "${ESOUT}/exec_sensitivity.json"
  first=true
  for s in "${SLIPPAGES[@]}"; do
    TMP_CFG="/tmp/${RUN_ID}_exec_${s}.json"
    python3 - <<PY
import json
base=json.load(open("${BASE_CONFIG}"))
base["slippage_model"]={"type":"pct","value":${s}}
with open("${TMP_CFG}","w") as f:
    json.dump(base,f,indent=2)
print("wrote", "${TMP_CFG}")
PY
    OUT_SUB="${ESOUT}/slippage_${s}"
    mkdir -p "${OUT_SUB}"
    python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${TMP_CFG}" --out "${OUT_SUB}" --lab-mode --min-exec-score 1.8 || echo "WARN: slippage ${s} run failed" > "${OUT_SUB}/ERROR.txt"
    MET="${OUT_SUB}/metrics.json"
    [ ! -f "${MET}" ] && MET="${OUT_SUB}/baseline/metrics.json"
    if [ -f "${MET}" ]; then
      PNL=$(jq -r '.net_pnl // .total_pnl_usd // "null"' "${MET}" 2>/dev/null || echo "null")
      TR=$(jq -r '.trades_count // .trades // "null"' "${MET}" 2>/dev/null || echo "null")
    else
      PNL=null; TR=null
    fi
    if [ "${first}" = true ]; then
      first=false
      echo "  \"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${ESOUT}/exec_sensitivity.json"
    else
      echo "  ,\"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${ESOUT}/exec_sensitivity.json"
    fi
  done
  echo "}" >> "${ESOUT}/exec_sensitivity.json"
fi

# 2) Exit sweep (attempt run; if stub remains, note it)
mkdir -p "${OUTDIR}/exit_sweep"
python3 scripts/run_exit_optimization_on_droplet.py --bars "${SNAPSHOT}" --config "${BASE_CONFIG}" --out "${OUTDIR}/exit_sweep" || echo "EXIT_SWEEP_WARN" > "${OUTDIR}/exit_sweep/ERROR.txt"

# 3) Run overlay experiments using merged config (ensure overlay dir and files exist)
mkdir -p configs/overlays
[ -f configs/overlays/tune_dark_pool_minus25.json ] || cat > configs/overlays/tune_dark_pool_minus25.json <<'JSON'
{"composite_weights": {"dark_pool": 0.75}, "notes": "Reduce dark_pool weight by 25%"}
JSON
[ -f configs/overlays/tune_freshness_smooth.json ] || cat > configs/overlays/tune_freshness_smooth.json <<'JSON'
{"composite_weights": {"freshness_factor": 0.7}, "freshness_smoothing_window": 3, "notes": "Lower freshness weight and smoothing"}
JSON
[ -f configs/overlays/tune_exit_trail.json ] || cat > configs/overlays/tune_exit_trail.json <<'JSON'
{"exit": {"profit_acceleration_trailing_stop_pct": 0.01, "profit_acceleration_delay_minutes": 30}, "notes": "Tighten trailing stop"}
JSON
OVERLAYS=("configs/overlays/tune_dark_pool_minus25.json" "configs/overlays/tune_freshness_smooth.json" "configs/overlays/tune_exit_trail.json")
mkdir -p "${OUTDIR}/experiments"
for ov in "${OVERLAYS[@]}"; do
  [ -f "${ov}" ] || continue
  NAME=$(basename "${ov}" .json)
  MERGED="/tmp/${RUN_ID}_${NAME}_cfg.json"
  python3 - <<PY
import json
base=json.load(open("${BASE_CONFIG}"))
try:
  ov=json.load(open("${ov}"))
except Exception:
  ov={}
if "composite_weights" in ov:
  base.setdefault("composite_weights",{}).update(ov["composite_weights"])
if "exit" in ov:
  base.setdefault("exit",{}).update(ov["exit"])
for k,v in ov.items():
  if k not in ("composite_weights","exit","notes"):
    base[k]=v
with open("${MERGED}","w") as f:
  json.dump(base,f,indent=2)
print("wrote", "${MERGED}")
PY
  OUT_EXP="${OUTDIR}/experiments/${NAME}"
  mkdir -p "${OUT_EXP}"
  python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${MERGED}" --out "${OUT_EXP}" --lab-mode --min-exec-score 1.8 || echo "EXP_WARN" > "${OUT_EXP}/ERROR.txt"
  if [ -f "${OUT_EXP}/baseline/metrics.json" ] && [ ! -f "${OUT_EXP}/metrics.json" ]; then
    cp -v "${OUT_EXP}/baseline/metrics.json" "${OUT_EXP}/metrics.json" || true
  fi
done

# 4) Generate experiments compare summary and artifact index
CMP="${OUTDIR}/experiments/compare_summary.md"
echo "# Experiments compare for ${RUN_ID}" > "${CMP}"
echo "" >> "${CMP}"
BASE_MET="${MM_BASE_DIR}/baseline/metrics.json"
if [ -f "${BASE_MET}" ]; then
  echo "## Baseline metrics" >> "${CMP}"
  jq '{net_pnl, trades_count, win_rate_pct}' "${BASE_MET}" >> "${CMP}" 2>/dev/null || cat "${BASE_MET}" >> "${CMP}"
fi
for d in "${OUTDIR}/experiments"/*; do
  [ -d "${d}" ] || continue
  if [ -f "${d}/metrics.json" ]; then
    echo "" >> "${CMP}"
    echo "## $(basename ${d})" >> "${CMP}"
    jq '{net_pnl, trades_count, win_rate_pct}' "${d}/metrics.json" >> "${CMP}" 2>/dev/null || cat "${d}/metrics.json" >> "${CMP}"
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

# 5) Re-run multi-model with full evidence and --out
MM_OUT="${OUTDIR}/multi_model/out"
mkdir -p "${MM_OUT}"
EVID="${OUTDIR}/multi_model/evidence"
mkdir -p "${EVID}"
cp -v "${EVID_BASE}/"* "${EVID}/" 2>/dev/null || true
cp -v "${OUTDIR}/exec_sensitivity/exec_sensitivity.json" "${EVID}/" 2>/dev/null || true
cp -v "${OUTDIR}/exit_sweep/"*.json "${EVID}/" 2>/dev/null || true
for d in "${OUTDIR}/experiments"/*/; do
  [ -d "${d}" ] || continue
  name=$(basename "${d}")
  [ -f "${d}/metrics.json" ] && cp -v "${d}/metrics.json" "${EVID}/exp_${name}_metrics.json" 2>/dev/null || true
done
[ -f "${MM_BASE_DIR}/baseline/backtest_trades.jsonl" ] && cp -v "${MM_BASE_DIR}/baseline/backtest_trades.jsonl" "${EVID}/" 2>/dev/null || true
[ -f "${MM_BASE_DIR}/baseline/backtest_summary.json" ] && cp -v "${MM_BASE_DIR}/baseline/backtest_summary.json" "${EVID}/" 2>/dev/null || true

python3 scripts/multi_model_runner.py --backtest_dir "${MM_BASE_DIR}" --roles prosecutor,defender,sre,board --evidence "${EVID}" --out "${MM_OUT}" || echo "MM_WARN" > "${MM_OUT}/ERROR.txt"
cp -v "${MM_OUT}"/* "${OUTDIR}/multi_model/" 2>/dev/null || true

# 6) Finalize and print summary
echo "Follow-up push run complete. Key artifacts:"
echo "- Exec sensitivity: ${OUTDIR}/exec_sensitivity/"
echo "- Exit sweep: ${OUTDIR}/exit_sweep/"
echo "- Experiments compare: ${CMP}"
echo "- Multi-model outputs: ${OUTDIR}/multi_model/"
echo "- Artifact index: ${ART}"
echo ""
echo "Tail of follow-up log (last 200 lines):"
tail -n 200 /tmp/followup_diag.log 2>/dev/null || true
echo ""
echo "DONE. Paste these artifacts here for synthesis:"
echo "- ${OUTDIR}/exec_sensitivity/exec_sensitivity.json"
echo "- ${OUTDIR}/exit_sweep/exit_sweep_summary.json"
echo "- ${OUTDIR}/experiments/compare_summary.md"
echo "- ${OUTDIR}/multi_model/board_verdict.md"
echo "- reports/backtests/${BASE_RUN}/attribution/per_signal_pnl.json"
echo "- reports/backtests/${BASE_RUN}/ablation/ablation_summary.json"
echo "- reports/backtests/${BASE_RUN}/baseline/metrics.json"
exit 0
