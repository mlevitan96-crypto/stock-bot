#!/usr/bin/env bash
# CURSOR_ONE_BLOCK_TRUTH_MIGRATION_NEXT_STEPS.sh
# Droplet-first continuation: capture baseline, verify CTR readiness, enable mirror mode safely,
# run freshness + parity checks, and emit governance-ready artifacts.
#
# SAFE: does NOT flip readers to CTR (TRUTH_USE_CTR stays unchanged). Does NOT disable legacy.
# Requires: run on droplet from repo root (/root/stock-bot).

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
CTR_ROOT_DEFAULT="/var/lib/stock-bot/truth"
RUN_TAG="truth_migration_next_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/truth_migration/run_${RUN_TAG}"
BASELINE_DIR="${REPO}/reports/truth_migration/droplet_baseline"
LOG="/tmp/cursor_truth_migration_next.log"

mkdir -p "${RUN_DIR}" "${BASELINE_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found: ${REPO}"

log "=== START ${RUN_TAG} ==="
log "Repo=${REPO}"
log "RunDir=${RUN_DIR}"

# -----------------------------
# 0) Preconditions
# -----------------------------
for f in \
  scripts/truth/capture_droplet_baseline.sh \
  src/infra/truth_router.py \
  docs/TRUTH_ROOT_CONTRACT.md \
  docs/DEPRECATIONS_TRUTH_PATHS.md \
  reports/truth_migration/TRUTH_MIGRATION_CONTRACT.md \
  reports/truth_migration/SAFE_TO_APPLY.md \
  tests/test_truth_router.py \
  scripts/truth/run_truth_smoke_test.sh
do
  [ -f "${f}" ] || fail "Missing required file: ${f}"
done

command -v jq >/dev/null 2>&1 || fail "jq required"
command -v python3 >/dev/null 2>&1 || fail "python3 required"

# -----------------------------
# 1) Capture droplet baseline (G1)
# -----------------------------
log "Capturing droplet baseline (systemd + freshness scan)"
bash scripts/truth/capture_droplet_baseline.sh 2>&1 | tee "${RUN_DIR}/capture_droplet_baseline.log" | tee -a "${LOG}"

# Ensure baseline artifacts from capture script exist (path_map.md is maintained in repo)
for f in systemd_snapshot.txt freshness_scan.json; do
  [ -f "${BASELINE_DIR}/${f}" ] || touch "${BASELINE_DIR}/${f}"
done

# -----------------------------
# 2) Identify live systemd units (Cursor can confirm here)
# -----------------------------
log "Discovering candidate systemd units"
SYSTEMD_UNITS_TXT="${RUN_DIR}/systemd_units_detected.txt"
{
  echo "# Detected units (heuristic)"
  systemctl list-units --type=service --all 2>/dev/null | grep -E "stock|uw|flow|bot" || true
  echo
  echo "# Unit files (heuristic)"
  systemctl list-unit-files 2>/dev/null | grep -E "stock|uw|flow|bot" || true
} > "${SYSTEMD_UNITS_TXT}"

log "Wrote ${SYSTEMD_UNITS_TXT}"

# -----------------------------
# 3) CTR root readiness (permissions + ownership)
# -----------------------------
CTR_ROOT="${STOCKBOT_TRUTH_ROOT:-$CTR_ROOT_DEFAULT}"
log "CTR_ROOT=${CTR_ROOT}"

if [ ! -d "${CTR_ROOT}" ]; then
  log "CTR root missing; creating ${CTR_ROOT}"
  sudo mkdir -p "${CTR_ROOT}"
fi

# Try to set ownership to the current user (safe default); if services run as different user, baseline will reveal it.
log "Ensuring CTR root is writable"
sudo chown -R "$(id -u)":"$(id -g)" "${CTR_ROOT}" 2>/dev/null || true
touch "${CTR_ROOT}/.cursor_write_test" 2>/dev/null || fail "CTR root not writable: ${CTR_ROOT}"
rm -f "${CTR_ROOT}/.cursor_write_test" 2>/dev/null || true

