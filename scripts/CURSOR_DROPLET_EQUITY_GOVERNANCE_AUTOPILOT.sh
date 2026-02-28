#!/usr/bin/env bash
# CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh
#
# ONLINE equity governance loop (live trades, 100-trade gate).
# Strategy: EQUITY ONLY. Stops when GLOBAL STOPPING CONDITION is met.
# DROPLET ONLY. PAPER ONLY.
#
# Cycle: A1 baseline -> A2 lever selection -> A3 apply overlay -> A4 wait 100 trades -> A5 compare -> A6 act.
# If stopping_condition_met after compare: write final summary and exit (no new levers).

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="equity_governance_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/equity_governance/${RUN_TAG}"
LOG="/tmp/equity_governance_autopilot.log"
mkdir -p "${OUT_DIR}"
: >> "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

# ---- Tunables
START_DATE_UTC="${START_DATE_UTC:-2026-02-01}"
END_DATE_UTC="${END_DATE_UTC:-$(date -u +%Y-%m-%d)}"
BASELINE_DIR="${BASELINE_DIR:-reports/effectiveness_baseline_blame}"
OVERLAY_DIR="${OVERLAY_DIR:-reports/effectiveness_overlay_check/${RUN_TAG}}"
MIN_CLOSED_TRADES="${MIN_CLOSED_TRADES:-100}"
POLL_SECONDS="${POLL_SECONDS:-120}"
ENTRY_SCORE_BUMP="${ENTRY_SCORE_BUMP:-0.2}"
EXIT_TWEAK_STRENGTH="${EXIT_TWEAK_STRENGTH:-0.03}"

log "=== EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ==="
log "OUT_DIR=${OUT_DIR} BASELINE_DIR=${BASELINE_DIR}"
log "MIN_CLOSED_TRADES=${MIN_CLOSED_TRADES}"

# ---- Preconditions
[ -f "scripts/analysis/run_effectiveness_reports.py" ] || { log "ERROR missing run_effectiveness_reports.py"; exit 2; }
[ -f "scripts/governance/generate_recommendation.py" ] || { log "ERROR missing generate_recommendation.py"; exit 2; }
[ -f "scripts/analysis/compare_effectiveness_runs.py" ] || { log "ERROR missing compare_effectiveness_runs.py"; exit 2; }
[ -f "scripts/ops/apply_paper_overlay.py" ] || { log "ERROR missing apply_paper_overlay.py"; exit 2; }

# ------------------------------------------------------------
# A1 — BASELINE (LIVE)
# ------------------------------------------------------------
log "A1 Baseline effectiveness (equity from logs) -> ${BASELINE_DIR}"
mkdir -p "${BASELINE_DIR}"

python3 scripts/analysis/run_effectiveness_reports.py \
  --start "${START_DATE_UTC}" \
  --end "${END_DATE_UTC}" \
  --out-dir "${BASELINE_DIR}" \
  | tee -a "${LOG}"

JOINED_COUNT="$(python3 -c "
import json, os
p=os.path.join('${BASELINE_DIR}','effectiveness_aggregates.json')
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get('joined_count',0))
")"
LOSING_TRADES="$(python3 -c "
import json, os
p=os.path.join('${BASELINE_DIR}','entry_vs_exit_blame.json')
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get('total_losing_trades',0))
")"

log "Baseline joined_count=${JOINED_COUNT} total_losing_trades=${LOSING_TRADES}"
if [ "${JOINED_COUNT}" -lt 30 ] || [ "${LOSING_TRADES}" -lt 5 ]; then
  log "ERROR: baseline insufficient (joined>=30, losing>=5). Fix attribution first."
  exit 3
fi

# A1.1 — Expectancy-gate diagnostic (additive; does not affect LOCK/REVERT)
python3 scripts/analysis/run_expectancy_gate_diagnostic.py \
  --start "${START_DATE_UTC}" --end "${END_DATE_UTC}" --base-dir "${REPO}" --out-dir "${BASELINE_DIR}" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# A2 — LEVER SELECTION (no-progress/alternation/force, else live vs replay)
# ------------------------------------------------------------
log "A2 Generating recommendation (entry vs exit)"
python3 scripts/governance/generate_recommendation.py \
  --effectiveness-dir "${BASELINE_DIR}" \
  --out "${OUT_DIR}/recommendation.json" \
  | tee -a "${LOG}"

if [ -n "${FORCE_LEVER:-}" ]; then
  LEVER="$(echo "${FORCE_LEVER}" | tr '[:upper:]' '[:lower:]')"
  log "FORCE_LEVER=${FORCE_LEVER} -> lever=${LEVER} (no-progress or alternation)"
