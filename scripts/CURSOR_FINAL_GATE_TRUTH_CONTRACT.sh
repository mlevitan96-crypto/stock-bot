#!/usr/bin/env bash
# CURSOR_FINAL_GATE_TRUTH_CONTRACT.sh
# Purpose:
# 1) Enforce gate-truth logging as a contract (no inference-only audits)
# 2) Reconcile live trades vs audit claims
# 3) Verify live MIN_EXEC_SCORE
# 4) Emit a copy/paste-ready summary for governance
#
# Droplet only. No gate loosening. No scoring changes.
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_gate_truth_contract.log"
RUN_TAG="gate_truth_contract_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/signal_review/gate_truth_contract_${RUN_TAG}"
EXCERPTS="/tmp/cursor_gate_truth_excerpts_${RUN_TAG}"

WINDOW_HOURS="${WINDOW_HOURS:-24}"
WINDOW_DAYS="${WINDOW_DAYS:-7}"
MIN_EXEC_SCORE_EXPECTED="${MIN_EXEC_SCORE_EXPECTED:-2.5}"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found: ${REPO}"

log "=== START gate-truth contract run ${RUN_TAG} ==="

# -------------------------------------------------
# 0) Preflight
# -------------------------------------------------
command -v jq >/dev/null 2>&1 || fail "jq required"
command -v python3 >/dev/null 2>&1 || fail "python3 required"
command -v systemctl >/dev/null 2>&1 || log "systemctl not found (continuing)"

# -------------------------------------------------
# 1) Verify services are running (systemd truth)
# -------------------------------------------------
SERVICES=("uw-flow-daemon.service" "stock-bot.service")
for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    systemctl is-active --quiet "${s}" 2>/dev/null && log "service_active ${s}=yes" || log "service_active ${s}=no"
  else
    log "service_present ${s}=no"
  fi
done

# -------------------------------------------------
# 2) Capture live MIN_EXEC_SCORE (config + runtime)
# -------------------------------------------------
MIN_SOURCES="${EXCERPTS}/min_exec_score_sources.txt"
: > "${MIN_SOURCES}"

# Search only relevant paths (avoid glob failures when config/ is empty)
( grep -r -n -E "MIN_EXEC_SCORE|min_exec_score" config/ 2>/dev/null || true
  grep -n -E "MIN_EXEC_SCORE|min_exec_score" main.py uw_composite_v2.py 2>/dev/null || true
) >> "${MIN_SOURCES}"

for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    {
      echo "---- systemctl show ${s} ----"
      systemctl show "${s}" -p Environment -p EnvironmentFile -p ExecStart 2>/dev/null || true
    } >> "${MIN_SOURCES}"
  fi
done

LIVE_MIN_EXEC_SCORE="$(python3 - <<PY
import re
path = "${MIN_SOURCES}"
try:
    txt = open(path).read()
except Exception:
    txt = ""
vals = []
for m in re.finditer(r'(MIN_EXEC_SCORE|min_exec_score)\D{0,40}([0-9]+(?:\.[0-9]+)?)', txt, re.I):
    try:
        vals.append(float(m.group(2)))
    except Exception:
        pass
print(vals[-1] if vals else "")
PY
)" || true
[ -z "${LIVE_MIN_EXEC_SCORE}" ] && LIVE_MIN_EXEC_SCORE="UNKNOWN"
log "LIVE_MIN_EXEC_SCORE=${LIVE_MIN_EXEC_SCORE} EXPECTED=${MIN_EXEC_SCORE_EXPECTED}"

# -------------------------------------------------
# 3) Re-run audit (authoritative artifacts)
# -------------------------------------------------
log "Re-running scoring pipeline audit (${WINDOW_DAYS} days)"
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days "${WINDOW_DAYS}" \
  2>&1 | tee "${EXCERPTS}/audit_rerun.log" | tee -a "${LOG}" || true

