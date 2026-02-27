#!/usr/bin/env bash
# CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
# Purpose:
# - Audit dashboard panels → real endpoints/files
# - Validate health checks, freshness, and failure modes
# - Produce governance-grade summary
# - Wire audit into daily EOD report (non-optional)
#
# Droplet only. No scoring or gate changes.
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_dashboard_truth_audit.log"
RUN_TAG="dashboard_truth_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/signal_review/dashboard_truth_${RUN_TAG}"
EXCERPTS="/tmp/cursor_dashboard_truth_excerpts_${RUN_TAG}"

EOD_SCRIPT="scripts/run_eod_confirmation.sh"
AUDIT_SCRIPT="scripts/run_dashboard_truth_audit.sh"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found: ${REPO}"

log "=== START dashboard truth audit ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Define dashboard panels and their truth sources
# -------------------------------------------------
# This is the contract. Panels must map to real sources.
# When TRUTH_USE_CTR=1 and STOCKBOT_TRUTH_ROOT is set, use CTR paths (Phase 2).
# Legacy: logs/expectancy_gate_truth.jsonl is canonical gate truth (contract may say gate_truth.jsonl as alias).
TRUTH_ROOT="${STOCKBOT_TRUTH_ROOT:-/var/lib/stock-bot/truth}"
if [ "${TRUTH_USE_CTR:-0}" = "1" ] && [ -d "${TRUTH_ROOT}" ]; then
  # Phase 2: contract points to CTR
  cat > "${EXCERPTS}/dashboard_contract.json" <<JSON
{
  "panels": [
    {"name": "Live Trades", "source": "journalctl:stock-bot.service", "evidence": "order_id|filled|submit_entry", "freshness_sec": 300},
    {"name": "Expectancy Gate Status", "source": "${TRUTH_ROOT}/gates/expectancy.jsonl", "evidence": "expectancy_gate", "freshness_sec": 300},
    {"name": "Signal Health", "source": "${TRUTH_ROOT}/health/signal_health.jsonl", "evidence": "has_data", "freshness_sec": 600},
    {"name": "Score Telemetry", "source": "${TRUTH_ROOT}/telemetry/score_telemetry.json", "evidence": "composite_exec_score", "freshness_sec": 600},
    {"name": "UW Cache", "source": "data/uw_flow_cache.json", "evidence": "symbol", "freshness_sec": 7200},
    {"name": "Exit Truth", "source": "${TRUTH_ROOT}/exits/exit_truth.jsonl", "evidence": "exit_pressure|decision", "freshness_sec": 600}
  ],
  "ctr_heartbeat": "${TRUTH_ROOT}/meta/last_write_heartbeat.json",
  "ctr_freshness": "${TRUTH_ROOT}/health/freshness.json"
}
JSON
else
  # Phase 1 / legacy: contract points to legacy paths (expectancy_gate_truth = gate truth)
  cat > "${EXCERPTS}/dashboard_contract.json" <<'JSON'
{
  "panels": [
    {"name": "Live Trades", "source": "journalctl:stock-bot.service", "evidence": "order_id|filled|submit_entry", "freshness_sec": 300},
    {"name": "Expectancy Gate Status", "source": "logs/expectancy_gate_truth.jsonl", "evidence": "expectancy_gate", "freshness_sec": 300},
    {"name": "Signal Health", "source": "logs/signal_health.jsonl", "evidence": "has_data", "freshness_sec": 600},
    {"name": "Score Telemetry", "source": "state/score_telemetry.json", "evidence": "composite_exec_score", "freshness_sec": 600},
    {"name": "UW Cache", "source": "data/uw_flow_cache.json", "evidence": "symbol", "freshness_sec": 7200},
    {"name": "Exit Truth", "source": "logs/exit_truth.jsonl", "evidence": "exit_pressure|decision", "freshness_sec": 600}
  ]
}
JSON
fi

# Copy contract to stable path for EOD (so daily EOD run has it)
cp "${EXCERPTS}/dashboard_contract.json" /tmp/dashboard_contract.json
log "Dashboard contract written to /tmp/dashboard_contract.json for EOD"

# -------------------------------------------------
# 2) Run the dashboard truth audit
# -------------------------------------------------
cat > "${AUDIT_SCRIPT}" <<'BASH'
#!/usr/bin/env bash
set -euo pipefail

CONTRACT="$1"
OUT_JSON="$2"
OUT_MD="$3"

# If contract missing (e.g. after reboot), write default so EOD can run
if [ ! -f "${CONTRACT}" ]; then
  mkdir -p "$(dirname "${CONTRACT}")"
  echo '{"panels":[{"name":"Live Trades","source":"journalctl:stock-bot.service","evidence":"order_id|filled|submit_entry","freshness_sec":300},{"name":"Expectancy Gate Status","source":"logs/gate_truth.jsonl","evidence":"expectancy_gate","freshness_sec":300},{"name":"Signal Health","source":"logs/signal_health.jsonl","evidence":"has_data","freshness_sec":600},{"name":"Score Telemetry","source":"state/score_telemetry.json","evidence":"composite_exec_score","freshness_sec":600},{"name":"UW Cache","source":"data/uw_flow_cache.json","evidence":"symbol","freshness_sec":7200},{"name":"Exit Truth","source":"logs/exit_truth.jsonl","evidence":"exit_pressure|decision","freshness_sec":600}]}' > "${CONTRACT}"