else
  # Replay-driven comparison: live recommendation vs top ranked_candidates.json
  # Writes OUT_DIR/overlay_config.json and prints chosen lever (entry or exit)
  log "A2 Replay-driven lever selection (live vs top replay candidate)"
  LEVER="$(python3 scripts/governance/select_lever_with_replay.py \
    --recommendation "${OUT_DIR}/recommendation.json" \
    --baseline-dir "${BASELINE_DIR}" \
    --out-dir "${OUT_DIR}" \
    --run-tag "${RUN_TAG}" \
    --base-dir "${REPO}" 2>> "${LOG}" | tail -1)"
  if [ -z "${LEVER}" ]; then
    LEVER="$(python3 -c "import json; j=json.load(open('${OUT_DIR}/recommendation.json')); print((j.get('next_lever') or 'exit').lower())")"
    log "Fallback to live recommendation: lever=${LEVER}"
  fi
fi
log "Lever=${LEVER}"
if [ "${LEVER}" != "entry" ] && [ "${LEVER}" != "exit" ]; then
  log "ERROR: lever must be entry or exit. Got: ${LEVER}"
  exit 4
fi

# ------------------------------------------------------------
# A3 — APPLY ONE OVERLAY (replay stagnation, replay-driven choice, or live)
# ------------------------------------------------------------
if [ -n "${REPLAY_OVERLAY_CONFIG:-}" ] && [ -f "${REPLAY_OVERLAY_CONFIG}" ]; then
  cp "${REPLAY_OVERLAY_CONFIG}" "${OUT_DIR}/overlay_config.json"
  LEVER="$(python3 -c "import json; j=json.load(open('${OUT_DIR}/overlay_config.json')); print((j.get('lever') or 'exit').lower())")"
  log "A3 Using replay overlay (stagnation) from ${REPLAY_OVERLAY_CONFIG} -> lever=${LEVER}"
elif [ -f "${OUT_DIR}/overlay_config.json" ]; then
  LEVER="$(python3 -c "import json; j=json.load(open('${OUT_DIR}/overlay_config.json')); print((j.get('lever') or 'exit').lower())")"
  log "A3 Using overlay from replay-driven lever selection -> lever=${LEVER}"
else
  log "A3 Applying ONE overlay (${LEVER}) from recommendation"
  python3 - <<PY
import json, os
lever = "${LEVER}"
rec_path = "${OUT_DIR}/recommendation.json"
suggested = None
entry_lever_type = None
worst_signal_id = None
down_weight_delta = None
if __import__("os").path.exists(rec_path):
    try:
        r = json.load(open(rec_path))
        suggested = r.get("suggested_min_exec_score")
        entry_lever_type = r.get("entry_lever_type") or "min_exec_score"
        worst_signal_id = r.get("worst_signal_id")
        down_weight_delta = r.get("down_weight_delta")
    except Exception: pass
# Lever variety: use GOVERNANCE_ENTRY_THRESHOLD / GOVERNANCE_EXIT_STRENGTH from loop (rotation by cycle)
gov_entry = os.environ.get("GOVERNANCE_ENTRY_THRESHOLD")
gov_exit = os.environ.get("GOVERNANCE_EXIT_STRENGTH")
if lever == "entry":
    if entry_lever_type == "down_weight_signal" and worst_signal_id and down_weight_delta is not None:
        change = {"signal_weight_delta": {worst_signal_id: float(down_weight_delta)}}
    elif gov_entry:
        change = {"type": "entry_bump", "min_exec_score": float(gov_entry)}
    elif suggested is not None:
        change = {"type": "entry_bump", "min_exec_score": float(suggested)}
    else:
        change = {"type": "entry_bump", "delta": float("${ENTRY_SCORE_BUMP}")}
    cfg = {"run_tag": "${RUN_TAG}", "lever": "entry", "paper_only": True, "change": change}
else:
    strength = float(gov_exit) if gov_exit else float("${EXIT_TWEAK_STRENGTH}")
    cfg = {"run_tag": "${RUN_TAG}", "lever": "exit", "paper_only": True, "change": {"type": "single_exit_tweak", "strength": strength}}
with open("${OUT_DIR}/overlay_config.json", "w") as f:
  json.dump(cfg, f, indent=2)
print("WROTE", "${OUT_DIR}/overlay_config.json")
PY
fi

python3 scripts/ops/apply_paper_overlay.py \
  --overlay "${OUT_DIR}/overlay_config.json" \
  | tee -a "${LOG}"

# Activate overlay via systemd
if [ "${LEVER}" = "entry" ]; then
  MIN_SCORE="$(python3 -c "
import json
j=json.load(open('${OUT_DIR}/overlay_config.json'))
ch = j.get('change') or {}
if ch.get('min_exec_score') is not None:
    print(round(float(ch['min_exec_score']), 2))
elif ch.get('signal_weight_delta'):
    print('2.5')
else:
    delta = ch.get('delta', 0.2)
    print(round(2.5 + float(delta), 2))
")"
  DROPIN_DIR="/etc/systemd/system/stock-bot.service.d"
  sudo mkdir -p "${DROPIN_DIR}"
  echo "[Service]" | sudo tee "${DROPIN_DIR}/paper-overlay.conf"
  echo "Environment=MIN_EXEC_SCORE=${MIN_SCORE}" | sudo tee -a "${DROPIN_DIR}/paper-overlay.conf"
  sudo rm -f "${DROPIN_DIR}/exit-paper-overlay.conf"
