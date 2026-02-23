#!/usr/bin/env bash
# FINALIZE PUSH, VERIFY SLIPPAGE, COMPUTE MFE/MAE IF NEEDED, TARGETED SWEEPS, MULTI-MODEL WITH PLUGINS
# Run on droplet at /root/stock-bot as repo user.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root missing"; exit 1; }

TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="final_finish_${TS}"
OUTDIR="reports/backtests/${RUN_ID}"
mkdir -p "${OUTDIR}"
echo "RUN_ID=${RUN_ID}" > "${OUTDIR}/run_meta.txt"

SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
BASE_CONFIG="configs/backtest_config.json"
BASE_RUN="alpaca_monday_final_20260222T174120Z"
if [ ! -f "${SNAPSHOT}" ]; then
  SNAPSHOT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -1)
  [ -z "${SNAPSHOT}" ] && SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
  echo "Using snapshot: ${SNAPSHOT}" >> "${OUTDIR}/run_meta.txt"
fi

# 1) Run push-with-plugins orchestration (collects plugins, runs finalize)
if [ -x scripts/run_push_with_plugins_on_droplet.sh ]; then
  bash scripts/run_push_with_plugins_on_droplet.sh >> "${OUTDIR}/push_with_plugins.log" 2>&1 || echo "WARN: push_with_plugins returned non-zero" >> "${OUTDIR}/push_with_plugins.log"
else
  echo "ERROR: scripts/run_push_with_plugins_on_droplet.sh missing" > "${OUTDIR}/ERROR.txt"
  exit 1
fi

# 2) Locate follow-up run dir (newest first)
FOLLOWUP_DIR=""
for pattern in finalize_push_ followup_push_ followup_diag_; do
  D=$(ls -td reports/backtests/${pattern}* 2>/dev/null | head -1)
  if [ -n "${D}" ] && [ -d "${D}" ]; then
    FOLLOWUP_DIR="${D}"
    break
  fi
done
if [ -z "${FOLLOWUP_DIR}" ]; then
  echo "No follow-up run dir found; aborting" >> "${OUTDIR}/ERROR.txt"
  exit 1
fi
echo "FOLLOWUP_DIR=${FOLLOWUP_DIR}" >> "${OUTDIR}/run_meta.txt"

# 3) Verify exec sensitivity; re-run sequential slippage if identical PnL
ES_SUM="${FOLLOWUP_DIR}/exec_sensitivity/exec_sensitivity.json"
mkdir -p "${FOLLOWUP_DIR}/exec_sensitivity_recheck"
if [ -f "${ES_SUM}" ]; then
  python3 - <<PY > "${OUTDIR}/es_check.txt"
import json
d=json.load(open("${ES_SUM}"))
vals=[v.get("net_pnl") for v in d.values() if isinstance(v,dict)]
print(len(vals), len(set(vals)))
PY
  if grep -q " 1$" "${OUTDIR}/es_check.txt" 2>/dev/null; then
    echo "Exec sensitivity shows identical PnL across slippage; re-running sequential slippage runs..."
    SLIPPAGES=(0.0 0.0005 0.001)
    echo "{" > "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json"
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
      OUT_SUB="${FOLLOWUP_DIR}/exec_sensitivity_recheck/slippage_${s}"
      mkdir -p "${OUT_SUB}"
      python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${TMP_CFG}" --out "${OUT_SUB}" --lab-mode --min-exec-score 1.8 || echo "WARN" > "${OUT_SUB}/ERROR.txt"
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
        echo "  \"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json"
      else
        echo "  ,\"slippage_${s}\": {\"net_pnl\": ${PNL}, \"trades\": ${TR}}" >> "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json"
      fi
    done
    echo "}" >> "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json"
    cp -v "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json" "${OUTDIR}/exec_sensitivity_recheck.json" 2>/dev/null || true
  else
    echo "Slippage appears applied; no re-run needed."
  fi
else
  echo "No exec_sensitivity summary found; consider re-running exec sensitivity separately."
fi