fi

now=$(date +%s)

jq -c '.panels[]' "${CONTRACT}" | while read -r panel; do
  name=$(echo "${panel}" | jq -r '.name')
  source=$(echo "${panel}" | jq -r '.source')
  evidence=$(echo "${panel}" | jq -r '.evidence')
  freshness=$(echo "${panel}" | jq -r '.freshness_sec')

  status="PASS"
  reason=""

  if [[ "${source}" == journalctl:* ]]; then
    svc="${source#journalctl:}"
    lines=$(journalctl -u "${svc}" --since "10 minutes ago" 2>/dev/null | grep -E "${evidence}" | wc -l || true)
    [ "${lines}" -gt 0 ] || { status="FAIL"; reason="no recent evidence in logs"; }
  else
    [ -f "${source}" ] || { status="FAIL"; reason="source missing"; }
    if [ "${status}" = "PASS" ]; then
      mtime=$(stat -c %Y "${source}")
      age=$((now - mtime))
      [ "${age}" -le "${freshness}" ] || { status="WARN"; reason="stale (${age}s)"; }
    fi
  fi

  jq -n \
    --arg name "${name}" \
    --arg source "${source}" \
    --arg status "${status}" \
    --arg reason "${reason}" \
    '{panel:$name, source:$source, status:$status, reason:$reason}'
done | jq -s '.' > "${OUT_JSON}"

# Markdown summary
{
  echo "# Dashboard Truth Audit"
  echo
  jq -r '.[] | "- **\(.panel)**: \(.status) (\(.source)) \(.reason)"' "${OUT_JSON}"
} > "${OUT_MD}"
BASH

chmod +x "${AUDIT_SCRIPT}"

# When using CTR, enforce heartbeat freshness (no silent inference)
CTR_HEARTBEAT=$(jq -r '.ctr_heartbeat // empty' "${EXCERPTS}/dashboard_contract.json")
if [ -n "${CTR_HEARTBEAT}" ] && [ -f "${CTR_HEARTBEAT}" ]; then
  CTR_MAX_AGE="${CTR_HEARTBEAT_MAX_AGE_SEC:-600}"
  NOW=$(date +%s)
  MTIME=$(stat -c %Y "${CTR_HEARTBEAT}" 2>/dev/null || echo "0")
  AGE=$((NOW - MTIME))
  if [ "${AGE}" -gt "${CTR_MAX_AGE}" ]; then
    log "ERROR: CTR heartbeat stale (${AGE}s > ${CTR_MAX_AGE}s). EOD fails. Set TRUTH_ROUTER_ENABLED=1 and ensure bot is writing to CTR."
    exit 1
  fi
  log "CTR heartbeat OK (age ${AGE}s)"
fi

log "Running dashboard truth audit"
bash "${AUDIT_SCRIPT}" \
  "${EXCERPTS}/dashboard_contract.json" \
  "${RUN_DIR}/dashboard_truth.json" \
  "${RUN_DIR}/dashboard_truth.md"

# -------------------------------------------------
# 3) Enforce wiring into daily EOD report
# -------------------------------------------------
log "Wiring dashboard truth audit into EOD"

if [ ! -f "${EOD_SCRIPT}" ]; then
  log "EOD script not found; creating ${EOD_SCRIPT} with dashboard truth audit"
  cat > "${EOD_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
# Daily EOD: dashboard truth audit (non-optional) then optional Python EOD.
# Run from repo root. Contract: /tmp/dashboard_contract.json (written by CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh)
set -euo pipefail
REPO="${REPO:-/root/stock-bot}"
cd "${REPO}" || exit 1

# --- Dashboard Truth Audit (non-optional) ---
bash scripts/run_dashboard_truth_audit.sh \
  /tmp/dashboard_contract.json \
  reports/signal_review/dashboard_truth_latest.json \
  reports/signal_review/dashboard_truth_latest.md
EOF
  chmod +x "${EOD_SCRIPT}"
  log "Created ${EOD_SCRIPT} with dashboard truth audit"
else
  if ! grep -q "run_dashboard_truth_audit.sh" "${EOD_SCRIPT}"; then
    cat >> "${EOD_SCRIPT}" <<'EOF'

# --- Dashboard Truth Audit (non-optional) ---
bash scripts/run_dashboard_truth_audit.sh \
  /tmp/dashboard_contract.json \
  reports/signal_review/dashboard_truth_latest.json \
  reports/signal_review/dashboard_truth_latest.md
EOF
    log "Dashboard truth audit appended to EOD script"
  else
    log "EOD script already includes dashboard truth audit"
  fi
fi

# -------------------------------------------------
# 4) Final copy/paste summary
# -------------------------------------------------
SUMMARY="${RUN_DIR}/cursor_final_summary.txt"

cat > "${SUMMARY}" <<EOF
RUN_TAG: ${RUN_TAG}
RUN_DIR: ${RUN_DIR}

DASHBOARD_TRUTH_AUDIT:
$(jq -r '.[] | "\(.panel): \(.status) \(.reason)"' "${RUN_DIR}/dashboard_truth.json")

EOD_WIRING: COMPLETE
AUDIT_SCRIPT: ${AUDIT_SCRIPT}
EOD_SCRIPT: ${EOD_SCRIPT}
LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: DASHBOARD_TRUTH_LOCKED"
echo "PR_BRANCH: NONE"

log "=== COMPLETE dashboard truth audit ==="
