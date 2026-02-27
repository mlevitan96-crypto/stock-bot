#!/usr/bin/env bash
# Truth migration smoke test: run bot loop in dry mode; verify CTR streams and heartbeat.
# Requires TRUTH_ROUTER_ENABLED=1. Writes to reports/truth_migration/smoke_test/.
set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "$0")/../.." && pwd)}"
OUT_DIR="${REPO}/reports/truth_migration/smoke_test"
mkdir -p "${OUT_DIR}"
cd "${REPO}" || exit 1

# Use a local truth root under repo for test (no /var/lib)
export TRUTH_ROUTER_ENABLED=1
export TRUTH_ROUTER_MIRROR_LEGACY=1
export STOCKBOT_TRUTH_ROOT="${REPO}/reports/truth_migration/smoke_test/truth"
rm -rf "${STOCKBOT_TRUTH_ROOT}"
mkdir -p "${STOCKBOT_TRUTH_ROOT}"

echo "=== Truth smoke test: CTR root ${STOCKBOT_TRUTH_ROOT} ==="
export REPO="${REPO}"

# Run a short Python snippet that uses the router (no full main.py)
python3 << PY
import os
import sys
sys.path.insert(0, os.environ.get("REPO", "."))
os.chdir(os.environ["REPO"])
# Ensure router is enabled
os.environ["TRUTH_ROUTER_ENABLED"] = "1"
os.environ["TRUTH_ROUTER_MIRROR_LEGACY"] = "1"
from src.infra.truth_router import append_jsonl, write_json, truth_path, is_writable

# Write one record to each stream type
append_jsonl("gates/expectancy.jsonl", {"ts_eval_epoch": 0, "symbol": "SMOKE", "gate_outcome": "pass"}, expected_max_age_sec=300)
append_jsonl("health/signal_health.jsonl", {"ts": 0, "symbol": "SMOKE", "components": {}}, expected_max_age_sec=600)
append_jsonl("exits/exit_truth.jsonl", {"ts": "2026-01-01T00:00:00Z", "symbol": "SMOKE", "decision": "HOLD"}, expected_max_age_sec=600)
write_json("telemetry/score_telemetry.json", {"last_update": "2026-01-01T00:00:00Z", "scores": []}, expected_max_age_sec=600)
print("Writes OK")
assert is_writable(), "is_writable() should be True"
print("is_writable OK")
PY

# Check structure
ROOT="${STOCKBOT_TRUTH_ROOT}"
for f in "${ROOT}/meta/last_write_heartbeat.json" "${ROOT}/meta/schema_version.json" "${ROOT}/health/freshness.json" \
         "${ROOT}/gates/expectancy.jsonl" "${ROOT}/exits/exit_truth.jsonl"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: missing $f"
    exit 1
  fi
  echo "OK: $f"
done

# Count lines in JSONL
GATE_LINES=$(wc -l < "${ROOT}/gates/expectancy.jsonl" || echo "0")
EXIT_LINES=$(wc -l < "${ROOT}/exits/exit_truth.jsonl" || echo "0")
echo "gates/expectancy.jsonl lines: ${GATE_LINES}"
echo "exits/exit_truth.jsonl lines: ${EXIT_LINES}"

# Summary
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "${TS} smoke test PASS" > "${OUT_DIR}/result.txt"
echo "Smoke test PASS. Output in ${OUT_DIR}"