# 4) If exit_sweep is stub or missing, compute best-effort MFE/MAE from baseline trades
EXIT_SUM="${FOLLOWUP_DIR}/exit_sweep/exit_sweep_summary.json"
TRADE_FILE="reports/backtests/${BASE_RUN}/baseline/backtest_trades.jsonl"
mkdir -p "${FOLLOWUP_DIR}/exit_sweep"
if [ ! -f "${EXIT_SUM}" ] || grep -q '"status": "stub"' "${EXIT_SUM}" 2>/dev/null; then
  python3 - "${TRADE_FILE}" "${FOLLOWUP_DIR}/exit_sweep/exit_sweep_summary.json" <<'PY'
import json, sys
trades_path = sys.argv[1]
out_path = sys.argv[2]
mfe, mae = [], []
try:
    with open(trades_path) as f:
        for line in f:
            try:
                t = json.loads(line)
                eq = t.get("exit_quality_metrics") or {}
                if eq.get("mfe_pct") is not None:
                    mfe.append(float(eq["mfe_pct"]))
                if eq.get("mae_pct") is not None:
                    mae.append(float(eq["mae_pct"]))
            except Exception:
                continue
except Exception as e:
    with open(out_path, "w") as f:
        json.dump({"status": "error", "error": str(e)}, f, indent=2)
    sys.exit(0)
def stats(a):
    if not a:
        return {"count": 0, "mean": None}
    return {"count": len(a), "mean": sum(a) / len(a)}
out = {"status": "computed_from_trades", "mfe": stats(mfe), "mae": stats(mae)}
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print("wrote", out_path)
PY
fi

# 5) Targeted weight scaling sweeps (merge overlay into config; simulation has no --overlay)
SWEEP_DIR="${FOLLOWUP_DIR}/targeted_sweeps"
mkdir -p "${SWEEP_DIR}"
signals=("flow" "dark_pool" "freshness_factor")
multipliers=(0.5 0.75 1.0)
for sig in "${signals[@]}"; do
  for m in "${multipliers[@]}"; do
    OVERLAY="/tmp/overlay_${sig}_${m}.json"
    MERGED="/tmp/${RUN_ID}_sweep_${sig}_${m}.json"
    cat > "${OVERLAY}" <<JSON
{"composite_weights": {"${sig}": ${m}}, "notes": "targeted sweep ${sig} * ${m}"}
JSON
    python3 - "${BASE_CONFIG}" "${OVERLAY}" "${MERGED}" <<'PY'
import json, sys
base = json.load(open(sys.argv[1]))
ov = json.load(open(sys.argv[2]))
base.setdefault("composite_weights", {}).update(ov.get("composite_weights", {}))
with open(sys.argv[3], "w") as f:
    json.dump(base, f, indent=2)
PY
    OUT_EXP="${SWEEP_DIR}/${sig}_x_${m}"
    mkdir -p "${OUT_EXP}"
    python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${MERGED}" --out "${OUT_EXP}" --lab-mode --min-exec-score 1.8 || echo "WARN" > "${OUT_EXP}/ERROR.txt"
    if [ -f "${OUT_EXP}/baseline/metrics.json" ] && [ ! -f "${OUT_EXP}/metrics.json" ]; then
      cp -v "${OUT_EXP}/baseline/metrics.json" "${OUT_EXP}/metrics.json" || true
    fi
  done
done

# 6) Re-run multi-model with full evidence and --out (include plugin evidence)
MM_OUT="${FOLLOWUP_DIR}/multi_model/out_final"
mkdir -p "${MM_OUT}"
EVID="${FOLLOWUP_DIR}/multi_model/evidence"
mkdir -p "${EVID}"
cp -v "${FOLLOWUP_DIR}/exec_sensitivity/exec_sensitivity.json" "${EVID}/" 2>/dev/null || true
[ -f "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json" ] && cp -v "${FOLLOWUP_DIR}/exec_sensitivity_recheck/exec_sensitivity.json" "${EVID}/exec_sensitivity_recheck.json" 2>/dev/null || true
cp -v "${FOLLOWUP_DIR}/exit_sweep/"*.json "${EVID}/" 2>/dev/null || true
for expdir in "${FOLLOWUP_DIR}/experiments"/*/; do
  [ -d "${expdir}" ] || continue
  name=$(basename "${expdir}")
  [ -f "${expdir}/metrics.json" ] && cp -v "${expdir}/metrics.json" "${EVID}/exp_${name}_metrics.json" 2>/dev/null || true
done
for sweepdir in "${FOLLOWUP_DIR}/targeted_sweeps"/*/; do
  [ -d "${sweepdir}" ] || continue
  name=$(basename "${sweepdir}")
  [ -f "${sweepdir}/metrics.json" ] && cp -v "${sweepdir}/metrics.json" "${EVID}/sweep_${name}_metrics.json" 2>/dev/null || true
