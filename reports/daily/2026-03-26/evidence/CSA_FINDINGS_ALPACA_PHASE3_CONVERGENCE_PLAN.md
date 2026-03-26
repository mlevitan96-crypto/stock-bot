# CSA Adversarial Review: Alpaca Phase 3 Convergence Plan

**Plan:** `docs/ALPACA_PHASE3_CONVERGENCE_PLAN.md`  
**Verdict:** **ACCEPT**

---

## Architecture fit

- Plan uses existing Tier 1/2/3 packet dirs from `state/alpaca_board_review_state.json` and fallbacks to `reports/board/` and `reports/state/rolling_pnl_5d.jsonl`. No new data authority; read-only. Aligns with ARCHITECTURE_AND_OPERATIONS (data authority on droplet; convergence can run locally or on droplet using same paths).
- Single new script and single new state file; no changes to Tier 1/2/3 scripts. Fits current Alpaca governance layering (Tier 3 → Tier 1/2 already implemented; convergence consumes their outputs).
- No Kraken references. Advisory only (design §6: no auto-block). No promotion logic in this phase.

## Adversarial checks

- **Missing packets:** Plan classifies as mild divergence and emits "Missing Tier1/2/3 data"; no crash. OK.
- **Sign consistency:** Tier1 5d vs Tier2/Tier3 sign comparison is defined; "zero" and "missing" avoid false severe. OK.
- **SRE anomaly:** Uses `overall_status` and `automation_anomalies_present` from SRE_STATUS.json; severe only when divergence + anomaly. OK.
- **State overwrite:** Overwrite each run is idempotent; no append. Safe.
- **Paths:** All under --base-dir; no hardcoded absolute paths for content. OK.

## Conditions

- Implementation must use Tier1 packet path from state when present (`tier1_last_packet_dir` → TIER1_REVIEW.json), Tier2 from `tier2_last_packet_dir` (TIER2_REVIEW.json), Tier3 from `last_packet_dir` (BOARD_REVIEW.json). Fallbacks only when state missing or packet dir missing.
- SRE anomaly: treat `overall_status` not in ("OK", "HEALTHY") OR `automation_anomalies_present` true as anomaly.

---

**CSA:** ACCEPT. Proceed to SRE review, then implementation.
