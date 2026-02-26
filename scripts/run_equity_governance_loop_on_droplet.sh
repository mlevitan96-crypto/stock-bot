#!/usr/bin/env bash
# Run equity governance autopilot in a loop until GLOBAL STOPPING CONDITION is met.
# Implements: (1) Alternation — even cycle = FORCE_LEVER=exit, odd = recommender.
#             (2) No-progress rule — after LOCK, if expectancy didn't improve, next cycle force other lever.
# State: state/equity_governance_loop_state.json
# Log: /tmp/equity_governance_autopilot.log

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
STATE_FILE="${REPO}/state/equity_governance_loop_state.json"
cd "${REPO}" || exit 1

mkdir -p "${REPO}/state"

# Initialize state if missing
if [ ! -f "${STATE_FILE}" ]; then
  echo '{"last_lever":"","last_candidate_expectancy":null,"prev_candidate_expectancy":null,"last_decision":""}' > "${STATE_FILE}"
fi

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] === GOVERNANCE CYCLE ${CYCLE} ===" | tee -a /tmp/equity_governance_autopilot.log

  # Read state for no-progress and alternation
  LAST_LEVER="$(python3 -c "
import json
j=json.load(open('${STATE_FILE}'))
print(j.get('last_lever',''))
" 2>/dev/null || echo "")"
  LAST_EXP="$(python3 -c "
import json
j=json.load(open('${STATE_FILE}'))
e=j.get('last_candidate_expectancy')
print(e if e is not None else '')
" 2>/dev/null || echo "")"
  PREV_EXP="$(python3 -c "
import json
j=json.load(open('${STATE_FILE}'))
e=j.get('prev_candidate_expectancy')
print(e if e is not None else '')
" 2>/dev/null || echo "")"
  LAST_DECISION="$(python3 -c "
import json
j=json.load(open('${STATE_FILE}'))
print(j.get('last_decision',''))
" 2>/dev/null || echo "")"

  # Decide FORCE_LEVER for this cycle
  FORCE_LEVER=""
  # (1) No-progress rule: last cycle was LOCK and expectancy did not improve -> force other lever
  if [ "${LAST_DECISION}" = "LOCK" ] && [ -n "${LAST_EXP}" ] && [ -n "${PREV_EXP}" ]; then
    IMPROVED="$(python3 -c "
try:
  last=float('${LAST_EXP}')
  prev=float('${PREV_EXP}')
  print('yes' if last > prev else 'no')
except Exception:
  print('no')
" 2>/dev/null || echo "no")"
    if [ "${IMPROVED}" = "no" ]; then
      if [ "${LAST_LEVER}" = "entry" ]; then FORCE_LEVER="exit"; else FORCE_LEVER="entry"; fi
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] No-progress: forcing other lever FORCE_LEVER=${FORCE_LEVER}" | tee -a /tmp/equity_governance_autopilot.log
    fi
  fi
  # (2) Alternation: even cycle = force exit (so we test exit every other cycle)
  if [ -z "${FORCE_LEVER}" ] && [ $((CYCLE % 2)) -eq 0 ]; then
    FORCE_LEVER="exit"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Alternation: even cycle -> FORCE_LEVER=exit" | tee -a /tmp/equity_governance_autopilot.log
  fi

  export FORCE_LEVER
  if [ -n "${FORCE_LEVER}" ]; then
    export FORCE_LEVER
  else
    unset FORCE_LEVER
  fi

  if ! bash scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Autopilot script failed. Exiting loop."
    exit 1
  fi

  # Update state from last run
  LAST_OUT="$(ls -td reports/equity_governance/equity_governance_* 2>/dev/null | head -1)"
  if [ -n "${LAST_OUT}" ] && [ -f "${LAST_OUT}/lock_or_revert_decision.json" ]; then
    python3 -c "
import json
dec=json.load(open('${LAST_OUT}/lock_or_revert_decision.json'))
cand=dec.get('candidate',{})
lev=None
if __import__('os').path.exists('${LAST_OUT}/overlay_config.json'):
    try:
        oc=json.load(open('${LAST_OUT}/overlay_config.json'))
        lev=oc.get('lever')
    except Exception: pass
if lev is None and __import__('os').path.exists('${LAST_OUT}/recommendation.json'):
    try:
        r=json.load(open('${LAST_OUT}/recommendation.json'))
        lev=r.get('next_lever')
    except Exception: pass
state_path='${STATE_FILE}'
try:
    s=json.load(open(state_path))
except Exception:
    s={}
s['prev_candidate_expectancy']=s.get('last_candidate_expectancy')
s['last_candidate_expectancy']=cand.get('expectancy_per_trade')
s['last_decision']=dec.get('decision','')
s['last_lever']=lev or s.get('last_lever','')
with open(state_path,'w') as f:
    json.dump(s,f,indent=2)
" 2>/dev/null || true
  fi

  # Check stopping condition
  if [ -n "${LAST_OUT}" ] && [ -f "${LAST_OUT}/lock_or_revert_decision.json" ]; then
    STOPPING="$(python3 -c "
import json
j=json.load(open('${LAST_OUT}/lock_or_revert_decision.json'))
print(j.get('stopping_condition_met', False))
" 2>/dev/null || echo "False")"
    if [ "${STOPPING}" = "True" ]; then
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stopping condition met. Exiting loop."
      exit 0
    fi
  fi

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Next cycle in 60s..."
  sleep 60
done
