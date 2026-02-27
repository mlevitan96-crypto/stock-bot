#!/usr/bin/env bash
# CURSOR_EXIT_PAPER_PROMOTION_WITH_ADVERSARIAL_REVIEW.sh
# Promote grid-approved exit strategy to PAPER trading.
# Shadow becomes experimental. Requires adversarial + code review before apply.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_paper_promotion_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_paper_promotion.log"

TUNED_CONFIG="config/exit_candidate_signals.tuned.json"
PAPER_CONFIG="config/paper_exit_signals.json"
SHADOW_CONFIG="config/shadow_exit_signals.json"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== EXIT PAPER PROMOTION WITH ADVERSARIAL REVIEW ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Preconditions
# -------------------------------------------------
if [ ! -f "${TUNED_CONFIG}" ]; then
  log "ERROR: Tuned exit config not found: ${TUNED_CONFIG}"
  exit 1
fi

log "Tuned exit config found."

# -------------------------------------------------
# 2) Stage PAPER and SHADOW configs (no apply yet)
# -------------------------------------------------
log "Staging PAPER exit config (best-known exits)"
cp "${TUNED_CONFIG}" "${PAPER_CONFIG}"

log "Staging SHADOW exit config (experimental baseline)"
cp "${TUNED_CONFIG}" "${SHADOW_CONFIG}"

# -------------------------------------------------
# 3) Adversarial multi-model review request
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_ADVERSARIAL_REVIEW_REQUEST.md" <<EOF
EXIT STRATEGY PROMOTION — ADVERSARIAL REVIEW REQUEST

CONTEXT:
- Exit grid search simulated 1,643 real exits using Alpaca bars.
- 160 exit parameter sets evaluated.
- Board decision: PROMOTE_TOP_CONFIG.
- Tuned exit config staged for PAPER trading.

PROPOSED CHANGE:
- PAPER trading will use the tuned exit config.
- SHADOW will diverge and be used for experimental exit logic.

REVIEW ROLES (REQUIRED):
1) Prosecutor:
   - Argue why this exit promotion could fail in live conditions.
2) Defender:
   - Argue why this promotion is justified and low-risk.
3) Quant:
   - Evaluate statistical validity and overfitting risk.
4) SRE:
   - Evaluate operational and monitoring risks.
5) Board:
   - Decide APPROVE / REQUEST_CHANGES / REJECT.

REVIEW MUST ADDRESS:
- Risk of overfitting
- Regime sensitivity
- Exit churn
- Failure modes in fast markets
- Rollback safety

NO CODE MAY BE APPLIED UNTIL REVIEW IS COMPLETE.
EOF

# -------------------------------------------------
# 4) Code review checklist
# -------------------------------------------------
cat > "${RUN_DIR}/CODE_REVIEW_CHECKLIST.md" <<EOF
EXIT PROMOTION — CODE REVIEW CHECKLIST

REVIEW REQUIRED BEFORE APPLY:
- Exit config loading paths correct
- PAPER vs SHADOW separation enforced
- No live trading flags touched
- Rollback path documented
- Metrics emitted for exits (PnL, churn, duration)
- No unintended side effects

Reviewer must sign off before apply.
EOF

# -------------------------------------------------
# 5) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT STRATEGY PROMOTION — WHAT IS HAPPENING

WHAT IS BEING PROMOTED:
- A grid-approved exit parameter configuration.
- Proven to improve PnL on historical exits.

WHAT THIS BLOCK DID:
- Staged tuned exits for PAPER trading.
- Defined SHADOW as an experimental exit lab.
- Requested adversarial multi-model review.
- Required explicit code review before apply.

IMPORTANT:
- No live capital is affected.
- No behavior has changed yet.
- This is a governance checkpoint.

NEXT STEPS:
1) Complete adversarial review (all roles).
2) Complete code review checklist.
3) If APPROVED:
   - Apply PAPER exit config.
   - Begin live truth capture.
4) If CHANGES REQUESTED:
   - Adjust config and re-review.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_PAPER_PROMOTION_REVIEW_REQUIRED"

log "=== COMPLETE EXIT PAPER PROMOTION STAGING ==="
