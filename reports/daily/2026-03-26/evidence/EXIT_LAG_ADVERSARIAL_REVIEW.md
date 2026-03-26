# Exit-Lag Adversarial Review

**Role:** Adversarial Reviewer. Challenge overfitting, regime bias, and hidden risk.

## Challenges

- **Sample size:** Only 1 days. Improvement could be noise or single-regime luck.
- **Overfitting risk:** One day only. Best variant may not generalize.
- **Regime bias:** If most days are red (or green), improvement may be regime-specific.
- **Cherry-picking:** Backfill uses available trace/attribution; missing days may differ.

## Mitigations / Recommendations

- Backfill more days (5–10) and re-run multi-day validation before any promotion.
- Do not promote on one day. Require multi-day consistency.
- Review EXIT_LAG_REGIME_BREAKDOWN.md; prefer variants that improve in both green and red.
- SRE: document which dates were skipped (data missing) in backfill manifest.

## Summary

Verdict remains **CONTINUE_SHADOW** until sample size and regime diversity are sufficient and no adversarial challenge blocks promotion. SRE and CSA should incorporate this review before any PROMOTE decision.