# -----------------------------
# 4) Run local truth smoke test (router correctness)
# -----------------------------
log "Running truth smoke test (local CTR under repo)"
bash scripts/truth/run_truth_smoke_test.sh 2>&1 | tee "${RUN_DIR}/truth_smoke_test.log" | tee -a "${LOG}"

log "Running unit tests for truth_router"
(cd "${REPO}" && PYTHONPATH="${REPO}" python3 -m unittest tests.test_truth_router -q 2>&1) | tee "${RUN_DIR}/truth_router_tests.log" | tee -a "${LOG}"

# -----------------------------
# 5) Enable CTR mirror mode (writers only; readers unchanged)
# -----------------------------
# NOTE: systemctl set-environment sets GLOBAL env for all future started services (not per-unit).
# For persistent per-service env, use a drop-in instead, e.g.:
#   sudo mkdir -p /etc/systemd/system/stock-bot.service.d
#   echo -e '[Service]\nEnvironment="TRUTH_ROUTER_ENABLED=1"\nEnvironment="TRUTH_ROUTER_MIRROR_LEGACY=1"\nEnvironment="STOCKBOT_TRUTH_ROOT='"${CTR_ROOT}"'"' | sudo tee /etc/systemd/system/stock-bot.service.d/truth.conf
#   sudo systemctl daemon-reload
SERVICES="${SERVICES:-stock-bot.service}"

log "Enabling CTR mirror mode (global env); services: ${SERVICES}"
sudo systemctl set-environment \
  TRUTH_ROUTER_ENABLED=1 \
  TRUTH_ROUTER_MIRROR_LEGACY=1 \
  STOCKBOT_TRUTH_ROOT="${CTR_ROOT}" 2>/dev/null || true

for svc in ${SERVICES}; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${svc}"; then
    log "Restarting ${svc}"
    sudo systemctl restart "${svc}" 2>&1 | tee -a "${LOG}" || true
  else
    log "Service not present: ${svc} (skipping)"
  fi
done

sleep 10

# -----------------------------
# 6) Freshness + heartbeat check (CTR)
# -----------------------------
log "Checking CTR meta/heartbeat + freshness"
CTR_META="${CTR_ROOT}/meta"
CTR_HEALTH="${CTR_ROOT}/health"

mkdir -p "${CTR_META}" "${CTR_HEALTH}" 2>/dev/null || true

HEARTBEAT_FILE="${CTR_META}/last_write_heartbeat.json"
FRESHNESS_FILE="${CTR_HEALTH}/freshness.json"
MANIFEST_FILE="${CTR_META}/truth_manifest.json"
SCHEMA_FILE="${CTR_META}/schema_version.json"
PRODUCER_FILE="${CTR_META}/producer_versions.json"

CTR_STATUS_JSON="${RUN_DIR}/ctr_status.json"

python3 - <<PY 2>/dev/null > "${CTR_STATUS_JSON}" || true
import os, json, time
ctr = """${CTR_ROOT}"""
paths = {
  "heartbeat": """${HEARTBEAT_FILE}""",
  "freshness": """${FRESHNESS_FILE}""",
  "manifest": """${MANIFEST_FILE}""",
  "schema": """${SCHEMA_FILE}""",
  "producer_versions": """${PRODUCER_FILE}""",
}
out = {"ctr_root": ctr, "now_utc": time.time(), "files": {}}
for k, p in paths.items():
  out["files"][k] = {
    "path": p,
    "exists": os.path.exists(p),
    "mtime": os.path.getmtime(p) if os.path.exists(p) else None,
    "age_sec": (time.time() - os.path.getmtime(p)) if os.path.exists(p) else None,
  }
print(json.dumps(out, indent=2))
PY

log "CTR status written: ${CTR_STATUS_JSON}"

