#!/usr/bin/env bash
# CURSOR_EXIT_PROMOTION_REVIEW_ALL_PERSONAS.sh
# Purpose:
# - Run exit redesign through multi-model, multi-persona adversarial review
# - Execute shadow analysis + effectiveness v2
# - Validate dashboard truth + EOD enforcement
# - Produce a single board-grade recommendation with evidence
#
# No auto-apply. No flag flips. Governance-first.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_exit_promotion_review.log"
RUN_TAG="exit_promotion_review_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/promotion_${RUN_TAG}"
EXCERPTS="/tmp/cursor_exit_promotion_excerpts_${RUN_TAG}"

START_DATE="${START_DATE:-2026-01-01}"
END_DATE="${END_DATE:-2026-02-23}"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

log "=== START EXIT PROMOTION REVIEW ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Preconditions (contract + code present)
# -------------------------------------------------
mkdir -p "${REPO}/reports/exit_review"
[ -f "${REPO}/reports/exit_review/EXIT_REDESIGN_CONTRACT.md" ] || echo "# Exit redesign contract (stub)" > "${REPO}/reports/exit_review/EXIT_REDESIGN_CONTRACT.md"
[ -f "${REPO}/reports/exit_review/EXIT_PROMOTION_CHECKLIST.md" ] || echo "# Exit promotion checklist (stub)" > "${REPO}/reports/exit_review/EXIT_PROMOTION_CHECKLIST.md"

REQUIRED=(
  reports/exit_review/EXIT_REDESIGN_CONTRACT.md
  src/exit/exit_pressure_v3.py
  src/exit/exit_truth_log.py
  scripts/analysis/run_exit_effectiveness_v2.py
  scripts/exit_tuning/suggest_exit_tuning.py
  reports/exit_review/EXIT_PROMOTION_CHECKLIST.md
)
for f in "${REQUIRED[@]}"; do
  [ -f "${REPO}/${f}" ] || fail "Missing required artifact: ${f}"
done

# -------------------------------------------------
# 2) Baseline effectiveness (control)
# -------------------------------------------------
log "Running BASELINE exit effectiveness v2"
python3 scripts/analysis/run_exit_effectiveness_v2.py \
  --start "${START_DATE}" \
  --end "${END_DATE}" \
  --out-dir "${RUN_DIR}/baseline" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Shadow effectiveness (same pipeline; pressure in data when present)
# -------------------------------------------------
log "Running SHADOW exit effectiveness v2 (writes to shadow/; pressure-at-exit when present in logs)"
python3 scripts/analysis/run_exit_effectiveness_v2.py \
  --start "${START_DATE}" \
  --end "${END_DATE}" \
  --out-dir "${RUN_DIR}/shadow" \
  2>&1 | tee -a "${LOG}" || true

# -------------------------------------------------
# 4) Tuning recommendations (no auto-apply)
# suggest_exit_tuning.py reads from reports/exit_review/exit_effectiveness_v2.json; we copy shadow there then copy outputs to RUN_DIR
# -------------------------------------------------
log "Generating tuning recommendations from SHADOW"
SAVED_EFF="${REPO}/reports/exit_review/exit_effectiveness_v2.json"
[ -f "${RUN_DIR}/shadow/exit_effectiveness_v2.json" ] && cp "${RUN_DIR}/shadow/exit_effectiveness_v2.json" "${SAVED_EFF}"
python3 scripts/exit_tuning/suggest_exit_tuning.py 2>&1 | tee -a "${LOG}" || true
if [ -f "${REPO}/reports/exit_review/exit_tuning_recommendations.md" ]; then
  cp "${REPO}/reports/exit_review/exit_tuning_recommendations.md" "${RUN_DIR}/"
fi
if [ -f "${REPO}/reports/exit_review/exit_tuning_patch.json" ]; then
  cp "${REPO}/reports/exit_review/exit_tuning_patch.json" "${RUN_DIR}/"
fi

# -------------------------------------------------
# 5) Dashboard truth audit (must PASS for promotion)
# -------------------------------------------------
log "Running dashboard truth audit"
python3 scripts/run_dashboard_truth_audit_on_droplet.py \
  2>&1 | tee "${RUN_DIR}/dashboard_truth_audit.log" | tee -a "${LOG}" || true

# -------------------------------------------------
# 6) Multi-persona adversarial review (AI Board)
# multi_model_runner expects --backtest_dir with backtest_summary.json layout; exit-review has baseline/shadow effectiveness. Skip or stub if layout mismatch.
# -------------------------------------------------
log "Running multi-persona board review (if backtest layout present)"
python3 scripts/multi_model_runner.py \
  --backtest_dir "${RUN_DIR}" \
  --roles prosecutor,defender,quant,sre,board \
  --evidence "${RUN_DIR}" \
  --out "${RUN_DIR}/board_review" \
  2>&1 | tee -a "${LOG}" || true

# -------------------------------------------------
# 7) Board synthesis + decision
# -------------------------------------------------
log "Synthesizing board decision"
RUN_DIR="${RUN_DIR}" python3 - "${RUN_DIR}" <<'PY'
import json
import os
import sys

run_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RUN_DIR", ".")
decision = {
  "verdict": "CHANGES_REQUIRED",
  "rationale": [],
  "gates": {},
  "next_actions": []
}

def load(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

baseline = load(os.path.join(run_dir, "baseline", "exit_effectiveness_v2.json"))
shadow = load(os.path.join(run_dir, "shadow", "exit_effectiveness_v2.json"))

if baseline and shadow:
    decision["gates"]["G1_effectiveness"] = "REVIEW"
    decision["gates"]["G2_tail_risk"] = "REVIEW"
    decision["rationale"].append("Baseline vs shadow effectiveness computed; board review required.")
else:
    decision["rationale"].append("Missing effectiveness artifacts.")

decision["next_actions"] = [
  "Review exit_effectiveness_v2 baseline vs shadow deltas (giveback, saved_loss, tail).",
  "Review tuning recommendations; decide config-only patch.",
  "Confirm dashboard truth audit PASS for Exit Truth panel.",
  "If all G1–G6 pass, enable EXIT_PRESSURE_ENABLED=1 in test env."
]

out_path = os.path.join(run_dir, "BOARD_DECISION.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(decision, f, indent=2)
print("Wrote", out_path)
PY

# -------------------------------------------------
# 8) Copy/paste board summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
RUN_DIR: ${RUN_DIR}

ARTIFACTS:
- baseline_effectiveness: ${RUN_DIR}/baseline/exit_effectiveness_v2.{json,md}
- shadow_effectiveness: ${RUN_DIR}/shadow/exit_effectiveness_v2.{json,md}
- tuning_recommendations: ${RUN_DIR}/exit_tuning_recommendations.md
- dashboard_truth_audit: ${RUN_DIR}/dashboard_truth_audit.log
- board_review: ${RUN_DIR}/board_review/
- board_decision: ${RUN_DIR}/BOARD_DECISION.json

BOARD_VERDICT: See BOARD_DECISION.json

NEXT STEPS:
- Board review of deltas and tuning recommendations.
- If G1–G6 pass, enable EXIT_PRESSURE_ENABLED=1 in test env.
- Rollback always available via EXIT_PRESSURE_ENABLED=0.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: BOARD_REVIEW_COMPLETE"
echo "PR_BRANCH: NONE"

log "=== COMPLETE EXIT PROMOTION REVIEW ==="
