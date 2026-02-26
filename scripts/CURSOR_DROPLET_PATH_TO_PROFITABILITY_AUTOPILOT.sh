#!/usr/bin/env bash
# CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh
#
# Enforces the loop:
# baseline blame -> decide lever -> apply ONE change -> 50 closed trades -> compare -> LOCK/REVERT
#
# DROPLET ONLY. PAPER ONLY. NO SUPPRESSION.

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="path_to_profitability_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/path_to_profitability/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"
mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

# ---- Inputs you can override
START_DATE_UTC="${START_DATE_UTC:-2026-02-01}"
END_DATE_UTC="${END_DATE_UTC:-$(date -u +%Y-%m-%d)}"
BASELINE_DIR="${BASELINE_DIR:-reports/effectiveness_baseline_blame}"
OVERLAY_DIR="${OVERLAY_DIR:-reports/effectiveness_overlay_check/${RUN_TAG}}"

# Entry lever defaults (small, reversible)
ENTRY_SCORE_BUMP="${ENTRY_SCORE_BUMP:-0.2}"     # e.g. raise MIN_EXEC_SCORE by +0.2

# Exit lever defaults (single tweak; your recommender should pick the exact one)
EXIT_TWEAK_STRENGTH="${EXIT_TWEAK_STRENGTH:-0.05}"

# Gate
MIN_CLOSED_TRADES="${MIN_CLOSED_TRADES:-50}"
POLL_SECONDS="${POLL_SECONDS:-120}"

# Set to 1 to run baseline + recommend + apply only (no wait/compare). Use for deploy verification.
STOP_AFTER_APPLY="${STOP_AFTER_APPLY:-0}"

log "=== START AUTOPILOT ==="
log "OUT_DIR=${OUT_DIR}"
log "BASELINE_DIR=${BASELINE_DIR}"
log "START_DATE_UTC=${START_DATE_UTC} END_DATE_UTC=${END_DATE_UTC}"
log "MIN_CLOSED_TRADES=${MIN_CLOSED_TRADES}"

# ---- Preconditions
[ -f "scripts/analysis/run_effectiveness_reports.py" ] || { log "ERROR missing scripts/analysis/run_effectiveness_reports.py"; exit 2; }
[ -f "scripts/governance/generate_recommendation.py" ] || { log "ERROR missing scripts/governance/generate_recommendation.py"; exit 2; }

# ------------------------------------------------------------
# 1) Build/refresh baseline effectiveness (canonical)
# ------------------------------------------------------------
log "Running baseline effectiveness from logs -> ${BASELINE_DIR}"
mkdir -p "${BASELINE_DIR}"

python3 scripts/analysis/run_effectiveness_reports.py \
  --start "${START_DATE_UTC}" \
  --end "${END_DATE_UTC}" \
  --out-dir "${BASELINE_DIR}" \
  | tee -a "${LOG}"

# Hard gate: join must work (effectiveness_aggregates.json has joined_count)
JOINED_COUNT="$(python3 - <<PY
import json, os
p=os.path.join("${BASELINE_DIR}","effectiveness_aggregates.json")
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get("joined_count",0))
PY
)"
LOSING_TRADES="$(python3 - <<PY
import json, os
p=os.path.join("${BASELINE_DIR}","entry_vs_exit_blame.json")
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get("total_losing_trades",0))
PY
)"

log "Baseline joined_count=${JOINED_COUNT} total_losing_trades=${LOSING_TRADES}"
if [ "${JOINED_COUNT}" -lt 30 ] || [ "${LOSING_TRADES}" -lt 5 ]; then
  log "ERROR: baseline insufficient. Fix attribution<->exit_attribution join keys/logging first."
  log "Expected: joined_count>=30 and total_losing_trades>=5"
  exit 3
fi

# ------------------------------------------------------------
# 2) Auto-decide lever (entry vs exit)
# ------------------------------------------------------------
log "Generating recommendation (entry vs exit decision)"
python3 scripts/governance/generate_recommendation.py \
  --effectiveness-dir "${BASELINE_DIR}" \
  --out "${OUT_DIR}/recommendation.json" \
  | tee -a "${LOG}"

LEVER="$(python3 - <<PY
import json
try:
    j=json.load(open("${OUT_DIR}/recommendation.json"))
    print((j.get("next_lever") or "").lower())
except Exception:
    print("")
PY
)"
log "Recommended lever=${LEVER}"
if [ "${LEVER}" != "entry" ] && [ "${LEVER}" != "exit" ]; then
  log "ERROR: recommender did not return next_lever=entry|exit"
  exit 4
