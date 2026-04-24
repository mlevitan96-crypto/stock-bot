#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — SHADOW SIGNAL CORRELATION & CLUSTER ANALYSIS
#
# PURPOSE:
#   - Analyze signal-level correlations at decision time
#   - Identify latent signal clusters and conditional dependence
#   - Produce cluster-aware diagnostics and recommendations
#
# SCOPE:
#   - Shadow-only
#   - Read-only
#   - No gating, no promotion, no weight changes
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow/correlation reports/shadow/clusters reports/audit

echo "=== PHASE 0: ASSERT TRUE REPLAY ARTIFACTS AVAILABLE ==="
test -f reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json || {
  echo "ERROR: Missing CSA replay feasibility verdict"
  exit 1
}

VERDICT=$(jq -r '.verdict' reports/audit/CSA_REPLAY_FEASIBILITY_VERDICT_${DATE}.json)
if [ "$VERDICT" != "TRUE_REPLAY_POSSIBLE" ]; then
  echo "ERROR: True replay artifacts not available; correlation analysis requires signal vectors"
  exit 1
fi

echo "=== PHASE 1: EXTRACT SIGNAL MATRICES FROM BACKFILLED LEDGERS ==="
python3 scripts/shadow/extract_signal_matrices.py \
  --ledger-dir reports/shadow/backfill \
  --output reports/shadow/correlation/SIGNAL_MATRICES_${DATE}.json

echo "=== PHASE 2: COMPUTE SIGNAL CORRELATION MATRICES ==="
python3 scripts/shadow/compute_signal_correlations.py \
  --signal-matrices reports/shadow/correlation/SIGNAL_MATRICES_${DATE}.json \
  --condition-on outcome \
  --output reports/shadow/correlation/SIGNAL_CORRELATIONS_${DATE}.json

echo "=== PHASE 3: IDENTIFY SIGNAL CLUSTERS ==="
python3 scripts/shadow/identify_signal_clusters.py \
  --correlations reports/shadow/correlation/SIGNAL_CORRELATIONS_${DATE}.json \
  --method hierarchical \
  --threshold 0.7 \
  --output reports/shadow/clusters/SIGNAL_CLUSTERS_${DATE}.json

echo "=== PHASE 4: CONDITIONAL IMPORTANCE ANALYSIS ==="
python3 scripts/shadow/analyze_conditional_importance.py \
  --clusters reports/shadow/clusters/SIGNAL_CLUSTERS_${DATE}.json \
  --signal-matrices reports/shadow/correlation/SIGNAL_MATRICES_${DATE}.json \
  --output reports/shadow/clusters/CONDITIONAL_IMPORTANCE_${DATE}.json

echo "=== PHASE 5: EMIT CLUSTER-AWARE RECOMMENDATIONS (SHADOW ONLY) ==="
python3 scripts/shadow/emit_cluster_recommendations.py \
  --clusters reports/shadow/clusters/SIGNAL_CLUSTERS_${DATE}.json \
  --importance reports/shadow/clusters/CONDITIONAL_IMPORTANCE_${DATE}.json \
  --output reports/shadow/clusters/CLUSTER_RECOMMENDATIONS_${DATE}.json

echo "=== SHADOW CORRELATION & CLUSTER ANALYSIS COMPLETE ==="
