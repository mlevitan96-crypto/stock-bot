# Profitability Cockpit — Validation Report

**Timestamp:** 2026-03-06  
**Script run:** `scripts/update_profitability_cockpit.py`

## What was ingested

| Artifact | Path | Present |
|----------|------|--------|
| CSA verdict latest | reports/audit/CSA_VERDICT_LATEST.json | yes |
| CSA verdicts (all) | reports/audit/CSA_VERDICT_*.json | yes (multiple) |
| CSA findings (latest mission) | reports/audit/CSA_FINDINGS_CSA_TRADE_100_20260306-002808.md | yes |
| CSA board markdowns | reports/board/CSA_*.md | yes (CSA_TRADE_100_2026-03-06.md) |
| Trade CSA state | reports/state/TRADE_CSA_STATE.json or reports/state/test_csa_100/TRADE_CSA_STATE.json | yes (test_csa_100) |
| Governance | reports/audit/GOVERNANCE_AUTOMATION_STATUS.json | yes |
| SRE status | reports/audit/SRE_STATUS.json | yes |
| Shadow comparison | reports/board/SHADOW_COMPARISON_LAST387.json | yes |
| Board review | reports/board/last387_comprehensive_review.json | yes |

## What was detected

- **CSA live:** True (CSA_VERDICT_LATEST.json exists and generated_ts within 7 days)
- **100-trade trigger wired:** True (TRADE_CSA_STATE.json exists; last_csa_trade_count is a multiple of 100 or zero)
- **Last CSA mission:** CSA_TRADE_100_20260306-002808
- **Total trade events:** 105 (from state file used)
- **Trades until next CSA review:** 95
- **Promotable (shadow nomination):** B2_shadow (advance to live paper test candidate)
- **Governance status:** ok; **SRE overall_status:** OK; **anomalies_detected:** false

## Dashboard summary

- **PROFITABILITY_COCKPIT.md** exists at `reports/board/PROFITABILITY_COCKPIT.md`.
- All seven sections present: (1) CSA Status, (2) Promotable Items, (3) Not Promotable / Needs More Evidence, (4) Blocked & Counter-Intelligence Summary, (5) Expectancy & Learning, (6) Governance & SRE Health, (7) Next Actions (Owner View).
- Dashboard reflects latest CSA verdict (PROCEED, MED), trade counts, next CSA threshold (95 trades), promotable B2_shadow, missing_data and counterfactuals, blocked distribution from board review, governance and SRE health, and owner-level next actions.

## Checks

| Criterion | Result |
|-----------|--------|
| PROFITABILITY_COCKPIT.md exists | yes |
| Contains all sections | yes |
| Reflects latest CSA verdict | yes |
| Shows trade counts and next CSA threshold | yes |
| Shows promotable items | yes (B2_shadow, shadow ranking) |
| Shows governance and SRE status | yes |
| No trading logic modified | yes (read-only script) |

## Conclusion

Cockpit is operational. Run `python scripts/update_profitability_cockpit.py` to refresh the dashboard after new CSA runs, governance updates, or board reviews.
