#!/usr/bin/env bash
# CURSOR_DROPLET_PATH_TO_PROFITABILITY_EXIT_AUTOPILOT.sh
#
# Enforces: baseline -> recommend EXIT -> apply ONE exit tweak -> 50 closed trades -> LOCK/REVERT
# DROPLET ONLY. PAPER ONLY. NO SUPPRESSION.

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="path_to_profitability_exit_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/path_to_profitability/${RUN_TAG}"
LOG="/tmp/path_to_profitability_exit_autopilot.log"
mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

# ---- Tunables (small, reversible)
START_DATE_UTC="${START_DATE_UTC:-2026-02-01}"
END_DATE_UTC="${END_DATE_UTC:-$(date -u +%Y-%m-%d)}"
BASELINE_DIR="${BASELINE_DIR:-reports/effectiveness_baseline_blame}"
OVERLAY_DIR="${OVERLAY_DIR:-reports/effectiveness_overlay_check/${RUN_TAG}}"
EXIT_TWEAK_STRENGTH="${EXIT_TWEAK_STRENGTH:-0.05}"   # small delta
MIN_CLOSED_TRADES="${MIN_CLOSED_TRADES:-50}"
POLL_SECONDS="${POLL_SECONDS:-120}"

log "=== EXIT AUTOPILOT START ==="
log "OUT_DIR=${OUT_DIR}"
log "BASELINE_DIR=${BASELINE_DIR}"
log "START_DATE_UTC=${START_DATE_UTC} END_DATE_UTC=${END_DATE_UTC}"
log "MIN_CLOSED_TRADES=${MIN_CLOSED_TRADES}"

# ---- Preconditions
[ -f "scripts/analysis/run_effectiveness_reports.py" ] || { log "ERROR missing run_effectiveness_reports.py"; exit 2; }
[ -f "scripts/governance/generate_recommendation.py" ] || { log "ERROR missing generate_recommendation.py"; exit 2; }
[ -f "scripts/analysis/compare_effectiveness_runs.py" ] || { log "ERROR missing compare_effectiveness_runs.py"; exit 2; }
[ -f "scripts/ops/apply_paper_overlay.py" ] || { log "ERROR missing apply_paper_overlay.py"; exit 2; }

# ------------------------------------------------------------
# 0) Ensure entry overlay is removed (clean baseline)
# ------------------------------------------------------------
log "Ensuring entry overlay is removed"
if [ -f "/etc/systemd/system/stock-bot.service.d/paper-overlay.conf" ]; then
  sudo rm /etc/systemd/system/stock-bot.service.d/paper-overlay.conf
  sudo systemctl daemon-reload
  sudo systemctl restart stock-bot.service
  log "Removed entry overlay and restarted stock-bot"
else
  log "No entry overlay present"
fi

# ------------------------------------------------------------
# 1) Build baseline effectiveness (canonical)
# ------------------------------------------------------------
log "Running baseline effectiveness -> ${BASELINE_DIR}"
mkdir -p "${BASELINE_DIR}"

python3 scripts/analysis/run_effectiveness_reports.py \
  --start "${START_DATE_UTC}" \
  --end "${END_DATE_UTC}" \
  --out-dir "${BASELINE_DIR}" \
  | tee -a "${LOG}"

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
  log "ERROR: baseline insufficient. Fix joins/logging first."
  exit 3
fi

# ------------------------------------------------------------
# 2) Recommendation (must be EXIT)
# ------------------------------------------------------------
log "Generating recommendation"
python3 scripts/governance/generate_recommendation.py \
  --effectiveness-dir "${BASELINE_DIR}" \
  --out "${OUT_DIR}/recommendation.json" \
  | tee -a "${LOG}"

LEVER="$(python3 - <<PY
import json
j=json.load(open("${OUT_DIR}/recommendation.json"))
print(j.get("next_lever","").lower())
PY
)"
# Allow override to run EXIT autopilot even when recommender says entry
if [ -n "${FORCE_LEVER:-}" ]; then
  LEVER="$(echo "${FORCE_LEVER}" | tr '[:upper:]' '[:lower:]')"
  log "FORCE_LEVER=${FORCE_LEVER} -> lever=${LEVER}"