fi

# ------------------------------------------------------------
# 3) Apply ONE change (paper overlay)
# ------------------------------------------------------------
log "Applying ONE change (paper overlay) -> ${OUT_DIR}/overlay_config.json"

python3 - <<PY
import json, os
lever="${LEVER}"
cfg={"run_tag":"${RUN_TAG}","lever":lever,"paper_only":True}

if lever=="entry":
    cfg["change"]={
        "type":"raise_min_exec_score",
        "delta": float("${ENTRY_SCORE_BUMP}")
    }
else:
    cfg["change"]={
        "type":"single_exit_tweak",
        "strength": float("${EXIT_TWEAK_STRENGTH}")
    }

with open("${OUT_DIR}/overlay_config.json","w") as f:
    json.dump(cfg, f, indent=2)
print("WROTE", "${OUT_DIR}/overlay_config.json")
PY

if [ -f "scripts/ops/apply_paper_overlay.py" ]; then
  log "Applying overlay via scripts/ops/apply_paper_overlay.py"
  python3 scripts/ops/apply_paper_overlay.py \
    --overlay "${OUT_DIR}/overlay_config.json" \
    | tee -a "${LOG}"
  OVERLAY_START_DATE="$(date -u +%Y-%m-%d)"
else
  log "ERROR: missing scripts/ops/apply_paper_overlay.py (needed to actually apply overlay + restart paper bot)"
  exit 5
fi

if [ "${STOP_AFTER_APPLY}" = "1" ]; then
  log "STOP_AFTER_APPLY=1: skipping wait loop and compare. Run again without STOP_AFTER_APPLY for full autopilot."
  cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
PATH TO PROFITABILITY AUTOPILOT (STOPPED AFTER APPLY)

BASELINE: ${BASELINE_DIR}
RECOMMENDATION: ${OUT_DIR}/recommendation.json
OVERLAY CONFIG: ${OUT_DIR}/overlay_config.json
Overlay applied. Restart paper bot with overlay env/config, then run this script again without STOP_AFTER_APPLY=1 to wait for 50 trades and compare.
LOG: ${LOG}
EOF
  echo "OUT_DIR: ${OUT_DIR}"
  log "=== DONE (STOP_AFTER_APPLY) ==="
  exit 0
fi

# ------------------------------------------------------------
# 4) Wait for >=50 closed trades in overlay window
# ------------------------------------------------------------
log "Waiting for >=${MIN_CLOSED_TRADES} closed trades in overlay window (since ${OVERLAY_START_DATE})"
mkdir -p "${OVERLAY_DIR}"

while true; do
  python3 scripts/analysis/run_effectiveness_reports.py \
    --start "${OVERLAY_START_DATE}" \
    --end "$(date -u +%Y-%m-%d)" \
    --out-dir "${OVERLAY_DIR}" \
    > "${OVERLAY_DIR}/latest_effectiveness_run.txt" 2>&1 || true

  CLOSED="$(python3 - <<PY
import json, os
p=os.path.join("${OVERLAY_DIR}","effectiveness_aggregates.json")
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get("joined_count",0))
PY
)"
  log "Overlay closed_trades (joined_count)=${CLOSED}"
  if [ "${CLOSED}" -ge "${MIN_CLOSED_TRADES}" ]; then
    break
  fi
  sleep "${POLL_SECONDS}"
done

# ------------------------------------------------------------
# 5) Compare overlay vs baseline and emit LOCK/REVERT packet
# ------------------------------------------------------------
log "Comparing overlay vs baseline"
python3 scripts/analysis/compare_effectiveness_runs.py \
  --baseline "${BASELINE_DIR}" \
  --candidate "${OVERLAY_DIR}" \
  --out "${OUT_DIR}/lock_or_revert_decision.json" \
  | tee -a "${LOG}" || true

cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
PATH TO PROFITABILITY AUTOPILOT COMPLETE

BASELINE:
- ${BASELINE_DIR}

RECOMMENDATION:
- ${OUT_DIR}/recommendation.json

OVERLAY CONFIG:
- ${OUT_DIR}/overlay_config.json

OVERLAY EFFECTIVENESS:
- ${OVERLAY_DIR}

DECISION:
- ${OUT_DIR}/lock_or_revert_decision.json

LOG:
- ${LOG}
EOF

log "=== DONE ==="
echo "OUT_DIR: ${OUT_DIR}"
