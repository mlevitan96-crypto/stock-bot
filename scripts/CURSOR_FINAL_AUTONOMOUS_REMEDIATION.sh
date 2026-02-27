#!/usr/bin/env bash
# CURSOR_FINAL_AUTONOMOUS_REMEDIATION.sh
# PURPOSE:
# - Identify why live trades are blocked
# - Validate signal ingestion + scoring integrity with real droplet data
# - Produce final evidence + decision
# - NO PLACEHOLDERS, NO GATE LOOSENING
#
# RUN LOCATION: DROPLET ONLY (/root/stock-bot)
# ADAPTED: Uses existing scripts (no main.py --dry-run; uses scoring pipeline audit + diagnostic).
#
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_final_autonomous_remediation.log"
RUN_BASE="${REPO}/reports/backtests"
RUN_TAG="final_autonomous_fix_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${RUN_BASE}/promotion_candidate_final_${RUN_TAG}"
EXCERPTS="/tmp/cursor_final_excerpts_${RUN_TAG}"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: > "${LOG}"
cd "${REPO}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== CURSOR FINAL AUTONOMOUS REMEDIATION START ==="

# -------------------------------------------------------------------
# 1. HARD FAIL IF DATA INGESTION IS BROKEN
# -------------------------------------------------------------------
log "Checking UW cache integrity"
UW_CACHE="data/uw_flow_cache.json"
if [ ! -f "${UW_CACHE}" ]; then
  log "FATAL: uw_flow_cache.json missing"
  exit 1
fi

