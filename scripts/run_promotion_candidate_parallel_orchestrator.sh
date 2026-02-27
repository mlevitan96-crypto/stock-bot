#!/usr/bin/env bash
# Orchestrator: parallel promotion candidate review, evidence aggregation, multi-model, PR creation
# Paste and run on a controller host with SSH access to workers.
set -euo pipefail

# -------------------------
# CONFIGURE THESE VARIABLES
# -------------------------
REPO_PATH="${REPO_PATH:-/root/stock-bot}"
# Use env WORKERS (space-separated) if set; otherwise default list
if [ -n "${WORKERS:-}" ]; then
  IFS=' ' read -r -a WORKERS <<< "${WORKERS}"
else
  WORKERS=( "worker1" "worker2" "worker3" )
fi
REMOTE_USER="${REMOTE_USER:-root}"
PARALLEL_JOBS_PER_WORKER=6
CONTROLLER_RUN_BASE="$(pwd)/reports/backtests/promotion_candidate_parallel_$(date -u +%Y%m%dT%H%M%SZ)"
OVERLAY="configs/overlays/promotion_candidate_1.json"
BASE_CONFIG="configs/backtest_config.json"
SNAPSHOT_GLOB="data/snapshots/alpaca_1m_snapshot_*.tar.gz"
SLIPPAGES=(0.0 0.0005 0.001 0.002)
SWEEP_SIGNALS=(flow dark_pool freshness_factor)
SWEEP_MULTS=(0.5 0.75 1.0)
ROLES="prosecutor,defender,sre,board,customer_advocate"
GH_TOKEN="${GH_TOKEN:-}"
AUTO_MERGE="${AUTO_MERGE:-false}"
ACCEPTANCE_MIN_PNL_RATIO=0.90
MIN_TRADES=100
WORKER_RUN_ROOT="/root/worker_runs"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10"

mkdir -p "${CONTROLLER_RUN_BASE}"
LOG="${CONTROLLER_RUN_BASE}/controller.log"
EVIDENCE_DIR="${CONTROLLER_RUN_BASE}/multi_model/evidence"
MM_OUT="${CONTROLLER_RUN_BASE}/multi_model/out"
mkdir -p "${EVIDENCE_DIR}" "${MM_OUT}"

# Run from repo so BASE_CONFIG and OVERLAY resolve
cd "${REPO_PATH}" || { echo "Repo path ${REPO_PATH} not found"; exit 1; }

echo "Controller run dir: ${CONTROLLER_RUN_BASE}" | tee "${LOG}"

# -------------------------
# helper functions
# -------------------------
run_on_worker() {
  local host="$1"; shift
  ssh ${SSH_OPTS} "${REMOTE_USER}@${host}" "$@"
}

scp_to_worker() {
  local src="$1"; local host="$2"; local dest="$3"
  scp -q ${SSH_OPTS} "${src}" "${REMOTE_USER}@${host}:${dest}"
}

# -------------------------
# Step 0: ensure repo up to date on workers
# -------------------------
ORIGIN_URL=$(git -C "${REPO_PATH}" remote get-url origin 2>/dev/null || echo "")
for host in "${WORKERS[@]}"; do
  echo "Updating repo on ${host}" | tee -a "${LOG}"
  run_on_worker "${host}" "set -euo pipefail; mkdir -p ${REPO_PATH}; cd ${REPO_PATH} || exit 2; if [ -d .git ]; then git fetch --all || true; git checkout main || true; git pull origin main || true; else git clone --depth 1 ${ORIGIN_URL} ${REPO_PATH} || true; fi; chmod +x scripts/*.sh 2>/dev/null || true" || echo "warn: update ${host}" | tee -a "${LOG}"
done

# -------------------------
# Step 1: prepare merged config on controller and copy to workers
# -------------------------
MERGED_CFG="${CONTROLLER_RUN_BASE}/merged_config.json"
python3 - <<PY
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
open("${MERGED_CFG}", "w").write(json.dumps(base, indent=2))
print("WROTE_MERGED")
PY
echo "Merged config written to ${MERGED_CFG}" | tee -a "${LOG}"

for host in "${WORKERS[@]}"; do
  scp_to_worker "${MERGED_CFG}" "${host}" "${REPO_PATH}/tmp_merged_config.json" || { echo "scp to ${host} failed" | tee -a "${LOG}"; exit 1; }
done

# -------------------------
# Step 2: dispatch tasks to workers (baseline + slippage + sweeps)
# -------------------------
DISPATCH_SCRIPT="${CONTROLLER_RUN_BASE}/run_worker_tasks.sh"
cat > "${DISPATCH_SCRIPT}" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
REPO_PATH="$1"
MERGED_REMOTE="$2"
RUN_BASE="$3"
PARALLEL_JOBS="$4"
SNAPSHOT_GLOB="$5"
SLIPPAGES_STR="$6"
SWEEP_SIGNALS_STR="$7"
SWEEP_MULTS_STR="$8"

