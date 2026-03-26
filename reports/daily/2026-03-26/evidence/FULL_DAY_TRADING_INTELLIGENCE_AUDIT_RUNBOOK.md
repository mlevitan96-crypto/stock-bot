# Full Day Trading Intelligence Audit — Runbook

CSA + SRE + multi-persona governance with **mandatory counter-intel** and **signal system review**.  
**SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED.**

## Where to run

**This audit MUST be run on the droplet** so it uses production telemetry, state, and logs. Per MEMORY_BANK (Data Source Rule), reports must use production data from the droplet; local runs would use stale or wrong data.

## How to run on droplet

1. SSH to droplet, `cd` to repo, ensure `main` is up to date.
2. Optional: set date and counter-intel minimum.
   ```bash
   export DATE=2026-03-10
   export MIN_CI_EVENTS=0   # use 0 when no counter-intel expected that day; default in script is 0
   ```
3. Execute:
   ```bash
   bash scripts/audit/run_full_day_trading_intelligence_audit.sh
   ```
4. Or run from local and fetch artifacts:
   ```bash
   python3 scripts/audit/run_full_day_trading_intelligence_audit_on_droplet.py --date 2026-03-10
   ```

## Environment

- `GOVERNANCE_MODE=SHADOW_ONLY` — no live writes.
- `ALLOW_LIVE_WRITES=false`
- `REQUIRE_COUNTER_INTEL=true` — governance flag (verdict can fail if no CI when required).
- `MIN_CI_EVENTS` — minimum counter-intel events for Phase 3 assertion (default in script: 0; set 1 for strict).
- `DATE` — `YYYY-MM-DD` (default: today UTC).

## Phases and artifacts

| Phase | Purpose | Key artifact |
|-------|---------|--------------|
| 0 | Safety & governance lock | — |
| 1 | Full day trade universe (executed + blocked + CI) | `reports/ledger/FULL_TRADE_LEDGER_<DATE>.json` |
| 2 | SRE day health certification | `reports/audit/SRE_DAY_HEALTH_<DATE>.json` |
| 3 | Counter-intel assertion (mandatory gate) | Pass/fail |
| 4 | CSA decision quality & opportunity cost | `reports/audit/CSA_DECISION_QUALITY_<DATE>.json` |
| 5 | Signal system expansion (entry + exit) | `SIGNAL_WEIGHT_SWEEPS_<DATE>.json`, `SIGNAL_PROFITABILITY_<DATE>.json` |
| 6 | Idea harvesting (mass) | `RAW_IDEA_POOL_<DATE>.json`, `CLUSTERED_IDEAS_<DATE>.json` |
| 7 | Multi-persona review (CSA, SRE, QUANT, RISK, ADVERSARIAL, BOARD) | `reports/experiments/PERSONA_REVIEWS_<DATE>.json` |
| 8 | Robustness & promotion scoring | `reports/experiments/IDEA_SCORECARD_<DATE>.json` |
| 9 | CSA promotion verdict (SRE + optional require-counter-intel) | `reports/audit/CSA_DAY_PROMOTION_VERDICT_<DATE>.json` |
| 10 | Board packet | `reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_<DATE>.md` |

## Scripts (CSA, SRE, signals, ideas, review, board)

- **Phase 1:** `scripts/audit/reconstruct_full_trade_ledger.py`, `verify_trade_ledger_integrity.py`
- **Phase 2:** `scripts/sre/run_day_health_audit.py`, `assert_clean_day.py`
- **Phase 3:** `scripts/csa/assert_counter_intel_present.py`
- **Phase 4:** `scripts/csa/analyze_decision_quality.py`
- **Phase 5:** `scripts/signals/explode_signal_weights.py`, `evaluate_signal_profitability.py`
- **Phase 6:** `scripts/ideas/harvest_promotion_candidates.py`, `deduplicate_and_cluster_ideas.py`
- **Phase 7:** `scripts/review/run_persona_reviews.py` (personas: CSA, SRE, QUANT, RISK, ADVERSARIAL, BOARD)
- **Phase 8:** `scripts/experiments/score_ideas_for_promotion.py`
- **Phase 9:** `scripts/csa/render_promotion_verdict.py`
- **Phase 10:** `scripts/board/generate_day_board_packet.py`

## Reference

- MEMORY_BANK.md — Data Source Rule, Golden Workflow, governance.
- reports/audit/WEEKLY_BOARD_AUDIT_RUNBOOK.md — weekly CSA board audit sequence.
