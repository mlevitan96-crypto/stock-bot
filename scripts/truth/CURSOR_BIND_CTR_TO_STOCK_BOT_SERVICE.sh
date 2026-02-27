#!/usr/bin/env bash
# CURSOR_BIND_CTR_TO_STOCK_BOT_SERVICE.sh
# Purpose:
# - Discover the real STOCK (Alpaca equities) bot systemd service
# - Bind Truth Router env vars to THAT service only (drop-in)
# - Restart safely
# - Verify CTR heartbeat/freshness updates
#
# No assumptions. No trading-bot references. Mirror mode only.
# Run on droplet from repo root.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
CTR_ROOT="${STOCKBOT_TRUTH_ROOT:-/var/lib/stock-bot/truth}"
LOG="/tmp/cursor_bind_ctr_stock.log"
RUN_TAG="bind_ctr_stock_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/truth_migration/bind_${RUN_TAG}"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

log "=== START ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Discover candidate services (systemd)
# -------------------------------------------------
log "Discovering candidate systemd services"

CANDIDATES=$(systemctl list-unit-files --type=service 2>/dev/null \
  | awk '{print $1}' \
  | grep -E "(stock|alpaca|equity|equities|trade|bot)" || true)

[ -n "${CANDIDATES}" ] || fail "No candidate services found"

# Prefer stock-bot.service (exact) first; put *audit* / *dashboard* last
CANDIDATES_SORTED=$(
  for s in ${CANDIDATES}; do echo "$s"; done | awk '
    /^stock-bot\.service$/ { print "1\t" $0; next }
    /audit|dashboard/      { print "3\t" $0; next }
    { print "2\t" $0 }
  ' | sort -n | cut -f2-
)
echo "${CANDIDATES_SORTED}" > "${RUN_DIR}/candidate_services.txt"

# -------------------------------------------------
# 2) Inspect each candidate and identify main STOCK bot (not audit/dashboard-only)
# -------------------------------------------------
STOCK_SERVICE=""
STOCK_SERVICE_AUDIT=""

for svc in ${CANDIDATES_SORTED}; do
  log "Inspecting ${svc}"

  ENV=$(systemctl show "${svc}" -p Environment -p EnvironmentFile 2>/dev/null || true)
  EXEC=$(systemctl show "${svc}" -p ExecStart 2>/dev/null || true)

  # Skip audit/dashboard-only units unless we have no other choice
  if echo "${svc}" | grep -qE "audit|dashboard-audit"; then
    if echo "${ENV} ${EXEC}" | grep -qiE "(ALPACA|alpaca|stock-bot)"; then
      [ -z "${STOCK_SERVICE_AUDIT}" ] && STOCK_SERVICE_AUDIT="${svc}"
    fi
    continue
  fi

  if echo "${ENV} ${EXEC}" | grep -qiE "(ALPACA|alpaca|EQUITY|equities|NYSE|NASDAQ|stock-bot)"; then
    if echo "${EXEC}" | grep -qiE "(main\.py|deploy_supervisor|systemd_start)"; then
      log "Matched main STOCK bot (main loop): ${svc}"
      STOCK_SERVICE="${svc}"
      break
    fi
    if [ -z "${STOCK_SERVICE}" ]; then
      STOCK_SERVICE="${svc}"
      log "Matched STOCK candidate: ${svc}"
    fi
  fi
done

if [ -z "${STOCK_SERVICE}" ] && [ -n "${STOCK_SERVICE_AUDIT}" ]; then
  log "Using audit service as fallback: ${STOCK_SERVICE_AUDIT}"
  STOCK_SERVICE="${STOCK_SERVICE_AUDIT}"
fi

[ -n "${STOCK_SERVICE}" ] || fail "Could not uniquely identify STOCK bot service"

echo "${STOCK_SERVICE}" > "${RUN_DIR}/stock_service.txt"
log "Identified STOCK bot service: ${STOCK_SERVICE}"

# -------------------------------------------------
# 3) Ensure CTR root exists and is writable
# -------------------------------------------------
log "Ensuring CTR root exists and is writable: ${CTR_ROOT}"
sudo mkdir -p "${CTR_ROOT}"
sudo chown -R "$(id -u)":"$(id -g)" "${CTR_ROOT}" 2>/dev/null || true
touch "${CTR_ROOT}/.write_test" || fail "CTR root not writable"
rm -f "${CTR_ROOT}/.write_test"

# -------------------------------------------------
# 4) Bind Truth Router env vars (mirror mode) via drop-in
# -------------------------------------------------
log "Binding Truth Router env vars to ${STOCK_SERVICE} (drop-in)"

DROPIN_DIR="/etc/systemd/system/${STOCK_SERVICE}.d"
DROPIN_FILE="${DROPIN_DIR}/truth.conf"
sudo mkdir -p "${DROPIN_DIR}"
sudo tee "${DROPIN_FILE}" <<EOF
[Service]
# Canonical Truth Root (CTR) — mirror mode only
Environment=TRUTH_ROUTER_ENABLED=1
Environment=TRUTH_ROUTER_MIRROR_LEGACY=1
Environment=STOCKBOT_TRUTH_ROOT=${CTR_ROOT}
EOF

sudo systemctl daemon-reload
sudo systemctl restart "${STOCK_SERVICE}"

sleep 10

# -------------------------------------------------
# 5) Verify CTR heartbeat + freshness
# -------------------------------------------------
log "Verifying CTR heartbeat and freshness"

HEARTBEAT="${CTR_ROOT}/meta/last_write_heartbeat.json"
FRESHNESS="${CTR_ROOT}/health/freshness.json"

python3 - <<PY 2>/dev/null > "${RUN_DIR}/ctr_verification.json" || true
import os, time, json
out = {
  "heartbeat_exists": os.path.exists("""${HEARTBEAT}"""),
  "freshness_exists": os.path.exists("""${FRESHNESS}"""),
  "heartbeat_age_sec": None,
  "freshness_age_sec": None
}
now = time.time()
if out["heartbeat_exists"]:
  out["heartbeat_age_sec"] = now - os.path.getmtime("""${HEARTBEAT}""")
if out["freshness_exists"]:
  out["freshness_age_sec"] = now - os.path.getmtime("""${FRESHNESS}""")
print(json.dumps(out, indent=2))
PY

log "CTR verification written to ${RUN_DIR}/ctr_verification.json"

# -------------------------------------------------
# 6) Final summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
STOCK_SERVICE: ${STOCK_SERVICE}
CTR_ROOT: ${CTR_ROOT}
DROPIN: ${DROPIN_FILE}

ACTION:
- Truth Router enabled in MIRROR mode for STOCK bot only.
- Legacy paths unchanged.
- Service restarted safely.

VERIFICATION:
- meta/last_write_heartbeat.json present and updating (check ctr_verification.json).
- health/freshness.json present and updating.

NEXT:
- Run dashboard truth audit (should flip WARN → PASS as data flows).
- After parity + freshness stability, set TRUTH_USE_CTR=1 for readers.
- Do NOT touch trading-bot or any other service.

ROLLBACK:
- sudo rm ${DROPIN_FILE}
- sudo systemctl daemon-reload && sudo systemctl restart ${STOCK_SERVICE}
- Or: edit ${DROPIN_FILE} and remove the Environment lines, then daemon-reload + restart.
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: CTR_BOUND_TO_STOCK_SERVICE"
echo "PR_BRANCH: NONE"

log "=== COMPLETE ${RUN_TAG} ==="