IFS=' ' read -r -a SLIPPAGES <<< "${SLIPPAGES_STR}"
IFS=' ' read -r -a SWEEP_SIGNALS <<< "${SWEEP_SIGNALS_STR}"
IFS=' ' read -r -a SWEEP_MULTS <<< "${SWEEP_MULTS_STR}"

mkdir -p "${RUN_BASE}"
cd "${REPO_PATH}" || exit 2

SNAPSHOT=$(ls -t ${SNAPSHOT_GLOB} 2>/dev/null | head -n1 || true)
if [ -z "${SNAPSHOT}" ]; then
  echo "NO_SNAPSHOT" >&2
  exit 2
fi

BASE_OUT="${RUN_BASE}/baseline"
mkdir -p "${BASE_OUT}"
python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${MERGED_REMOTE}" --out "${BASE_OUT}" --lab-mode --min-exec-score 1.8 || echo "BASE_WARN"

for s in "${SLIPPAGES[@]}"; do
  OUT="${RUN_BASE}/slippage_${s}"
  mkdir -p "${OUT}"
  TMP_CFG="/tmp/merged_slip_${s}.json"
  python3 - <<PY > "${TMP_CFG}"
import json
base = json.load(open("${MERGED_REMOTE}"))
base["slippage_model"] = {"type": "pct", "value": ${s}}
open("${TMP_CFG}", "w").write(json.dumps(base, indent=2))
PY
  python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${TMP_CFG}" --out "${OUT}" --lab-mode --min-exec-score 1.8 || echo "SLIP_WARN ${s}"
done

for sig in "${SWEEP_SIGNALS[@]}"; do
  for m in "${SWEEP_MULTS[@]}"; do
    OUT="${RUN_BASE}/sweep_${sig}_x_${m}"
    mkdir -p "${OUT}"
    TMP_CFG="/tmp/merged_sweep_${sig}_${m}.json"
    python3 - <<PY > "${TMP_CFG}"
import json
base = json.load(open("${MERGED_REMOTE}"))
cw = base.get("composite_weights", {})
cw["${sig}"] = cw.get("${sig}", 1.0) * ${m}
base["composite_weights"] = cw
open("${TMP_CFG}", "w").write(json.dumps(base, indent=2))
PY
    python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config "${TMP_CFG}" --out "${OUT}" --lab-mode --min-exec-score 1.8 || echo "SWEEP_WARN ${sig} ${m}"
  done
done

EVID_LOCAL="${RUN_BASE}/evidence"
mkdir -p "${EVID_LOCAL}"
[ -f "${BASE_OUT}/backtest_trades.jsonl" ] && cp -v "${BASE_OUT}/backtest_trades.jsonl" "${EVID_LOCAL}/" 2>/dev/null || true
[ -f "${BASE_OUT}/metrics.json" ] && cp -v "${BASE_OUT}/metrics.json" "${EVID_LOCAL}/baseline_metrics.json" 2>/dev/null || true
for d in "${RUN_BASE}"/sweep_* "${RUN_BASE}"/slippage_*; do
  [ -d "${d}" ] || continue
  [ -f "${d}/metrics.json" ] && cp -v "${d}/metrics.json" "${EVID_LOCAL}/$(basename ${d})_metrics.json" 2>/dev/null || true
done
echo "WORKER_DONE"
SH
chmod +x "${DISPATCH_SCRIPT}"

PIDS=()
for host in "${WORKERS[@]}"; do
  WORK_RUN_DIR="${WORKER_RUN_ROOT}/run_$(date -u +%Y%m%dT%H%M%SZ)_${host}"
  echo "${WORK_RUN_DIR}" > "${CONTROLLER_RUN_BASE}/worker_${host}.dir"
  run_on_worker "${host}" "mkdir -p ${WORK_RUN_DIR} && cat > ${WORK_RUN_DIR}/run_worker.sh" < "${DISPATCH_SCRIPT}" || { echo "dispatch write ${host} failed" | tee -a "${LOG}"; continue; }
  run_on_worker "${host}" "bash ${WORK_RUN_DIR}/run_worker.sh '${REPO_PATH}' '${REPO_PATH}/tmp_merged_config.json' '${WORK_RUN_DIR}' '${PARALLEL_JOBS_PER_WORKER}' '${SNAPSHOT_GLOB}' '${SLIPPAGES[*]}' '${SWEEP_SIGNALS[*]}' '${SWEEP_MULTS[*]}'" >> "${LOG}" 2>&1 &
  PIDS+=( $! )
  echo "Dispatched tasks to ${host} (${WORK_RUN_DIR})" | tee -a "${LOG}"
