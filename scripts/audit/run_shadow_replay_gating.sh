#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — SHADOW REPLAY CAPABILITY DISCOVERY & GATING
#
# PURPOSE:
#   - Determine whether true replay rescoring is possible
#   - Enforce proxy-only vs decision-grade separation
#   - Decide next execution path with CSA + SRE
#
# CONSTRAINTS:
#   - Shadow-only
#   - Read-only
#   - No promotion unless true replay is proven
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow/audit reports/shadow/rescore reports/audit

echo "=== PHASE 0: ASSERT BOARD APPROVAL ==="
test -f reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md || {
  echo "ERROR: Board approval missing"
  exit 1
}

grep -q "APPROVE" reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md || {
  echo "ERROR: Board decision not APPROVED"
  exit 1
}

echo "=== PHASE 1: CSA + SRE ARTIFACT DISCOVERY ==="
python3 scripts/shadow/discover_replay_artifacts.py \
  --ledger-dir reports/ledger \
  --expected-artifacts \
      signal_vectors \
      normalized_scores \
      decision_timestamps \
      entry_exit_reasons \
  --output reports/shadow/audit/REPLAY_ARTIFACT_DISCOVERY_${DATE}.json

echo "=== PHASE 2: CSA VERDICT — TRUE REPLAY FEASIBILITY ==="
python3 scripts/csa/evaluate_replay_feasibility.py \
  --discovery reports/shadow/audit/REPLAY_ARTIFACT_DISCOVERY_${DATE}.json \
  --require-explicit-verdict \
  --output reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json

echo "=== PHASE 3: BRANCH ON VERDICT ==="
VERDICT=$(jq -r '.verdict' reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json)

if [ "$VERDICT" = "TRUE_REPLAY_POSSIBLE" ]; then
  echo "=== TRUE REPLAY AVAILABLE — RUN DECISION-GRADE RESCORE ==="

  python3 scripts/shadow/run_true_replay_rescore.py \
    --replay-manifest reports/shadow/SHADOW_REPLAY_READY_${DATE}.json \
    --shortlist reports/shadow/PROMOTION_SHORTLIST_${DATE}.json \
    --metrics realized_pnl drawdown stability turnover tail_risk \
    --output reports/shadow/rescore/TRUE_REPLAY_RESULTS_${DATE}.json

  python3 scripts/shadow/rank_weight_configurations.py \
    --results reports/shadow/rescore/TRUE_REPLAY_RESULTS_${DATE}.json \
    --criteria expected_pnl stability drawdown tail_risk \
    --top-n 10 \
    --output reports/shadow/rescore/TRUE_REPLAY_RANKING_${DATE}.json

  python3 scripts/shadow/emit_promotion_shortlist.py \
    --ranking reports/shadow/rescore/TRUE_REPLAY_RANKING_${DATE}.json \
    --method true_replay_rescore \
    --output reports/shadow/PROMOTION_SHORTLIST_${DATE}.promotable.json

else
  echo "=== TRUE REPLAY NOT POSSIBLE — PROXY ONLY ==="

  python3 scripts/shadow/stamp_proxy_only.py \
    --shortlist reports/shadow/PROMOTION_SHORTLIST_${DATE}.json \
    --method proxy_pnl_scaling \
    --output reports/shadow/PROMOTION_SHORTLIST_${DATE}.proxy_only.json

  python3 scripts/audit/block_promotion_due_to_proxy.py \
    --reason "True replay artifacts missing" \
    --output reports/audit/PROMOTION_BLOCKED_PROXY_ONLY_${DATE}.json
fi

echo "=== SHADOW REPLAY GATING COMPLETE ==="
