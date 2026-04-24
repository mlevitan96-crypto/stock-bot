#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — TRUE REPLAY RESCORE (BACKFILLED LEDGERS) + PROMOTABLE SHORTLIST
#
# PURPOSE:
#   - Use CSA-approved TRUE_REPLAY_POSSIBLE path
#   - Rescore shortlisted configs via true replay (shadow-only)
#   - Rank + emit PROMOTABLE shortlist for daily promotion loop
#   - Stamp artifact provenance = synthetic_backfill (epistemic honesty)
#
# CONSTRAINTS:
#   - Shadow-only
#   - Read-only w.r.t. live/paper configs
#   - No auto-promotion
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow/rescore reports/shadow/rankings reports/audit

echo "=== PHASE 0: ASSERT TRUE REPLAY ENABLED (CSA) ==="
test -f reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json || {
  echo "ERROR: Missing CSA replay feasibility verdict"
  exit 1
}

VERDICT=$(jq -r '.verdict' reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json)
if [ "$VERDICT" != "TRUE_REPLAY_POSSIBLE" ]; then
  echo "ERROR: CSA verdict is not TRUE_REPLAY_POSSIBLE (got: $VERDICT)"
  exit 1
fi

echo "=== PHASE 1: ASSERT INPUTS ==="
test -f reports/shadow/PROMOTION_SHORTLIST_${DATE}.json || {
  echo "ERROR: Missing shadow shortlist input"
  exit 1
}

test -f reports/shadow/SHADOW_REPLAY_READY_${DATE}.json || {
  echo "ERROR: Missing shadow replay manifest"
  exit 1
}

test -d reports/shadow/backfill || {
  echo "ERROR: Missing backfilled ledger directory: reports/shadow/backfill"
  exit 1
}

echo "=== PHASE 2: CREATE BACKFILL-BASED REPLAY MANIFEST (SHADOW-ONLY) ==="
python3 scripts/shadow/build_replay_manifest.py \
  --ledger-dir reports/shadow/backfill \
  --signal-model shadow/config/WEIGHTED_SIGNAL_MODEL.json \
  --read-only \
  --output reports/shadow/SHADOW_REPLAY_READY_${DATE}.backfill.json

echo "=== PHASE 3: TRUE REPLAY RESCORE TOP CANDIDATES ==="
python3 scripts/shadow/run_true_replay_rescore.py \
  --replay-manifest reports/shadow/SHADOW_REPLAY_READY_${DATE}.backfill.json \
  --shortlist reports/shadow/PROMOTION_SHORTLIST_${DATE}.json \
  --top-k 25 \
  --metrics realized_pnl drawdown stability turnover tail_risk \
  --output reports/shadow/rescore/TRUE_REPLAY_RESULTS_${DATE}.json

echo "=== PHASE 4: RANK TRUE REPLAY RESULTS ==="
python3 scripts/shadow/rank_weight_configurations.py \
  --results reports/shadow/rescore/TRUE_REPLAY_RESULTS_${DATE}.json \
  --criteria expected_pnl stability drawdown tail_risk \
  --top-n 10 \
  --output reports/shadow/rankings/TRUE_REPLAY_RANKING_${DATE}.json

echo "=== PHASE 5: EMIT PROMOTABLE SHORTLIST (TRUE REPLAY) ==="
python3 scripts/shadow/emit_promotion_shortlist.py \
  --ranking reports/shadow/rankings/TRUE_REPLAY_RANKING_${DATE}.json \
  --method true_replay_rescore \
  --output reports/shadow/PROMOTION_SHORTLIST_${DATE}.promotable.json

echo "=== PHASE 6: STAMP ARTIFACT PROVENANCE (SYNTHETIC BACKFILL) ==="
python3 scripts/shadow/stamp_shortlist_provenance.py \
  --shortlist reports/shadow/PROMOTION_SHORTLIST_${DATE}.promotable.json \
  --provenance synthetic_backfill \
  --notes "signal_vectors/normalized_scores/timestamps were backfilled; treat as bridge until native emission exists" \
  --output reports/shadow/PROMOTION_SHORTLIST_${DATE}.promotable.backfill.json

echo "=== PHASE 7: ASSERT PROMOTABLE SHORTLIST CONTRACT ==="
python3 scripts/audit/assert_promotable_shortlist.py \
  --shortlist reports/shadow/PROMOTION_SHORTLIST_${DATE}.promotable.backfill.json \
  --require-method "true_replay_rescore" \
  --output reports/audit/ASSERT_PROMOTABLE_SHORTLIST_${DATE}.json

echo "=== TRUE REPLAY SHORTLIST READY — DAILY PROMOTION LOOP MAY CONSUME ==="
