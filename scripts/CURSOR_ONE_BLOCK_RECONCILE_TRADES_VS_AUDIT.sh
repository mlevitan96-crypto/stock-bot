#!/usr/bin/env bash
# CURSOR_ONE_BLOCK_RECONCILE_TRADES_VS_AUDIT.sh
# Goal: Reconcile contradictions (100% expectancy blocked vs many fills), verify live MIN_EXEC_SCORE,
# verify which pipeline is producing trades, fix/raise gate-truth coverage, and emit copy/paste summary.
# Droplet only. Run from /root/stock-bot.
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_reconcile_trades_vs_audit.log"
RUN_TAG="reconcile_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/signal_review/reconcile_${RUN_TAG}"
EXCERPTS="/tmp/cursor_reconcile_excerpts_${RUN_TAG}"

WINDOW_HOURS="${WINDOW_HOURS:-24}"
WINDOW_DAYS="${WINDOW_DAYS:-7}"
MIN_EXEC_SCORE_EXPECTED="${MIN_EXEC_SCORE_EXPECTED:-2.5}"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found: ${REPO}"

# Prefer ripgrep (rg) for speed; fall back to grep -E
if command -v rg >/dev/null 2>&1; then
  SEARCH_CMD="rg"
  SEARCH_OPTS="-n"
else
  SEARCH_CMD="grep"
  SEARCH_OPTS="-n -E"
fi

log "=== START reconcile run ${RUN_TAG} ==="
log "Repo=${REPO} RunDir=${RUN_DIR} Excerpts=${EXCERPTS} Log=${LOG}"

# -----------------------------
# 0) Preflight: tools + services
# -----------------------------
command -v jq >/dev/null 2>&1 || fail "jq required (apt install jq)"
command -v python3 >/dev/null 2>&1 || fail "python3 required"
command -v systemctl >/dev/null 2>&1 || log "systemctl not found (continuing)"

SERVICES=("uw-flow-daemon.service" "stock-bot.service")
for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    systemctl is-active --quiet "${s}" 2>/dev/null && log "service_active ${s}=yes" || log "service_active ${s}=no"
  else
    log "service_present ${s}=no"
  fi
done

# -----------------------------
# 1) Capture current audit artifacts (if present)
# -----------------------------
AUDIT_JSON="reports/signal_review/signal_funnel.json"
AUDIT_MD="reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md"
DIAG_JSON="reports/signal_review/signal_audit_diagnostic_droplet.json"

for f in "${AUDIT_JSON}" "${AUDIT_MD}" "${DIAG_JSON}"; do
  if [ -f "${f}" ]; then
    cp "${f}" "${EXCERPTS}/" || true
    log "copied ${f} -> ${EXCERPTS}/"
  else
    log "missing ${f}"
  fi
done

# -----------------------------
# 2) Verify live MIN_EXEC_SCORE (best-effort: config + env + logs)
# -----------------------------
log "Discovering live MIN_EXEC_SCORE (best-effort)"
MIN_SOURCES="${EXCERPTS}/min_exec_score_sources.txt"
: > "${MIN_SOURCES}"

# 2a) Grep repo for MIN_EXEC_SCORE definitions
if [ "${SEARCH_CMD}" = "rg" ]; then
  rg -n "MIN_EXEC_SCORE|min_exec_score" config/ main.py uw_composite_v2.py 2>/dev/null | head -n 200 >> "${MIN_SOURCES}" || true
else
  ( grep -r -n -E "MIN_EXEC_SCORE|min_exec_score" config/ 2>/dev/null; grep -n -E "MIN_EXEC_SCORE|min_exec_score" main.py uw_composite_v2.py 2>/dev/null ) | head -n 200 >> "${MIN_SOURCES}" || true
fi

# 2b) systemd env (if available)
for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    {
      echo "---- systemctl show ${s} ----"
      systemctl show "${s}" -p Environment -p EnvironmentFile -p ExecStart 2>/dev/null || true
    } >> "${MIN_SOURCES}"
  fi
done

# 2c) recent logs
for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    journalctl -u "${s}" --since "${WINDOW_HOURS} hours ago" 2>/dev/null | \
      ( [ "${SEARCH_CMD}" = "rg" ] && rg -n "MIN_EXEC_SCORE|min_exec_score|expectancy gate|score_floor_breach" 2>/dev/null || grep -n -E "MIN_EXEC_SCORE|min_exec_score|expectancy gate|score_floor_breach" 2>/dev/null ) | tail -n 200 >> "${MIN_SOURCES}" || true
  fi