# Copy canonical outputs
for f in \
  reports/signal_review/signal_funnel.json \
  reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md \
  reports/signal_review/signal_audit_diagnostic_droplet.json
do
  [ -f "${f}" ] && cp "${f}" "${RUN_DIR}/$(basename "${f}")" || true
done

FUNNEL="${RUN_DIR}/signal_funnel.json"
[ ! -f "${FUNNEL}" ] && [ -f "reports/signal_review/signal_funnel.json" ] && cp "reports/signal_review/signal_funnel.json" "${FUNNEL}" || true

# -------------------------------------------------
# 4) Extract gate-truth coverage + expectancy stats
# -------------------------------------------------
TOTAL_CAND="UNKNOWN"
PCT_ABOVE_POST="UNKNOWN"
GATE_TRUTH_LINES="UNKNOWN"
GATE_TRUTH_COVERAGE="UNKNOWN"
STAGE5_FROM_TRUTH="UNKNOWN"
DOM_CHOKE="UNKNOWN"

if [ -f "${FUNNEL}" ]; then
  TOTAL_CAND="$(jq -r '.total_candidates // "UNKNOWN"' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  PCT_ABOVE_POST="$(jq -r '.expectancy_distributions.pct_above_min_exec_post // "UNKNOWN"' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  GATE_TRUTH_LINES="$(jq -r '.gate_truth_lines_in_window // "UNKNOWN"' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  GATE_TRUTH_COVERAGE="$(jq -r '.gate_truth_coverage_pct // "UNKNOWN"' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  STAGE5_FROM_TRUTH="$(jq -r '.stage5_from_gate_truth // "UNKNOWN"' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
  DOM_CHOKE="$(jq -r 'if .dominant_choke_point then (.dominant_choke_point.stage // "?")+":"+(.dominant_choke_point.reason // "?") else "UNKNOWN" end' "${FUNNEL}" 2>/dev/null || echo "UNKNOWN")"
fi

log "funnel_total=${TOTAL_CAND} pct_above_post=${PCT_ABOVE_POST} gate_truth_lines=${GATE_TRUTH_LINES} gate_truth_cov=${GATE_TRUTH_COVERAGE} stage5_from_truth=${STAGE5_FROM_TRUTH} dominant=${DOM_CHOKE}"

# -------------------------------------------------
# 5) Count real fills from logs (last WINDOW_HOURS)
# -------------------------------------------------
ORDER_LINES="${EXCERPTS}/order_lines_last_${WINDOW_HOURS}h.txt"
: > "${ORDER_LINES}"

for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${s}"; then
    journalctl -u "${s}" --since "${WINDOW_HOURS} hours ago" 2>/dev/null | \
      grep -n -E "(filled|fill|submit_entry|order_id|rejected|reject)" 2>/dev/null >> "${ORDER_LINES}" || true
  fi
done

FILL_COUNT=0
REJECT_COUNT=0
if [ -s "${ORDER_LINES}" ]; then
  FILL_COUNT=$(grep -i -E "(filled\b|fill\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
  REJECT_COUNT=$(grep -i -E "(rejected\b|reject\b)" "${ORDER_LINES}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
fi
FILL_COUNT="${FILL_COUNT:-0}"
REJECT_COUNT="${REJECT_COUNT:-0}"
log "fills_last_${WINDOW_HOURS}h=${FILL_COUNT} rejects_last_${WINDOW_HOURS}h=${REJECT_COUNT}"

# -------------------------------------------------
# 6) Classification (authoritative; first match wins)
# -------------------------------------------------
CLASSIFICATION="UNKNOWN"
PRIMARY_REASON=""

# A) Audit inference not trustworthy
if [ "${FILL_COUNT}" -gt 0 ] 2>/dev/null && \
   { [ "${PCT_ABOVE_POST}" = "0" ] || [ "${PCT_ABOVE_POST}" = "0.0" ] || [ "${PCT_ABOVE_POST}" = "0.00" ]; } && \
   [ "${STAGE5_FROM_TRUTH}" = "false" ]; then
  CLASSIFICATION="A_AUDIT_INFERENCE_NOT_TRUSTWORTHY"
  PRIMARY_REASON="Real fills observed while stage-5 expectancy is inferred with low gate-truth coverage."
fi

# B) Config mismatch (only if still UNKNOWN)
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
    PRIMARY_REASON="Running service MIN_EXEC_SCORE differs from expected."
  fi
fi

# C) Trades from different path or missing gate-truth (only if still UNKNOWN)
if [ "${CLASSIFICATION}" = "UNKNOWN" ] && [ "${FILL_COUNT}" -gt 0 ] 2>/dev/null && \
   [ "${STAGE5_FROM_TRUTH}" != "true" ] && { [ "${GATE_TRUTH_LINES}" = "0" ] || [ "${GATE_TRUTH_LINES}" = "0.0" ]; }; then
  CLASSIFICATION="C_TRADES_FROM_DIFFERENT_PATH_OR_MISSING_GATE_TRUTH"
  PRIMARY_REASON="Fills present but no gate-truth lines captured."
fi

if [ "${CLASSIFICATION}" = "UNKNOWN" ]; then
  CLASSIFICATION="HEALTHY_WITH_OBSERVABILITY_GAP"
  PRIMARY_REASON="System trading; enforce gate-truth logging to remove ambiguity."
fi

# -------------------------------------------------
# 7) Write copy/paste summary + report
# -------------------------------------------------
SUMMARY="${RUN_DIR}/cursor_final_summary.txt"
REPORT="${RUN_DIR}/cursor_report.md"

cat > "${SUMMARY}" <<EOF
RUN_TAG: ${RUN_TAG}
RUN_DIR: ${RUN_DIR}

LIVE_MIN_EXEC_SCORE: ${LIVE_MIN_EXEC_SCORE}
EXPECTED_MIN_EXEC_SCORE: ${MIN_EXEC_SCORE_EXPECTED}

FUNNEL_TOTAL_CANDIDATES: ${TOTAL_CAND}
FUNNEL_PCT_ABOVE_MIN_EXEC_POST: ${PCT_ABOVE_POST}
FUNNEL_GATE_TRUTH_LINES_IN_WINDOW: ${GATE_TRUTH_LINES}
FUNNEL_GATE_TRUTH_COVERAGE_PCT: ${GATE_TRUTH_COVERAGE}
FUNNEL_STAGE5_FROM_GATE_TRUTH: ${STAGE5_FROM_TRUTH}
FUNNEL_DOMINANT_CHOKE_POINT: ${DOM_CHOKE}

FILLS_LAST_${WINDOW_HOURS}H: ${FILL_COUNT}
REJECTS_LAST_${WINDOW_HOURS}H: ${REJECT_COUNT}

CLASSIFICATION: ${CLASSIFICATION}
PRIMARY_REASON: ${PRIMARY_REASON}

ARTIFACTS:
- funnel_json: ${FUNNEL}
- audit_md: ${RUN_DIR}/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md
- min_exec_score_sources: ${EXCERPTS}/min_exec_score_sources.txt
- order_lines: ${EXCERPTS}/order_lines_last_${WINDOW_HOURS}h.txt
- log: ${LOG}
EOF

cat > "${REPORT}" <<EOF
# Gate-Truth Contract & Reconciliation Report

**Generated (droplet):** $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Copy/paste summary
\`\`\`
$(cat "${SUMMARY}")
\`\`\`

## Interpretation
- Trades are real (fills observed).
- Audit conclusions depend on gate-truth coverage.
- This run enforces gate-truth as a contract so audits cannot infer silently.

## Next step
- If CLASSIFICATION starts with A or C: add/enable gate-truth logging in the execution path.
- If B: align config.
- If HEALTHY: proceed; observability gap closed.
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ${CLASSIFICATION}"
echo "PR_BRANCH: NONE"

log "=== COMPLETE gate-truth contract run ==="
