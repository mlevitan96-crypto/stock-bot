# CSA Review: Alpaca Tier 3 Board Review Implementation Plan

**Artifact:** `docs/ALPACA_TIER3_BOARD_REVIEW_IMPLEMENTATION_PLAN.md`  
**Reviewer:** CSA (Chief Strategy Auditor) persona  
**Date:** 2026-03-15 (design-time)

---

## Adversarial assessment

1. **Risks**
   - **Stale inputs:** Packet may be generated when last387 or shadow comparison are days old. Plan correctly does not mandate freshness; packet is point-in-time. **Mitigation:** Document in packet "Generated at X; input paths and mtimes can be checked by SRE." No code change required for Phase 1.
   - **Missing shadow comparison:** Plan correctly marks section as "Shadow comparison not run; required before promotion." This is narrative only and does not gate anything. **Accept.**

2. **Blind spots**
   - **Weekly ledger date:** Plan uses `--date` or today for WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_<date>.json. If weekly review runs on a specific weekday, date alignment may yield missing file. Plan already treats weekly as optional. **Accept.**
   - **CSA_BOARD_REVIEW glob:** Plan says "CSA_BOARD_REVIEW_<date>.json (glob)". Implementation should resolve to single most recent by date or mtime to avoid ambiguity. **Recommendation:** In implementation, glob and take latest by mtime; document in plan. **Conditional accept.**

3. **Missing surfaces**
   - Tier 3 design includes "stability/cluster-risk" and "CSA_BOARD_REVIEW (promotable ideas)". Plan includes optional CSA_BOARD_REVIEW. Stability/cluster-risk (STABILITY_ANALYSIS, CLUSTER_RISK_OVER_TIME) are not in the input list. For Phase 1, acceptable to omit; can be added in a later phase. **Accept.**

4. **Improvements**
   - Add to packet cover: "Input file mtimes (UTC)" for key artifacts (last387 review, shadow comparison, CSA_VERDICT_LATEST, SRE_STATUS) so readers can judge staleness. **Recommendation:** Implement optional mtime listing in cover or appendices. **Non-blocking.**

---

## Verdict

**ACCEPT** with one implementation note: when including optional CSA_BOARD_REVIEW, resolve glob to a single latest file (by mtime). No plan revision required. Proceed to SRE review.