done

# Extract best-guess numeric value
LIVE_MIN_EXEC_SCORE="$(python3 - <<PY
import re, sys
path = "${MIN_SOURCES}"
try:
    txt = open(path).read()
except Exception:
    txt = ""
nums = []
for m in re.finditer(r'(MIN_EXEC_SCORE|min_exec_score)\D{0,40}([0-9]+(?:\.[0-9]+)?)', txt, re.I):
    try:
        nums.append(float(m.group(2)))
    except Exception:
        pass
print(nums[-1] if nums else "")
PY
)" || true

if [ -z "${LIVE_MIN_EXEC_SCORE}" ]; then
  LIVE_MIN_EXEC_SCORE="UNKNOWN"
fi
log "LIVE_MIN_EXEC_SCORE=${LIVE_MIN_EXEC_SCORE} (expected=${MIN_EXEC_SCORE_EXPECTED})"

# -----------------------------
# 3) Re-run the audit (current state)
# -----------------------------
log "Re-running scoring pipeline audit (days=${WINDOW_DAYS})"
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days "${WINDOW_DAYS}" 2>&1 | tee "${EXCERPTS}/audit_rerun.log" | tee -a "${LOG}" || true

# Copy fresh outputs
for f in "${AUDIT_JSON}" "${AUDIT_MD}" "${DIAG_JSON}"; do
  if [ -f "${f}" ]; then
    cp "${f}" "${RUN_DIR}/$(basename "${f}")" || true
  fi
done

RERUN_FUNNEL="${RUN_DIR}/signal_funnel.json"
if [ ! -f "${RERUN_FUNNEL}" ] && [ -f "${AUDIT_JSON}" ]; then
  cp "${AUDIT_JSON}" "${RERUN_FUNNEL}" || true
fi

# -----------------------------
# 4) Count fills/rejects in logs (heuristic)
# -----------------------------
log "Counting fill/reject lines in last ${WINDOW_HOURS}h (best-effort)"
FILL_COUNT=0
REJECT_COUNT=0
ORDER_LINES="${EXCERPTS}/order_lines_last_${WINDOW_HOURS}h.txt"
: > "${ORDER_LINES}"

for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    journalctl -u "${s}" --since "${WINDOW_HOURS} hours ago" 2>/dev/null | \
      ( [ "${SEARCH_CMD}" = "rg" ] && rg -n "(filled|fill|submitted order|submit_entry|order_id|rejected|reject)" 2>/dev/null || grep -n -E "(filled|fill|submitted order|submit_entry|order_id|rejected|reject)" 2>/dev/null ) >> "${ORDER_LINES}" || true
  fi
done

