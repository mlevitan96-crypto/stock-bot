#!/usr/bin/env bash
# Run equity governance autopilot in a loop until GLOBAL STOPPING CONDITION is met.
# Implements: (1) Alternation — even cycle = FORCE_LEVER=exit, odd = recommender.
#             (2) No-progress rule — after LOCK, if expectancy didn't improve, next cycle force other lever.
#             (3) Multi-cycle stagnation -> replay-driven jump (optional).
# State: state/equity_governance_loop_state.json
# Log: /tmp/equity_governance_autopilot.log

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
STATE_FILE="${REPO}/state/equity_governance_loop_state.json"
REPLAY_OVERLAY_PATH="${REPO}/state/replay_overlay_config.json"
EXPECTANCY_HISTORY_N=5
STAGNATION_CYCLES=3
STAGNATION_EPSILON=0.012
REPLAY_JUMP_COOLDOWN=2

cd "${REPO}" || exit 1

mkdir -p "${REPO}/state"

# Initialize state if missing
if [ ! -f "${STATE_FILE}" ]; then
  python3 -c "
import json
json.dump({
  'last_lever':'','last_candidate_expectancy':None,'prev_candidate_expectancy':None,'last_decision':'',
  'expectancy_history':[],'last_replay_jump_cycle':0
}, open('${STATE_FILE}','w'), indent=2)
"
fi

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] === GOVERNANCE CYCLE ${CYCLE} ===" | tee -a /tmp/equity_governance_autopilot.log

  # Read state for no-progress, alternation, stagnation
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

  # Ensure state has multi-cycle fields (migrate old state)
  python3 -c "
import json
p='${STATE_FILE}'
try:
  s=json.load(open(p))
except Exception:
  s={}
if 'expectancy_history' not in s: s['expectancy_history']=[]
if 'last_replay_jump_cycle' not in s: s['last_replay_jump_cycle']=0
with open(p,'w') as f: json.dump(s,f,indent=2)
" 2>/dev/null || true

  # Stagnation: last N LOCK expectancies flat or no improvement -> replay jump (optional)
  REPLAY_OVERLAY_CONFIG=""
  USED_REPLAY=0
  STAGNANT="$(python3 -c "
import json
j=json.load(open('${STATE_FILE}'))
hist = j.get('expectancy_history') or []
last_jump = int(j.get('last_replay_jump_cycle') or 0)
cycle = ${CYCLE}
# Need at least ${STAGNATION_CYCLES} LOCK-cycle expectancies
if len(hist) < ${STAGNATION_CYCLES}:
  print('0')
  exit(0)
last_n = hist[-${STAGNATION_CYCLES}:]
mn, mx = min(last_n), max(last_n)
# Stagnant if range < epsilon
if (mx - mn) >= ${STAGNATION_EPSILON}:
  print('0')
  exit(0)
# Cooldown: don't jump every cycle
if (cycle - last_jump) < ${REPLAY_JUMP_COOLDOWN}:
  print('0')
  exit(0)
print('1')
" 2>/dev/null || echo "0")"
  if [ "${STAGNANT}" = "1" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stagnation detected -> running replay campaign and using top replay lever" | tee -a /tmp/equity_governance_autopilot.log
    if python3 scripts/replay/run_equity_replay_campaign.py 2>>/tmp/equity_governance_autopilot.log; then
      LATEST_CAMPAIGN="$(ls -td reports/replay/equity_replay_campaign_* 2>/dev/null | head -1)"
      if [ -n "${LATEST_CAMPAIGN}" ] && [ -f "${LATEST_CAMPAIGN}/campaign_results.json" ]; then
        if python3 scripts/governance/select_lever_from_replay.py --campaign-dir "${LATEST_CAMPAIGN}" --out "${REPLAY_OVERLAY_PATH}" 2>>/tmp/equity_governance_autopilot.log; then
          export REPLAY_OVERLAY_CONFIG="${REPLAY_OVERLAY_PATH}"
          USED_REPLAY=1
          echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Replay overlay written to ${REPLAY_OVERLAY_PATH}" | tee -a /tmp/equity_governance_autopilot.log
        fi
      fi
    fi
  fi

  # Decide FORCE_LEVER for this cycle (only when not using replay overlay)
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

  # Update state from last run (expectancy_history, last_replay_jump_cycle)
  LAST_OUT="$(ls -td reports/equity_governance/equity_governance_* 2>/dev/null | head -1)"
  export CYCLE USED_REPLAY
  if [ -n "${LAST_OUT}" ] && [ -f "${LAST_OUT}/lock_or_revert_decision.json" ]; then
    python3 -c "
import json, os
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
s.setdefault('expectancy_history', [])
s.setdefault('last_replay_jump_cycle', 0)
s['prev_candidate_expectancy']=s.get('last_candidate_expectancy')
s['last_candidate_expectancy']=cand.get('expectancy_per_trade')
s['last_decision']=dec.get('decision','')
s['last_lever']=lev or s.get('last_lever','')
# On LOCK, append expectancy to history (keep last ${EXPECTANCY_HISTORY_N})
if dec.get('decision') == 'LOCK' and cand.get('expectancy_per_trade') is not None:
    s['expectancy_history'] = (s['expectancy_history'] + [float(cand['expectancy_per_trade'])])[-${EXPECTANCY_HISTORY_N}:]
if int(os.environ.get('USED_REPLAY','0')) == 1:
    s['last_replay_jump_cycle'] = int(os.environ.get('CYCLE','0'))
with open(state_path,'w') as f:
    json.dump(s,f,indent=2)
" 2>/dev/null || true
  fi
  unset REPLAY_OVERLAY_CONFIG 2>/dev/null || true

  # Board and persona review (additive; live on droplet)
  python3 scripts/governance/run_board_persona_review.py --base-dir "${REPO}" --out-dir "${REPO}/reports/governance" | tee -a /tmp/equity_governance_autopilot.log || true

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