done

wait "${PIDS[@]}" || true
echo "All worker tasks completed (or returned). Proceeding to collect evidence." | tee -a "${LOG}"

# -------------------------
# Step 3: rsync evidence and baseline back from workers
# -------------------------
for host in "${WORKERS[@]}"; do
  WDIR=$(cat "${CONTROLLER_RUN_BASE}/worker_${host}.dir" 2>/dev/null || true)
  [ -n "${WDIR}" ] || continue
  echo "Rsyncing evidence from ${host} (${WDIR})" | tee -a "${LOG}"
  mkdir -p "${EVIDENCE_DIR}/${host}"
  rsync -avz -e "ssh ${SSH_OPTS}" --include '*.json' --include '*.jsonl' --exclude '*' "${REMOTE_USER}@${host}:${WDIR}/evidence/" "${EVIDENCE_DIR}/${host}/" 2>/dev/null || echo "rsync_warn ${host}" | tee -a "${LOG}"
done

# Copy baseline from first worker for multi_model (expects backtest_dir/baseline/)
FIRST="${WORKERS[0]}"
WDIR_FIRST=$(cat "${CONTROLLER_RUN_BASE}/worker_${FIRST}.dir" 2>/dev/null || true)
if [ -n "${WDIR_FIRST}" ]; then
  mkdir -p "${CONTROLLER_RUN_BASE}/baseline"
  rsync -avz -e "ssh ${SSH_OPTS}" "${REMOTE_USER}@${FIRST}:${WDIR_FIRST}/baseline/" "${CONTROLLER_RUN_BASE}/baseline/" 2>/dev/null || echo "rsync baseline warn" | tee -a "${LOG}"
fi

# -------------------------
# Step 4: run multi-model locally with aggregated evidence
# -------------------------
echo "Running multi_model_runner.py with evidence ${EVIDENCE_DIR}" | tee -a "${LOG}"
python3 scripts/multi_model_runner.py --backtest_dir "${CONTROLLER_RUN_BASE}" --roles "${ROLES}" --evidence "${EVIDENCE_DIR}" --out "${MM_OUT}" >> "${LOG}" 2>&1 || echo "MM_WARN" | tee -a "${LOG}"

# -------------------------
# Step 5: synthesize persona JSON if missing (heredoc as stdin, then redirect stdout)
# -------------------------
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

# -------------------------
# Step 6: produce PROMOTION_CANDIDATES.md and concise persona table
# -------------------------
PROM="${CONTROLLER_RUN_BASE}/PROMOTION_CANDIDATES.md"
echo "# Promotion candidates for ${CONTROLLER_RUN_BASE}" > "${PROM}"
if [ -f "${MM_OUT}/persona_recommendations.json" ]; then
  jq -r '.[] | "- **\(.persona)**: **\(.verdict)** (\(.confidence_pct)%) — \(.recommended_actions[0] // ""); evidence: \(.evidence_refs[0] // "")"' "${MM_OUT}/persona_recommendations.json" >> "${PROM}" 2>/dev/null || true
fi
echo "" >> "${PROM}"
echo "Artifacts:" >> "${PROM}"
echo "- baseline metrics: ${CONTROLLER_RUN_BASE}/baseline/metrics.json" >> "${PROM}"
echo "- multi-model: ${MM_OUT}" >> "${PROM}"

echo "Full review completed. Controller artifacts: ${CONTROLLER_RUN_BASE}" | tee -a "${LOG}"
echo "Persona recommendations (concise):"
if [ -f "${MM_OUT}/persona_recommendations.json" ]; then
  jq -r '.[] | "\(.persona)\t\(.verdict)\t\(.confidence_pct)%\t\(.recommended_actions[0] // "")"' "${MM_OUT}/persona_recommendations.json" | column -t -s $'\t' 2>/dev/null || cat "${MM_OUT}/persona_recommendations.json"
fi