done
# Plugin evidence from push_with_plugins run if present
PUSH_RUN=$(ls -td reports/backtests/push_with_plugins_* 2>/dev/null | head -1)
if [ -n "${PUSH_RUN}" ] && [ -d "${PUSH_RUN}/multi_model/evidence/plugins" ]; then
  cp -v "${PUSH_RUN}/multi_model/evidence/plugins/"* "${EVID}/" 2>/dev/null || true
fi
cp -v "reports/backtests/${BASE_RUN}/baseline/backtest_trades.jsonl" "${EVID}/" 2>/dev/null || true
cp -v "reports/backtests/${BASE_RUN}/baseline/backtest_summary.json" "${EVID}/" 2>/dev/null || true

python3 scripts/multi_model_runner.py --backtest_dir "reports/backtests/${BASE_RUN}" --roles prosecutor,defender,sre,board --evidence "${EVID}" --out "${MM_OUT}" >> "${FOLLOWUP_DIR}/multi_model_final.log" 2>&1 || echo "WARN: multi_model_runner returned non-zero" >> "${FOLLOWUP_DIR}/multi_model_final.log"
cp -v "${MM_OUT}"/* "${FOLLOWUP_DIR}/multi_model/" 2>/dev/null || true

# 7) Produce PROMOTION_CANDIDATES.md and ARTIFACT_INDEX.md
PROM="${FOLLOWUP_DIR}/PROMOTION_CANDIDATES.md"
echo "# Promotion candidates" > "${PROM}"
for d in "${FOLLOWUP_DIR}/targeted_sweeps"/*; do
  [ -d "${d}" ] || continue
  if [ -f "${d}/metrics.json" ]; then
    echo "## $(basename ${d})" >> "${PROM}"
    jq '{net_pnl, trades_count, win_rate_pct}' "${d}/metrics.json" >> "${PROM}" 2>/dev/null || cat "${d}/metrics.json" >> "${PROM}"
    echo "" >> "${PROM}"
  fi
done
if [ -f "${FOLLOWUP_DIR}/experiments/compare_summary.md" ]; then
  echo "## Experiments compare" >> "${PROM}"
  head -n 100 "${FOLLOWUP_DIR}/experiments/compare_summary.md" >> "${PROM}" 2>/dev/null || true
fi
ART="${FOLLOWUP_DIR}/ARTIFACT_INDEX.md"
cat > "${ART}" <<TXT
# Artifact index for ${FOLLOWUP_DIR}
- Exec sensitivity: ${FOLLOWUP_DIR}/exec_sensitivity/
- Exec sensitivity recheck: ${FOLLOWUP_DIR}/exec_sensitivity_recheck/
- Exit sweep: ${FOLLOWUP_DIR}/exit_sweep/
- Experiments: ${FOLLOWUP_DIR}/experiments/
- Targeted sweeps: ${FOLLOWUP_DIR}/targeted_sweeps/
- Multi-model outputs: ${FOLLOWUP_DIR}/multi_model/
- Promotion candidates: ${PROM}
TXT

# 8) Print final status and key artifact paths
echo "Completed. Key artifacts under ${FOLLOWUP_DIR}:"
ls -la "${FOLLOWUP_DIR}" || true
echo ""
echo "Please paste these artifacts here for final synthesis:"
echo "- ${FOLLOWUP_DIR}/exec_sensitivity/exec_sensitivity.json (or exec_sensitivity_recheck/exec_sensitivity.json)"
echo "- ${FOLLOWUP_DIR}/exit_sweep/exit_sweep_summary.json"
echo "- ${FOLLOWUP_DIR}/experiments/compare_summary.md"
echo "- ${FOLLOWUP_DIR}/multi_model/board_verdict.md"
echo "- ${FOLLOWUP_DIR}/PROMOTION_CANDIDATES.md"
echo "- reports/backtests/${BASE_RUN}/baseline/metrics.json"
exit 0
