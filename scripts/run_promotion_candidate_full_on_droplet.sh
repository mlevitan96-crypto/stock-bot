#!/usr/bin/env bash
# Full promotion candidate run: timestamped dir, merged config, baseline + parallel slippage + sweeps,
# evidence collection, multi-model, persona synthesis, PROMOTION_CANDIDATES.md.
# Requires: GNU parallel (apt install parallel). Run on droplet as repo user in /root/stock-bot.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root not found"; exit 1; }

# Config
TS=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_BASE="reports/backtests/promotion_candidate_full_${TS}"
mkdir -p "${RUN_BASE}"
OUT_LOG="${RUN_BASE}/run.log"
PARALLEL_JOBS=6
SNAPSHOT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -n1)
BASE_CONFIG="configs/backtest_config.json"
OVERLAY="configs/overlays/promotion_candidate_1.json"
MERGED="/tmp/${TS}_merged_config.json"

if [ -z "${SNAPSHOT}" ] || [ ! -f "${SNAPSHOT}" ]; then
  echo "No snapshot found under data/snapshots/alpaca_1m_snapshot_*.tar.gz"
  exit 1
fi

# 0) Prepare merged config
python3 - <<PY >> "${OUT_LOG}" 2>&1
import json
base = json.load(open("${BASE_CONFIG}"))
try:
    overlay = json.load(open("${OVERLAY}"))
except Exception:
    overlay = {}
base.update({k: v for k, v in overlay.items() if k != "composite_weights"})
cw = base.get("composite_weights", {})
cw.update(overlay.get("composite_weights", {}))
base["composite_weights"] = cw
open("${MERGED}", "w").write(json.dumps(base, indent=2))
print("WROTE_MERGED")
PY

# 1) Baseline run (serial)
BASE_OUT="${RUN_BASE}/baseline"
mkdir -p "${BASE_OUT}"
echo "Running baseline..." | tee -a "${OUT_LOG}"
python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${MERGED}" --out "${BASE_OUT}" --lab-mode --min-exec-score 1.8 >> "${OUT_LOG}" 2>&1 || echo "BASE_WARN" >> "${OUT_LOG}"

# 2) Parallel slippage runs
SLIPPAGES=(0.0 0.0005 0.001 0.002)
echo "Running slippage scenarios in parallel..." | tee -a "${OUT_LOG}"
export RUN_BASE OUT_LOG MERGED SNAPSHOT
parallel -j ${PARALLEL_JOBS} --halt soon,fail=1 bash -c '
S="$1"
OUT="${RUN_BASE}/slippage_${S}"
mkdir -p "${OUT}"
TMP_CFG="/tmp/merged_slip_${S}.json"
python3 - <<PY > "${TMP_CFG}"
import json
base = json.load(open("'"${MERGED}"'"))
base["slippage_model"] = {"type": "pct", "value": '"${S}"'}
open("'"${TMP_CFG}"'", "w").write(json.dumps(base, indent=2))
PY
python3 scripts/run_simulation_backtest_on_droplet.py --bars "'"${SNAPSHOT}"'" --config "${TMP_CFG}" --out "${OUT}" --lab-mode --min-exec-score 1.8 >> "'"${OUT_LOG}"'" 2>&1 || echo "SLIP_WARN ${S}" >> "'"${OUT_LOG}"'"
' ::: "${SLIPPAGES[@]}"

# 3) Parallel targeted sweeps
signals=(flow dark_pool freshness_factor)
multipliers=(0.5 0.75 1.0)
echo "Running targeted sweeps in parallel..." | tee -a "${OUT_LOG}"
export MERGED SNAPSHOT RUN_BASE OUT_LOG
parallel -j ${PARALLEL_JOBS} --halt soon,fail=1 bash -c '
SIG="$1"; M="$2"
OUT="${RUN_BASE}/sweep_${SIG}_x_${M}"
mkdir -p "${OUT}"
TMP_CFG="/tmp/merged_sweep_${SIG}_${M}.json"
python3 - <<PY > "${TMP_CFG}"
import json
base = json.load(open("'"${MERGED}"'"))
cw = base.get("composite_weights", {})
cw["'"${SIG}"'"] = cw.get("'"${SIG}"'", 1.0) * float("'"${M}"'")
base["composite_weights"] = cw
open("'"${TMP_CFG}"'", "w").write(json.dumps(base, indent=2))
PY
python3 scripts/run_simulation_backtest_on_droplet.py --bars "'"${SNAPSHOT}"'" --config "${TMP_CFG}" --out "${OUT}" --lab-mode --min-exec-score 1.8 >> "'"${OUT_LOG}"'" 2>&1 || echo "SWEEP_WARN ${SIG} ${M}" >> "'"${OUT_LOG}"'"
' ::: "${signals[@]}" ::: "${multipliers[@]}"