fi
log "Recommended lever=${LEVER}"
if [ "${LEVER}" != "exit" ]; then
  log "ERROR: recommender did not select EXIT (set FORCE_LEVER=exit to run anyway). Aborting to avoid stacking."
  exit 4
fi

# ------------------------------------------------------------
# 3) Apply ONE exit tweak (paper)
# ------------------------------------------------------------
log "Applying ONE exit tweak (paper overlay)"
python3 - <<PY
import json
cfg={
  "run_tag":"${RUN_TAG}",
  "lever":"exit",
  "paper_only":True,
  "change":{
    "type":"single_exit_tweak",
    "strength": float("${EXIT_TWEAK_STRENGTH}")
  }
}
json.dump(cfg, open("${OUT_DIR}/overlay_config.json","w"), indent=2)
print("WROTE", "${OUT_DIR}/overlay_config.json")
PY

python3 scripts/ops/apply_paper_overlay.py \
  --overlay "${OUT_DIR}/overlay_config.json" \
  --no_suppression \
  | tee -a "${LOG}"

# Activate exit overlay via systemd (tuning_loader reads GOVERNED_TUNING_CONFIG)
PAPER_OVERLAY_JSON="${REPO}/config/tuning/paper_overlay.json"
DROPIN_DIR="/etc/systemd/system/stock-bot.service.d"
mkdir -p "${DROPIN_DIR}"
echo "[Service]" | sudo tee "${DROPIN_DIR}/exit-paper-overlay.conf"
echo "Environment=GOVERNED_TUNING_CONFIG=${PAPER_OVERLAY_JSON}" | sudo tee -a "${DROPIN_DIR}/exit-paper-overlay.conf"
sudo systemctl daemon-reload
sudo systemctl restart stock-bot.service
log "Restarted stock-bot with exit overlay active (GOVERNED_TUNING_CONFIG=${PAPER_OVERLAY_JSON})"

# ------------------------------------------------------------
# 4) Wait for >=50 closed trades in overlay window
# ------------------------------------------------------------
log "Waiting for >=${MIN_CLOSED_TRADES} closed trades (overlay window)"
mkdir -p "${OVERLAY_DIR}"

while true; do
  python3 scripts/analysis/run_effectiveness_reports.py \
    --start "$(date -u +%Y-%m-%d)" \
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
  log "Overlay joined_count=${CLOSED}"
  if [ "${CLOSED}" -ge "${MIN_CLOSED_TRADES}" ]; then
    break
  fi
  sleep "${POLL_SECONDS}"
done

# ------------------------------------------------------------
# 5) Compare and decide LOCK/REVERT
# ------------------------------------------------------------
log "Comparing overlay vs baseline"
python3 scripts/analysis/compare_effectiveness_runs.py \
  --baseline "${BASELINE_DIR}" \
  --candidate "${OVERLAY_DIR}" \
  --out "${OUT_DIR}/lock_or_revert_decision.json" \
  --no_suppression \
  | tee -a "${LOG}"

# If REVERT, remove exit overlay so bot returns to default tuning
DECISION="$(python3 -c "
import json
j=json.load(open(\"${OUT_DIR}/lock_or_revert_decision.json\"))
print(j.get(\"decision\",\"\").upper())
" 2>/dev/null || echo "")"
if [ "${DECISION}" = "REVERT" ]; then
  if [ -f "/etc/systemd/system/stock-bot.service.d/exit-paper-overlay.conf" ]; then
    sudo rm /etc/systemd/system/stock-bot.service.d/exit-paper-overlay.conf
    sudo systemctl daemon-reload
    sudo systemctl restart stock-bot.service
    log "REVERT: removed exit overlay and restarted stock-bot"
  fi
fi

cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT AUTOPILOT COMPLETE

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

log "=== EXIT AUTOPILOT DONE ==="
echo "OUT_DIR: ${OUT_DIR}"