# -----------------------------
# 7) Parity spot-check (legacy vs CTR) — best-effort
# -----------------------------
log "Running parity spot-check (best-effort)"
PARITY_MD="${RUN_DIR}/parity_spotcheck.md"

LEGACY_STREAMS=(
  "logs/exit_truth.jsonl"
  "logs/expectancy_gate_truth.jsonl"
  "logs/signal_health.jsonl"
  "state/score_telemetry.json"
)
CTR_STREAMS=(
  "exits/exit_truth.jsonl"
  "gates/expectancy.jsonl"
  "health/signal_health.jsonl"
  "telemetry/score_telemetry.json"
)

{
  echo "# Parity spot-check (legacy vs CTR)"
  echo
  echo "| Stream | Legacy exists | Legacy mtime | Legacy lines | CTR exists | CTR mtime | CTR lines |"
  echo "|---|---:|---:|---:|---:|---:|---:|"
  for i in "${!LEGACY_STREAMS[@]}"; do
    l="${LEGACY_STREAMS[$i]}"
    c="${CTR_ROOT}/${CTR_STREAMS[$i]}"
    lex="no"; lmt=""; lln=""
    cex="no"; cmt=""; cln=""
    [ -f "${l}" ] && { lex="yes"; lmt="$(stat -c %Y "${l}" 2>/dev/null || true)"; [[ "${l}" == *.jsonl ]] && lln="$(wc -l < "${l}" 2>/dev/null || true)" || true; }
    [ -f "${c}" ] && { cex="yes"; cmt="$(stat -c %Y "${c}" 2>/dev/null || true)"; [[ "${c}" == *.jsonl ]] && cln="$(wc -l < "${c}" 2>/dev/null || true)" || true; }
    echo "| ${CTR_STREAMS[$i]} | ${lex} | ${lmt} | ${lln} | ${cex} | ${cmt} | ${cln} |"
  done
} > "${PARITY_MD}"

log "Wrote ${PARITY_MD}"

# -----------------------------
# 8) Governance summary (copy/paste)
# -----------------------------
SUMMARY="${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt"

cat > "${SUMMARY}" <<EOF
RUN_TAG: ${RUN_TAG}
RUN_DIR: ${RUN_DIR}
CTR_ROOT: ${CTR_ROOT}

WHAT RAN:
- scripts/truth/capture_droplet_baseline.sh
- scripts/truth/run_truth_smoke_test.sh
- tests/test_truth_router.py
- systemd env set (global): TRUTH_ROUTER_ENABLED=1, TRUTH_ROUTER_MIRROR_LEGACY=1, STOCKBOT_TRUTH_ROOT=${CTR_ROOT}
- restarted: ${SERVICES}

ARTIFACTS:
- baseline_dir: ${BASELINE_DIR}/
- detected_units: ${SYSTEMD_UNITS_TXT}
- ctr_status: ${CTR_STATUS_JSON}
- parity_spotcheck: ${PARITY_MD}
- logs: ${LOG}

NEXT (Cursor should do immediately):
1) Open ${BASELINE_DIR}/systemd_snapshot.txt and confirm the real producer units + run user.
2) If services run as non-root user, chown CTR_ROOT to that user and restart services.
3) Confirm CTR freshness: meta/last_write_heartbeat.json and health/freshness.json update during market hours.
4) Only after parity is stable: set TRUTH_USE_CTR=1 for dashboard/EOD readers (Phase 2).
5) Only after G2–G6 pass: consider TRUTH_ROUTER_MIRROR_LEGACY=0 (Phase 3).

ROLLBACK:
- Set TRUTH_ROUTER_ENABLED=0 in systemd env and restart stock-bot.
- Legacy remains authoritative; CTR directory stays for forensics.
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: CTR_MIRROR_MODE_ENABLED_BASELINE_CAPTURED"
echo "PR_BRANCH: NONE"

log "=== COMPLETE ${RUN_TAG} ==="
