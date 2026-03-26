# CSA Review: Alpaca Tier 1 + Tier 2 Board Review Implementation Plan

**Artifact:** `docs/ALPACA_TIER1_TIER2_BOARD_REVIEW_IMPLEMENTATION_PLAN.md`  
**Reviewer:** CSA (Chief Strategy Auditor) persona  
**Date:** 2026-03-16

---

## Adversarial assessment

1. **Risks**
   - **Tier 1 import of board.eod.rolling_windows:** Script adds repo to sys.path and imports; same process as build_30d_comprehensive_review. No execution risk; read-only. **Accept.**
   - **Tier 2 read-only:** No invocation of build_30d; if 7d/30d/last100 artifacts are missing, packet is partial. Plan correctly marks sections "missing." **Accept.**

2. **Blind spots**
   - **Trade visibility 48h:** Self-contained read of attribution/exit_attribution for since-hours may duplicate logic with trade_visibility_review; plan avoids subprocess. Consistency: both use same canonical logs. **Accept.**
   - **State merge:** Preserving Tier 3 keys while adding tier1_*/tier2_* must be implemented as read-modify-write; if state file is missing, Tier 1/2 scripts should create it with only their keys (Tier 3 keys absent until next Tier 3 run). **Recommendation:** On first run when state missing, write state with tier1_* and tier2_* only; Tier 3 script will repopulate its keys on next run. **Conditional accept.**

3. **Missing surfaces**
   - Tier 1 does not include 7d (design places 7d at Tier 2 boundary). **Accept.**
   - Tier 2 does not pull shadow comparison; that remains Tier 3. **Accept.**

4. **Improvements**
   - Optional: Tier 1 packet could note "For Tier 2/3 alignment see ALPACA_TIER2_REVIEW_* and ALPACA_BOARD_REVIEW_*." Non-blocking. **Accept.**

---

## Verdict

**ACCEPT.** Proceed to SRE review. Implementation note: state merge must not drop existing keys when updating; if state file is missing, write new state with only tier1/tier2 keys.