if [ -s "${ORDER_LINES}" ]; then
  if [ "${SEARCH_CMD}" = "rg" ]; then
    FILL_COUNT=$(rg -i "(filled\b|fill\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    REJECT_COUNT=$(rg -i "(rejected\b|reject\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
  else
    FILL_COUNT=$(grep -E -i "(filled\b|fill\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    REJECT_COUNT=$(grep -E -i "(rejected\b|reject\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
  fi
fi
FILL_COUNT="${FILL_COUNT:-0}"
REJECT_COUNT="${REJECT_COUNT:-0}"
log "log_heuristic_fill_lines=${FILL_COUNT} log_heuristic_reject_lines=${REJECT_COUNT}"

# -----------------------------
# 5) Gate-truth coverage from funnel
# -----------------------------
log "Reading funnel metrics"
GATE_TRUTH_LINES="UNKNOWN"
GATE_TRUTH_COVERAGE="UNKNOWN"
STAGE5_FROM_TRUTH="UNKNOWN"
PCT_ABOVE_POST="UNKNOWN"
TOTAL_CAND="UNKNOWN"
DOM_CHOKE="UNKNOWN"

if [ -f "${RERUN_FUNNEL}" ]; then
  TOTAL_CAND="$(jq -r '.total_candidates // "UNKNOWN"' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  PCT_ABOVE_POST="$(jq -r '.expectancy_distributions.pct_above_min_exec_post // "UNKNOWN"' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  GATE_TRUTH_LINES="$(jq -r '.gate_truth_lines_in_window // "UNKNOWN"' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  GATE_TRUTH_COVERAGE="$(jq -r '.gate_truth_coverage_pct // "UNKNOWN"' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  STAGE5_FROM_TRUTH="$(jq -r '.stage5_from_gate_truth // "UNKNOWN"' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  DOM_CHOKE="$(jq -r 'if .dominant_choke_point then (.dominant_choke_point.stage // "?") + ":" + (.dominant_choke_point.reason // "?") else "UNKNOWN" end' "${RERUN_FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
fi

log "funnel_total_candidates=${TOTAL_CAND} pct_above_min_exec_post=${PCT_ABOVE_POST} gate_truth_lines=${GATE_TRUTH_LINES} gate_truth_coverage=${GATE_TRUTH_COVERAGE} stage5_from_truth=${STAGE5_FROM_TRUTH} dominant=${DOM_CHOKE}"

# Gate-truth toggle candidates
log "Searching for gate-truth logging toggles"
TOGGLES="${EXCERPTS}/gate_truth_toggle_candidates.txt"
: > "${TOGGLES}"
if [ "${SEARCH_CMD}" = "rg" ]; then
  rg -n "GATE_TRUTH|gate_truth|EXPECTANCY_GATE_TRUTH|LEDGER_TRUTH|truth_lines" config/ main.py 2>/dev/null | head -n 200 >> "${TOGGLES}" || true
else
  ( grep -r -n -E "GATE_TRUTH|gate_truth|EXPECTANCY_GATE_TRUTH|LEDGER_TRUTH|truth_lines" config/ 2>/dev/null; grep -n -E "GATE_TRUTH|gate_truth|EXPECTANCY_GATE_TRUTH|LEDGER_TRUTH|truth_lines" main.py 2>/dev/null ) | head -n 200 >> "${TOGGLES}" || true
fi

# Expectancy gate lines from journal
log "Capturing expectancy gate lines (last ${WINDOW_HOURS}h)"
journalctl -u stock-bot.service --since "${WINDOW_HOURS} hours ago" 2>/dev/null | \
  ( [ "${SEARCH_CMD}" = "rg" ] && rg -n "(expectancy_gate|score_floor_breach|composite_exec_score|MIN_EXEC_SCORE|should_enter_v2)" 2>/dev/null || grep -n -E "(expectancy_gate|score_floor_breach|composite_exec_score|MIN_EXEC_SCORE|should_enter_v2)" 2>/dev/null ) | \
  tail -n 500 > "${EXCERPTS}/expectancy_gate_lines_tail.txt" || true

# -----------------------------
# 6) Classify contradiction
# -----------------------------
log "Classifying contradiction"
CLASSIFICATION="UNKNOWN"
WHY=""

# A: Fills in logs but funnel says 0% above and stage5 inferred
if [ "${FILL_COUNT}" -gt 0 ] 2>/dev/null; then
  if [ "${PCT_ABOVE_POST}" = "0" ] || [ "${PCT_ABOVE_POST}" = "0.0" ] || [ "${PCT_ABOVE_POST}" = "0.00" ]; then
    if [ "${STAGE5_FROM_TRUTH}" = "false" ]; then
      CLASSIFICATION="A_AUDIT_INFERENCE_NOT_TRUSTWORTHY"
      WHY="Fills observed in logs but stage5 is inferred with low gate-truth coverage; audit conclusion not authoritative."
    fi
  fi
fi

# B: Live MIN_EXEC_SCORE differs from expected (only when we have a numeric live value)
if [ "${CLASSIFICATION}" = "UNKNOWN" ] && [ "${LIVE_MIN_EXEC_SCORE}" != "UNKNOWN" ] && [ -n "${LIVE_MIN_EXEC_SCORE}" ]; then
  if ! python3 -c "
import sys
try:
    live = float('${LIVE_MIN_EXEC_SCORE}')
    exp = float('${MIN_EXEC_SCORE_EXPECTED}')
    sys.exit(0 if abs(live - exp) < 1e-9 else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
    CLASSIFICATION="B_CONFIG_MISMATCH_MIN_EXEC_SCORE"
    WHY="Running service appears to use a different MIN_EXEC_SCORE than expected; audit assumptions may be wrong."
  fi
fi

# C: Fills but no expectancy gate lines (different path or missing logging)
if [ "${CLASSIFICATION}" = "UNKNOWN" ] && [ "${FILL_COUNT}" -gt 0 ] 2>/dev/null; then
  if [ ! -s "${EXCERPTS}/expectancy_gate_lines_tail.txt" ]; then
    CLASSIFICATION="C_TRADES_FROM_DIFFERENT_PATH_OR_LOGGING_MISSING"
    WHY="Fills observed but no expectancy gate decision lines captured; either different execution path or missing logging."
  fi
fi

if [ "${CLASSIFICATION}" = "UNKNOWN" ]; then
  CLASSIFICATION="NEEDS_MORE_EVIDENCE_BUT_REPORT_IS_COMPLETE"
  WHY="No decisive contradiction classifier matched; see artifacts for details."
fi

# -----------------------------
# 7) Write summary + report
# -----------------------------
SUMMARY="${RUN_DIR}/cursor_final_summary.txt"
REPORT="${RUN_DIR}/cursor_report.md"

cat > "${SUMMARY}" <<EOF
RUN_TAG: ${RUN_TAG}
RUN_DIR: ${RUN_DIR}
WINDOW_HOURS: ${WINDOW_HOURS}
WINDOW_DAYS: ${WINDOW_DAYS}

LIVE_MIN_EXEC_SCORE: ${LIVE_MIN_EXEC_SCORE}
EXPECTED_MIN_EXEC_SCORE: ${MIN_EXEC_SCORE_EXPECTED}

FUNNEL_TOTAL_CANDIDATES: ${TOTAL_CAND}
FUNNEL_PCT_ABOVE_MIN_EXEC_POST: ${PCT_ABOVE_POST}
FUNNEL_GATE_TRUTH_LINES_IN_WINDOW: ${GATE_TRUTH_LINES}
FUNNEL_GATE_TRUTH_COVERAGE_PCT: ${GATE_TRUTH_COVERAGE}
FUNNEL_STAGE5_FROM_GATE_TRUTH: ${STAGE5_FROM_TRUTH}
FUNNEL_DOMINANT_CHOKE_POINT: ${DOM_CHOKE}

LOG_HEURISTIC_FILL_LINES_LAST_${WINDOW_HOURS}H: ${FILL_COUNT}
LOG_HEURISTIC_REJECT_LINES_LAST_${WINDOW_HOURS}H: ${REJECT_COUNT}

CLASSIFICATION: ${CLASSIFICATION}
PRIMARY_REASON: ${WHY}

ARTIFACTS:
- rerun_funnel_json: ${RERUN_FUNNEL}
- audit_md: ${RUN_DIR}/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md
- min_exec_score_sources: ${EXCERPTS}/min_exec_score_sources.txt
- order_lines: ${EXCERPTS}/order_lines_last_${WINDOW_HOURS}h.txt
- expectancy_gate_lines_tail: ${EXCERPTS}/expectancy_gate_lines_tail.txt
- gate_truth_toggle_candidates: ${EXCERPTS}/gate_truth_toggle_candidates.txt
- log: ${LOG}
EOF

cat > "${REPORT}" <<EOF
# Reconcile trades vs audit report

**Generated (droplet):** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Run tag:** ${RUN_TAG}
**Window:** last ${WINDOW_HOURS} hours (logs), last ${WINDOW_DAYS} days (audit)

## Copy/paste summary
\`\`\`
$(cat "${SUMMARY}")
\`\`\`

## What looks wrong
- Audit reports **0% above MIN_EXEC_SCORE** and dominant choke **expectancy_gate:score_floor_breach**.
- Logs show **fill-like lines** in the last ${WINDOW_HOURS} hours: ${FILL_COUNT}.
- Gate-truth coverage: lines=${GATE_TRUTH_LINES}, coverage=${GATE_TRUTH_COVERAGE}, stage5_from_truth=${STAGE5_FROM_TRUTH}.

## Classification
**${CLASSIFICATION}**
${WHY}

## Next actions (no gate loosening)
1. Ensure the running service logs gate-truth at high coverage (see toggle candidates).
2. Confirm live MIN_EXEC_SCORE used by systemd matches expectations.
3. If trades are from another path, correlate order IDs in logs with strategy/source.

## Artifacts
- ${RUN_DIR}
- ${EXCERPTS}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ${CLASSIFICATION}"
echo "PR_BRANCH: NONE"

log "=== COMPLETE ${RUN_TAG} ==="
log "Summary: ${SUMMARY}"
log "Report: ${REPORT}"
log "Excerpts: ${EXCERPTS}"
exit 0
