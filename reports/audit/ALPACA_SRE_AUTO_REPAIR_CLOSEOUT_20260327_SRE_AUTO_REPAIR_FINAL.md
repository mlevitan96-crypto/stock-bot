# CSA stop-gate — SRE auto-repair

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

## Criteria

| # | Requirement | Status |
|---|-------------|--------|
| A | Known failure classes auto-repaired without human | **Met** — classified trades receive additive `apply_backfill_for_trade_ids` when not UNKNOWN |
| B | Strict completeness → 0 when repairable | **Met** — engine re-gates each round; droplet history includes CERT_OK runs; repairable cohorts clear |
| C | Novel / unrepairable → single actionable INCIDENT | **Met** — exit **2**, incident MD/JSON + `sre_*` fields |
| D | Scheduler + manual proof | **Met** — bundle + timer restart + `latest_run_json_head` |

**CSA_VERDICT: SRE_AUTO_REPAIR_ACTIVE**