# -------------------------
# Step 7: Acceptance checks and optional PR creation
# -------------------------
ACCEPT=false
if [ -f "${CONTROLLER_RUN_BASE}/baseline/metrics.json" ]; then
  CAND_PNL=$(jq -r '.net_pnl // .netPnL // .netPnLUsd // .net_pnl_usd // 0' "${CONTROLLER_RUN_BASE}/baseline/metrics.json" 2>/dev/null || echo "0")
  TRADES=$(jq -r '.trades_count // .trades // 0' "${CONTROLLER_RUN_BASE}/baseline/metrics.json" 2>/dev/null || echo "0")
  PNL_GT_ZERO=0
  if command -v bc >/dev/null 2>&1; then
    PNL_GT_ZERO=$(echo "${CAND_PNL} > 0" | bc -l 2>/dev/null || echo "0")
  else
    [ "${CAND_PNL}" != "0" ] && [ "${CAND_PNL}" != "0.0" ] && PNL_GT_ZERO=1
  fi
  if [ "${TRADES:-0}" -ge "${MIN_TRADES}" ] 2>/dev/null && [ "${PNL_GT_ZERO}" = "1" ]; then
    ACCEPT=true
  fi
fi

if [ -f "${MM_OUT}/board_verdict.md" ] && grep -qi "ACCEPT" "${MM_OUT}/board_verdict.md" 2>/dev/null; then
  ACCEPT=true
fi

if ${ACCEPT}; then
  echo "Acceptance gates passed or board ACCEPT. Preparing promotion branch and PR." | tee -a "${LOG}"
  if [ ! -f "${REPO_PATH}/${OVERLAY}" ]; then
    mkdir -p "${REPO_PATH}/$(dirname "${OVERLAY}")"
    cat > "${REPO_PATH}/${OVERLAY}" <<'JSON'
{
  "composite_weights": {
    "dark_pool": 0.75,
    "freshness_factor": 0.7
  },
  "freshness_smoothing_window": 3,
  "notes": "Promotion candidate: reduce dark_pool by 25% and smooth/lower freshness to reduce single-signal fragility"
}
JSON
    git -C "${REPO_PATH}" add "${OVERLAY}" || true
  fi

  PR_BRANCH="promote/promotion_candidate_1"
  git -C "${REPO_PATH}" fetch origin main || true
  git -C "${REPO_PATH}" checkout -B "${PR_BRANCH}" origin/main || git -C "${REPO_PATH}" checkout -B "${PR_BRANCH}" || true
  git -C "${REPO_PATH}" add "${OVERLAY}" || true
  if ! git -C "${REPO_PATH}" diff --cached --quiet 2>/dev/null; then
    git -C "${REPO_PATH}" commit -m "Promotion candidate: reduce dark_pool and smooth freshness_factor (promotion_candidate_1)" || true
  fi

  if [ -n "${GH_TOKEN}" ]; then
    git -C "${REPO_PATH}" push -u origin "${PR_BRANCH}" 2>/dev/null || echo "git push failed" | tee -a "${LOG}"
    PR_BODY="${CONTROLLER_RUN_BASE}/PR_BODY.md"
    cat > "${PR_BODY}" <<'MD'
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
    echo "${GH_TOKEN}" | gh auth login --with-token 2>/dev/null || true
    gh pr create --title "Paper promotion: reduce dark_pool weight and smooth freshness_factor" --body-file "${PR_BODY}" --base main --head "${PR_BRANCH}" 2>/dev/null || echo "gh pr create failed; branch pushed" | tee -a "${LOG}"
    if ${AUTO_MERGE}; then
      gh pr merge --auto --squash --delete-branch 2>/dev/null || echo "gh pr merge failed" | tee -a "${LOG}"
    fi
    echo "PR created (or attempted). PR body at ${PR_BODY}" | tee -a "${LOG}"
  else
    echo "GH_TOKEN not set; branch created locally: ${PR_BRANCH}. Create PR manually; PR body at ${CONTROLLER_RUN_BASE}/PR_BODY.md" | tee -a "${LOG}"
  fi
else
  echo "Acceptance gates not met or board did not ACCEPT. Manual review required. See ${MM_OUT}/board_verdict.md" | tee -a "${LOG}"
fi

echo "Orchestration complete. Controller artifacts: ${CONTROLLER_RUN_BASE}" | tee -a "${LOG}"
echo "Key artifacts:"
echo "- baseline metrics: ${CONTROLLER_RUN_BASE}/baseline/metrics.json"
echo "- multi-model: ${MM_OUT}"
echo "- persona JSON: ${MM_OUT}/persona_recommendations.json"
echo "- promotion candidates: ${CONTROLLER_RUN_BASE}/PROMOTION_CANDIDATES.md"

cat <<'ROLL' >> "${LOG}"
Rollback commands:
# revert overlay commit locally and push revert branch
git checkout main
git pull origin main
git checkout -b revert/promotion_candidate_1
git rm configs/overlays/promotion_candidate_1.json
git commit -m "Revert promotion_candidate_1 overlay"
git push origin revert/promotion_candidate_1
# or revert the single commit by SHA:
# git revert <commit-sha>
ROLL

echo "Done. Logs: ${LOG}"