elif [ "${LEVER}" = "exit" ]; then
  PAPER_OVERLAY_JSON="${REPO}/config/tuning/paper_overlay.json"
  DROPIN_DIR="/etc/systemd/system/stock-bot.service.d"
  sudo mkdir -p "${DROPIN_DIR}"
  echo "[Service]" | sudo tee "${DROPIN_DIR}/exit-paper-overlay.conf"
  echo "Environment=GOVERNED_TUNING_CONFIG=${PAPER_OVERLAY_JSON}" | sudo tee -a "${DROPIN_DIR}/exit-paper-overlay.conf"
fi
sudo systemctl daemon-reload
sudo systemctl restart stock-bot.service
log "A3 Restarted stock-bot with overlay active"

# ------------------------------------------------------------
# A4 — WAIT FOR >=100 CLOSED TRADES (overlay window)
# ------------------------------------------------------------
OVERLAY_START_DATE="$(date -u +%Y-%m-%d)"
log "A4 Waiting for >=${MIN_CLOSED_TRADES} closed trades (since ${OVERLAY_START_DATE})"
mkdir -p "${OVERLAY_DIR}"

while true; do
  python3 scripts/analysis/run_effectiveness_reports.py \
    --start "${OVERLAY_START_DATE}" \
    --end "$(date -u +%Y-%m-%d)" \
    --out-dir "${OVERLAY_DIR}" \
    > "${OVERLAY_DIR}/latest_effectiveness_run.txt" 2>&1 || true

  CLOSED="$(python3 -c "
import json, os
p=os.path.join('${OVERLAY_DIR}','effectiveness_aggregates.json')
j=json.load(open(p)) if os.path.exists(p) else {}
print(j.get('joined_count',0))
")"
  log "Overlay joined_count=${CLOSED}"
  if [ "${CLOSED}" -ge "${MIN_CLOSED_TRADES}" ]; then
    break
  fi
  sleep "${POLL_SECONDS}"
done

# ------------------------------------------------------------
# A5 — COMPARE (baseline vs overlay)
# ------------------------------------------------------------
log "A5 Comparing overlay vs baseline"
python3 scripts/analysis/compare_effectiveness_runs.py \
  --baseline "${BASELINE_DIR}" \
  --candidate "${OVERLAY_DIR}" \
  --out "${OUT_DIR}/lock_or_revert_decision.json" \
  | tee -a "${LOG}"

# ------------------------------------------------------------
# A6 — ACT: check stopping condition; LOCK/REVERT
# ------------------------------------------------------------
STOPPING_MET="$(python3 -c "
import json
j=json.load(open('${OUT_DIR}/lock_or_revert_decision.json'))
print(j.get('stopping_condition_met', False))
" 2>/dev/null || echo "False")"

if [ "${STOPPING_MET}" = "True" ]; then
  log "GLOBAL STOPPING CONDITION MET. Stopping improvement loop."
  cat > "${OUT_DIR}/GOVERNANCE_FINAL_SUMMARY.txt" <<EOF
EQUITY GOVERNANCE AUTOPILOT — STOPPING CONDITION MET

Last overlay run: ${OUT_DIR}
Baseline: ${BASELINE_DIR}
Overlay effectiveness: ${OVERLAY_DIR}
Decision: $(python3 -c "import json; j=json.load(open('${OUT_DIR}/lock_or_revert_decision.json')); print(j.get('decision',''))")

Stopping checks (all true):
- Expectancy > 0 over last ${MIN_CLOSED_TRADES} equity trades
- Win rate >= baseline + 2pp
- Giveback <= baseline + 0.05
- Attribution healthy (joined_count >= 100)

No new levers will be applied. Locked configuration remains active.
EOF
  log "Wrote ${OUT_DIR}/GOVERNANCE_FINAL_SUMMARY.txt"
  echo "OUT_DIR: ${OUT_DIR}"
  exit 0
fi

DECISION="$(python3 -c "
import json
j=json.load(open('${OUT_DIR}/lock_or_revert_decision.json'))
print(j.get('decision','').upper())
")"

if [ "${DECISION}" = "REVERT" ]; then
  log "A6 REVERT: removing overlay and restarting"
  sudo rm -f /etc/systemd/system/stock-bot.service.d/paper-overlay.conf
  sudo rm -f /etc/systemd/system/stock-bot.service.d/exit-paper-overlay.conf
  rm -f "${REPO}/state/path_to_profitability_overlay.json" "${REPO}/state/paper_overlay.env"
  sudo systemctl daemon-reload
  sudo systemctl restart stock-bot.service
  log "Rebuilding baseline for next cycle"
  python3 scripts/analysis/run_effectiveness_reports.py \
    --start "${START_DATE_UTC}" \
    --end "$(date -u +%Y-%m-%d)" \
    --out-dir "${BASELINE_DIR}" \
    | tee -a "${LOG}" || true
fi

# If LOCK: baseline for next cycle is this overlay; no removal. Next run will build baseline from logs (which include this overlay).
log "=== CYCLE DONE ==="
echo "OUT_DIR: ${OUT_DIR}"
