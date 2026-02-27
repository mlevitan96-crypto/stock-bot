#!/usr/bin/env bash
# Capture droplet baseline for truth migration: systemd snapshot + freshness scan.
# Run on droplet from repo root (e.g. /root/stock-bot). Writes to reports/truth_migration/droplet_baseline/.
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
OUT_DIR="${REPO}/reports/truth_migration/droplet_baseline"
mkdir -p "${OUT_DIR}"
cd "${REPO}" || exit 1

# Systemd snapshot
{
  echo "# systemctl show stock-bot"
  systemctl show stock-bot --property=WorkingDirectory --property=Environment --property=EnvironmentFile --property=MainPID --property=ActiveState 2>/dev/null || true
  echo ""
  echo "# systemctl show uw-flow-daemon (if present)"
  systemctl show uw-flow-daemon --property=WorkingDirectory --property=Environment --property=MainPID --property=ActiveState 2>/dev/null || true
  echo ""
  echo "# ls -la logs/ state/ data/"
  ls -la logs/ state/ data/ 2>/dev/null || true
} > "${OUT_DIR}/systemd_snapshot.txt"

# Freshness scan: truth-relevant paths
NOW=$(date +%s)
PATHS=(
  "logs/attribution.jsonl"
  "logs/exit_attribution.jsonl"
  "logs/exit_truth.jsonl"
  "logs/expectancy_gate_truth.jsonl"
  "logs/gate_truth.jsonl"
  "logs/run.jsonl"
  "logs/signal_health.jsonl"
  "logs/signal_score_breakdown.jsonl"
  "logs/score_snapshot.jsonl"
  "logs/orders.jsonl"
  "state/score_telemetry.json"
  "state/bot_heartbeat.json"
  "data/uw_flow_cache.json"
)

echo "{" > "${OUT_DIR}/freshness_scan.json"
echo "  \"ts_capture_iso\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "${OUT_DIR}/freshness_scan.json"
echo "  \"cwd\": \"$(pwd)\"," >> "${OUT_DIR}/freshness_scan.json"
echo "  \"paths\": [" >> "${OUT_DIR}/freshness_scan.json"
FIRST=1
for p in "${PATHS[@]}"; do
  if [ -f "${p}" ]; then
    MTIME=$(stat -c %Y "${p}" 2>/dev/null || echo "0")
    SIZE=$(stat -c %s "${p}" 2>/dev/null || echo "0")
    AGE=$((NOW - MTIME))
    [ "${FIRST}" -eq 0 ] && echo "," >> "${OUT_DIR}/freshness_scan.json"
    printf '    {"path":"%s","mtime_epoch":%s,"size_bytes":%s,"age_sec":%s}' "${p}" "${MTIME}" "${SIZE}" "${AGE}" >> "${OUT_DIR}/freshness_scan.json"
    FIRST=0
  fi
done
echo "" >> "${OUT_DIR}/freshness_scan.json"
echo "  ]" >> "${OUT_DIR}/freshness_scan.json"
echo "}" >> "${OUT_DIR}/freshness_scan.json"

echo "Captured: ${OUT_DIR}/systemd_snapshot.txt and ${OUT_DIR}/freshness_scan.json"