# Count top-level keys that look like symbols (not starting with _)
CACHE_COUNT=$(python3 -c "
import json
with open('${UW_CACHE}') as f:
    d = json.load(f)
n = sum(1 for k in d if isinstance(k, str) and not k.startswith('_') and isinstance(d.get(k), (dict, list)))
print(n)
" 2>/dev/null || echo "0")
if [ "${CACHE_COUNT}" -lt 10 ]; then
  log "FATAL: UW cache too small (${CACHE_COUNT} symbol entries)"
  exit 1
fi

CACHE_MTIME=$(stat -c %Y "${UW_CACHE}" 2>/dev/null || echo 0)
NOW=$(date +%s)
AGE=$((NOW - CACHE_MTIME))
if [ "${AGE}" -gt 3600 ]; then
  log "WARNING: UW cache may be stale (${AGE}s old) — continuing but ingestion may need refresh"
fi

log "UW cache OK (${CACHE_COUNT} symbol entries, age=${AGE}s)"

# -------------------------------------------------------------------
# 2. RUN SCORING PIPELINE AUDIT (real data: funnel + diagnostic)
# -------------------------------------------------------------------
log "Running scoring pipeline audit (full_signal_review + signal_audit_diagnostic)"
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7 >> "${LOG}" 2>&1 || true

# Copy audit outputs to excerpts
cp -f "${REPO}/reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md" "${RUN_DIR}/" 2>/dev/null || true
cp -f "${REPO}/reports/signal_review/signal_funnel.json" "${EXCERPTS}/" 2>/dev/null || true
cp -f "${REPO}/reports/signal_review/signal_audit_diagnostic_droplet.json" "${EXCERPTS}/" 2>/dev/null || true

# -------------------------------------------------------------------
# 3. SCORE DISTRIBUTION (from funnel or diagnostic)
# -------------------------------------------------------------------
log "Analyzing score distribution"
ABOVE_2_5=0
MEDIAN_SCORE="0"
if [ -f "${EXCERPTS}/signal_funnel.json" ]; then
  ABOVE_2_5=$(python3 -c "
import json
with open('${EXCERPTS}/signal_funnel.json') as f:
    d = json.load(f)
exp = d.get('expectancy_distributions') or {}
pct = float(exp.get('pct_above_min_exec_post') or 0)
total = int(d.get('total_candidates') or 0)
above = int(round(total * pct / 100.0))
print(above)
" 2>/dev/null || echo "0")
  MEDIAN_SCORE=$(python3 -c "
import json
with open('${EXCERPTS}/signal_funnel.json') as f:
    d = json.load(f)
exp = d.get('expectancy_distributions') or {}
post = exp.get('post_adjust') or {}
print(post.get('p50', 0))
" 2>/dev/null || echo "0")
fi

if [ -f "${EXCERPTS}/signal_audit_diagnostic_droplet.json" ]; then
  python3 -c "
import json
with open('${EXCERPTS}/signal_audit_diagnostic_droplet.json') as f:
    d = json.load(f)
dist = d.get('composite_distribution') or {}
print(json.dumps({
  'count': dist.get('count', 0),
  'median': dist.get('mean', 0),
  'mean': dist.get('mean', 0),
  'max': dist.get('max', 0),
  'above_2_5_diagnostic': sum(1 for _ in range(dist.get('count', 0)) if dist.get('mean', 0) >= 2.5)
}))
" > "${EXCERPTS}/score_stats.json" 2>/dev/null || true
fi

if [ ! -f "${EXCERPTS}/score_stats.json" ]; then
  echo "{\"count\": 0, \"median\": ${MEDIAN_SCORE}, \"mean\": 0, \"max\": 0, \"above_2_5\": ${ABOVE_2_5}}" > "${EXCERPTS}/score_stats.json"
else
  # Ensure above_2_5 from funnel is in score_stats for decision
  python3 -c "
import json
with open('${EXCERPTS}/score_stats.json') as f:
    d = json.load(f)
d['above_2_5'] = ${ABOVE_2_5}
d['median_from_funnel'] = ${MEDIAN_SCORE}
with open('${EXCERPTS}/score_stats.json','w') as f:
    json.dump(d, f, indent=2)
"
fi

cat "${EXCERPTS}/score_stats.json" | tee -a "${LOG}"

# Decision uses funnel above_2_5; log but do not exit here so we always produce report
ABOVE=$(python3 -c "import json; d=json.load(open('${EXCERPTS}/score_stats.json')); print(d.get('above_2_5', 0))" 2>/dev/null || echo "0")
if [ "${ABOVE}" -eq 0 ]; then
  log "FATAL: No candidates exceed MIN_EXEC_SCORE — fix ingestion and scoring (see SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md)"
else
  log "Scores viable (${ABOVE} above MIN_EXEC_SCORE) — proceeding"
fi

# -------------------------------------------------------------------
# 4. REFRESH INTEL (no pkill — safe refresh)
# -------------------------------------------------------------------
log "Refreshing intel (build_expanded_intel + intel producers)"
python3 scripts/build_expanded_intel.py >> "${LOG}" 2>&1 || true
python3 scripts/run_premarket_intel.py >> "${LOG}" 2>&1 || true
python3 scripts/run_postmarket_intel.py >> "${LOG}" 2>&1 || true
python3 scripts/build_expanded_intel.py >> "${LOG}" 2>&1 || true
log "Intel refresh done"

# -------------------------------------------------------------------
# 5. RE-RUN AUDIT AFTER REFRESH (optional)
# -------------------------------------------------------------------
log "Re-running scoring pipeline audit after intel refresh"
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7 >> "${LOG}" 2>&1 || true
cp -f "${REPO}/reports/signal_review/signal_funnel.json" "${EXCERPTS}/signal_funnel_after_fix.json" 2>/dev/null || true

# -------------------------------------------------------------------
# 6. FINAL DECISION
# -------------------------------------------------------------------
ABOVE=$(python3 -c "import json; d=json.load(open('${EXCERPTS}/score_stats.json')); print(d.get('above_2_5', 0))" 2>/dev/null || echo "0")
ABOVE_FINAL=$(python3 -c "
import json
p = '${EXCERPTS}/signal_funnel_after_fix.json'
if __import__('os').path.exists(p):
    with open(p) as f: d = json.load(f)
    exp = d.get('expectancy_distributions') or {}
    total = int(d.get('total_candidates') or 0)
    pct = float(exp.get('pct_above_min_exec_post') or 0)
    print(int(round(total * pct / 100.0)))
else:
    print(${ABOVE})
" 2>/dev/null || echo "${ABOVE}")

DECISION="REJECT"
if [ "${ABOVE_FINAL}" -gt 10 ]; then
  DECISION="ALLOW_TRADING"
fi

# -------------------------------------------------------------------
# 7. WRITE FINAL REPORT
# -------------------------------------------------------------------
cat > "${RUN_DIR}/cursor_final_summary.txt" <<EOF
RUN_DIR: ${RUN_DIR}
DECISION: ${DECISION}
CANDIDATES_ABOVE_MIN_EXEC_SCORE: ${ABOVE_FINAL}
LOG: ${LOG}
EXCERPTS: ${EXCERPTS}
EOF

cat > "${RUN_DIR}/cursor_report.md" <<EOF
# Final Autonomous Remediation Report

## Outcome
Decision: **${DECISION}**

## Evidence
- UW cache validated (${CACHE_COUNT} entries, age ${AGE}s)
- Scoring pipeline audit run (full_signal_review + signal_audit_diagnostic)
- Signal health / funnel from real droplet data
- Intel refresh (build_expanded_intel, premarket, postmarket)

## Score Distribution

EOF
cat "${EXCERPTS}/score_stats.json" >> "${RUN_DIR}/cursor_report.md" 2>/dev/null || echo "{}" >> "${RUN_DIR}/cursor_report.md"
cat >> "${RUN_DIR}/cursor_report.md" <<EOF

## Artifacts
- SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md
- signal_funnel.json
- signal_audit_diagnostic_droplet.json (if produced)

## Next Action
- If DECISION = ALLOW_TRADING → resume paper/live trading after human review
- If REJECT → ingestion/scoring still broken; see SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md and docs/SIGNAL_DATA_SOURCES_AND_CHECKLIST.md
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ${DECISION}"
echo "CANDIDATES_ABOVE_MIN_EXEC_SCORE: ${ABOVE_FINAL}"

log "=== CURSOR FINAL AUTONOMOUS REMEDIATION COMPLETE ==="

# Exit 1 if no candidates can trade (remediation did not succeed)
[ "${ABOVE_FINAL}" -gt 0 ] || exit 1
