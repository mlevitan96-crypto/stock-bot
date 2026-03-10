# Full Day Trading Intelligence Audit — Runbook

CSA + SRE + multi-persona governance pipeline. **SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED.**

## Where to run

**This audit MUST be run on the droplet** so it uses production telemetry, state, and logs. Per MEMORY_BANK (Data Source Rule), reports must use production data from the droplet; local runs would use stale or wrong data.

## How to run on droplet

1. SSH to droplet, `cd` to repo, ensure `main` is up to date.
2. Optional: set date (default is today UTC).
   ```bash
   export DATE=2026-03-10
   ```
3. Execute:
   ```bash
   bash scripts/audit/run_full_day_trading_intelligence_audit.sh
   ```
4. Pull artifacts back (e.g. commit/push from droplet or fetch via your usual sync).

## Environment

- `GOVERNANCE_MODE=SHADOW_ONLY` — no live writes.
- `ALLOW_LIVE_WRITES=false`
- `PROMOTION_ALLOWED=true`
- `DATE` — `YYYY-MM-DD` (default: today UTC).

## Phases and artifacts

| Phase | Purpose | Key artifact |
|-------|---------|--------------|
| 0 | Safety & scope lock | — |
| 1 | Full day trade universe | `reports/ledger/FULL_TRADE_LEDGER_<DATE>.json` |
| 2 | SRE system health | `reports/audit/SRE_DAY_HEALTH_<DATE>.json` |
| 3 | CSA decision quality | `reports/audit/CSA_DECISION_QUALITY_<DATE>.json` |
| 4 | Idea harvesting | `reports/ideas/CLUSTERED_IDEAS_<DATE>.json` |
| 5 | Multi-persona review | `reports/experiments/PERSONA_REVIEWS_<DATE>.json` |
| 6 | Promotion scoring | `reports/experiments/IDEA_SCORECARD_<DATE>.json` |
| 7 | CSA promotion verdict | `reports/audit/CSA_DAY_PROMOTION_VERDICT_<DATE>.json` |
| 8 | Board packet | `reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_<DATE>.md` |
| 9 | Final assertions | Pass/fail on required artifacts |

## Implementation status

The following scripts are **referenced by the pipeline but may not yet exist**. Implement or wire stubs as needed:

- `scripts/audit/reconstruct_full_trade_ledger.py`
- `scripts/audit/verify_trade_ledger_integrity.py`
- `scripts/sre/run_day_health_audit.py`
- `scripts/sre/assert_clean_day.py`
- `scripts/csa/analyze_decision_quality.py`
- `scripts/ideas/harvest_promotion_candidates.py`
- `scripts/ideas/deduplicate_and_cluster_ideas.py`
- `scripts/review/run_persona_reviews.py`
- `scripts/experiments/score_ideas_for_promotion.py`
- `scripts/csa/render_promotion_verdict.py`
- `scripts/board/generate_day_board_packet.py`
- `scripts/audit/assert_artifacts_present.py`
- `config/promotion_rules.json`

Existing related pieces: `scripts/audit/build_weekly_trade_decision_ledger.py`, `scripts/audit/run_csa_weekly_review.py`, `scripts/board/build_next_action_packet.py`, `scripts/sre/run_sre_anomaly_scan.py`.

## Reference

- MEMORY_BANK.md — Data Source Rule, Golden Workflow, governance.
- reports/audit/WEEKLY_BOARD_AUDIT_RUNBOOK.md — weekly CSA board audit sequence.
