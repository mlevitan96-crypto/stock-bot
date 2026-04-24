#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — TRUE REPLAY ENABLEMENT (SHADOW + PAPER SAFE)
#
# PURPOSE:
#   - Add required replay artifacts to ledger emission (paper-only)
#   - Backfill missing artifacts for existing ledgers (shadow-only)
#   - Re-run CSA/SRE gating until TRUE_REPLAY_POSSIBLE
#
# CONSTRAINTS:
#   - No live trading impact
#   - Shadow writes allowed only under reports/shadow or shadow/
#   - Paper engine changes allowed only to ADD logging fields (no behavior change)
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow/audit reports/audit reports/shadow/backfill

echo "=== PHASE 0: ASSERT BOARD APPROVAL ==="
test -f reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md
grep -q "APPROVE" reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md

echo "=== PHASE 1: SRE SCAN — WHERE LEDGERS ARE WRITTEN & WHICH FIELDS EXIST ==="
python3 scripts/sre/scan_ledger_emission_points.py \
  --repo-root . \
  --output reports/audit/SRE_LEDGER_EMISSION_SCAN_${DATE}.json

echo "=== PHASE 2: CSA CONTRACT — REQUIRED TRUE REPLAY FIELDS (AUTHORITATIVE) ==="
python3 scripts/csa/emit_true_replay_contract.py \
  --required \
      signal_vectors \
      normalized_scores \
      decision_timestamps \
      entry_exit_reasons \
  --timestamp-requirements \
      entry_ts \
      exit_ts \
  --output reports/audit/CSA_TRUE_REPLAY_CONTRACT_${DATE}.json

echo "=== PHASE 3: IMPLEMENTATION — ADD LEDGER FIELDS (PAPER-ONLY LOGGING) ==="
python3 scripts/runtime/patch_ledger_schema_add_replay_fields.py \
  --mode paper \
  --contract reports/audit/CSA_TRUE_REPLAY_CONTRACT_${DATE}.json \
  --sre-scan reports/audit/SRE_LEDGER_EMISSION_SCAN_${DATE}.json \
  --output reports/audit/LEDGER_SCHEMA_PATCH_PLAN_${DATE}.json

python3 scripts/runtime/apply_ledger_schema_patch.py \
  --mode paper \
  --plan reports/audit/LEDGER_SCHEMA_PATCH_PLAN_${DATE}.json \
  --output reports/audit/LEDGER_SCHEMA_PATCH_APPLIED_${DATE}.json

echo "=== PHASE 4: BACKFILL EXISTING LEDGERS (SHADOW-ONLY) ==="
python3 scripts/shadow/backfill_replay_artifacts.py \
  --ledger-dir reports/ledger \
  --contract reports/audit/CSA_TRUE_REPLAY_CONTRACT_${DATE}.json \
  --output-dir reports/shadow/backfill \
  --output reports/shadow/backfill/BACKFILL_REPORT_${DATE}.json

echo "=== PHASE 5: RE-RUN DISCOVERY + CSA FEASIBILITY GATE ==="
python3 scripts/shadow/discover_replay_artifacts.py \
  --ledger-dir reports/shadow/backfill \
  --expected-artifacts \
      signal_vectors \
      normalized_scores \
      decision_timestamps \
      entry_exit_reasons \
  --output reports/shadow/audit/REPLAY_ARTIFACT_DISCOVERY_${DATE}.json

python3 scripts/csa/evaluate_replay_feasibility.py \
  --discovery reports/shadow/audit/REPLAY_ARTIFACT_DISCOVERY_${DATE}.json \
  --require-explicit-verdict \
  --output reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json

echo "=== PHASE 6: HARD ASSERT — TRUE REPLAY MUST BE POSSIBLE OR BLOCK ==="
VERDICT=$(jq -r '.verdict' reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json)

if [ "$VERDICT" != "TRUE_REPLAY_POSSIBLE" ]; then
  echo "ERROR: TRUE REPLAY STILL NOT POSSIBLE — SEE ARTIFACT DISCOVERY + BACKFILL REPORT"
  exit 1
fi

echo "=== TRUE REPLAY ENABLED — SHADOW PROMOTION PIPELINE MAY PROCEED ==="