# 4) Collect metrics into evidence dir (multi_model expects RUN_BASE/baseline/; we pass --backtest_dir RUN_BASE)
EVID="${RUN_BASE}/multi_model/evidence"
mkdir -p "${EVID}"
cp -v "${BASE_OUT}/backtest_trades.jsonl" "${EVID}/" 2>/dev/null || true
if [ -f "${BASE_OUT}/metrics.json" ]; then cp -v "${BASE_OUT}/metrics.json" "${EVID}/exp_baseline_metrics.json" 2>/dev/null || true; fi
for d in "${RUN_BASE}"/sweep_* "${RUN_BASE}"/slippage_*; do
  [ -d "${d}" ] || continue
  if [ -f "${d}/metrics.json" ]; then
    cp -v "${d}/metrics.json" "${EVID}/$(basename ${d})_metrics.json" 2>/dev/null || true
  fi
done

# 5) Run multi-model (backtest_dir = run root so it finds baseline/ under it)
MM_OUT="${RUN_BASE}/multi_model/out"
mkdir -p "${MM_OUT}"
echo "Running multi-model runner..." | tee -a "${OUT_LOG}"
python3 scripts/multi_model_runner.py --backtest_dir "${RUN_BASE}" --roles prosecutor,defender,sre,board --evidence "${EVID}" --out "${MM_OUT}" >> "${OUT_LOG}" 2>&1 || echo "MM_WARN" >> "${OUT_LOG}"

# 6) Synthesize persona JSON from board_verdict if missing (heredoc as stdin, then redirect stdout)
if [ ! -f "${MM_OUT}/persona_recommendations.json" ] && [ -f "${MM_OUT}/board_verdict.md" ]; then
  python3 - "${MM_OUT}/board_verdict.md" <<'PY' > "${MM_OUT}/persona_recommendations.json"
import re, sys, json
bd_path = sys.argv[1]
out = []
pat = re.compile(r'^\s*-\s*\*\*(?P<persona>[^*]+)\*\*\s*—\s*\*\*(?P<verdict>[^*]+)\*\*\s*\(confidence\s*(?P<conf>[\d\.]+)%\)\s*:\s*(?P<action>[^;]+)(?:;\s*evidence:\s*(?P<evidence>.+))?', re.I)
with open(bd_path) as f:
    for line in f:
        m = pat.match(line)
        if m:
            out.append({
                "persona": m.group("persona").strip(),
                "verdict": m.group("verdict").strip().upper(),
                "confidence_pct": float(m.group("conf")) if m.group("conf") else 0.0,
                "top_concerns": [],
                "recommended_actions": [m.group("action").strip()] if m.group("action") else [],
                "evidence_refs": [m.group("evidence").strip()] if m.group("evidence") else []
            })
if not out:
    text = open(bd_path).read()
    m2 = re.search(r"Board.*?(ACCEPT|REJECT|CONDITIONAL)", text, re.I)
    if m2:
        out.append({"persona": "Board", "verdict": m2.group(1).upper(), "confidence_pct": 75.0, "top_concerns": [], "recommended_actions": [], "evidence_refs": []})
print(json.dumps(out, indent=2))
PY
fi

# 7) Produce PROMOTION_CANDIDATES.md
PROM="${RUN_BASE}/PROMOTION_CANDIDATES.md"
echo "# Promotion candidates for ${RUN_BASE}" > "${PROM}"
if [ -f "${MM_OUT}/persona_recommendations.json" ]; then
  jq -r '.[] | "- \(.persona): \(.verdict) (\(.confidence_pct)%) — \(.recommended_actions[0] // ""); evidence: \(.evidence_refs[0] // "")"' "${MM_OUT}/persona_recommendations.json" >> "${PROM}" 2>/dev/null || true
fi
echo "" >> "${PROM}"
echo "Artifacts:" >> "${PROM}"
echo "- baseline metrics: ${BASE_OUT}/metrics.json" >> "${PROM}"
echo "- multi-model: ${MM_OUT}" >> "${PROM}"

# 8) Print summary
echo "Completed full review. Key artifacts under ${RUN_BASE}"
ls -la "${RUN_BASE}" | sed -n '1,200p'
echo "Tail of run log:"
tail -n 200 "${OUT_LOG}"

# 9) Next steps hint
echo "If board verdict is ACCEPT, create PR branch promote/promotion_candidate_1 with ${OVERLAY} and run paper for 7 days."
exit 0
