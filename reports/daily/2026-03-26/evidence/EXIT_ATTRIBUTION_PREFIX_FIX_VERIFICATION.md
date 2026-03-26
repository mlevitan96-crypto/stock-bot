# Exit Attribution Prefix Fix — Verification

**Date:** 2026-02-28  
**Orchestrator:** Autonomous multi-model orchestrator  
**Commit:** fd71b7e — Normalize exit attribution naming (exit_ prefix), update tests and docs.

---

## Summary of code changes

### 1. `src/exit/exit_score_v2.py`

- **Canonical naming:** All exit attribution components now use `signal_id` with the **`exit_`** prefix.
- Added helper `_exit_signal_id(key)` returning `key` if it already starts with `exit_`, else `f"exit_{key}"`.
- **attribution_components** list now emits:
  - `signal_id`: normalized (e.g. `exit_flow_deterioration`, `exit_score_deterioration`, `exit_regime_shift`, `exit_vol_expansion`).
  - `source`: `"exit"` (explicit per-component source).
  - `contribution_to_score`: unchanged (weight × component value).
- **exit_reason_code** and raw **components** dict (v2_exit_components) are unchanged; only the attribution list written to logs uses the normalized prefix.

### 2. `validation/scenarios/test_exit_attribution_phase4.py`

- **test_exit_attribution_no_opaque_components:** Assertion updated from `startswith("exit.")` to `startswith("exit_")` with a clear error message.
- **test_build_exit_attribution_record_phase4_fields:** Example attribution component updated from `"exit.score_deterioration"` to `"exit_score_deterioration"`.
- Docstring updated: no opaque components → every component has `signal_id` with **"exit_"** prefix.

### 3. Documentation

- **MEMORY_BANK.md:** New bullet under §7.12: exit attribution naming contract — all `attribution_components[].signal_id` MUST begin with `exit_`.
- **reports/audit/MEMORY_BANK_INDEX.md:** Exit attribution schema (canonical) note and reference to test.
- **reports/exit_review/WHY_MULTI_FACTOR_EXITS_AND_HOW_TO_REVIEW.md:** Attribution paragraph updated to state that component `signal_id` values use the `exit_` prefix.
- **reports/exit_review/EXIT_IMPROVEMENT_PLAN.md:** Opening section updated with exit attribution schema (exit_ prefix).
- **reports/repo_audit/CANONICAL_REPO_STRUCTURE.md:** New canonical item: exit attribution schema (exit_ prefix, enforced by exit_score_v2 and test_exit_attribution_phase4).

---

## Test results

### Local (Windows)

- `validation/scenarios/test_exit_attribution_phase4.py`: **5 passed.**

### Droplet (after deploy)

- **Pytest spine (venv):**
  - `test_exit_attribution_phase4.py`: **5 passed** (including `test_exit_attribution_no_opaque_components`).
  - `test_effectiveness_reports.py`: **2 passed.**
  - `test_attribution_loader_join.py`: **3 passed.**
- **Total: 10 passed, 0 failed.**

---

## Deploy results

- **Git:** `git fetch origin && git reset --hard origin/main` — HEAD at fd71b7e.
- **Pytest spine:** Run via `venv/bin/python -m pytest` (all 10 tests passed).
- **Deploy steps:** git_pull ✓, pytest_spine ✓, kill_stale_dashboard ✓, restart_service ✓.
- **Deploy success:** True.
- **Live trading configs / overlays:** Not modified. No governance cycle started.

---

## Attribution verification

- **report_last_5_trades.py** (on droplet): Run completed; output saved to `reports/audit/last_5_trades_after_prefix_fix.txt`.
- **v2_exit_components:** Present in report (section “v2_exit_components (signals at exit that feed exit score)”).
- **Current last 5 trades:** Pre-deploy exits (v2_exit_score 0.0, “(none)” for components in display). New closes after deploy will emit **attribution_components** with `signal_id` values starting with `exit_`; no unprefixed component can be produced by the updated code path (enforced by `_exit_signal_id` in exit_score_v2 and by test_exit_attribution_no_opaque_components).

---

## Governance / status verification

- **Endpoint:** `GET http://localhost:5000/api/governance/status` (dashboard auth from .env).
- **Response (verified):**
  - `avg_profit_giveback`: null (expected until next effectiveness run).
  - `stopping_condition_met`: false.
  - `stopping_checks`: present (expectancy_gt_0, giveback_le_baseline_plus_005, joined_count_ge_100, win_rate_ge_baseline_plus_2pp).
  - `source_decision`: reports/equity_governance/equity_governance_20260227T184644Z/lock_or_revert_decision.json.
  - `source_aggregates`: reports/effectiveness_baseline_blame/effectiveness_aggregates.json.
  - `decision`: LOCK.
  - `expectancy_per_trade`, `win_rate`, `joined_count`: present.

---

## Phase 1 audit (droplet)

- **stock-bot.service:** Active.
- **uw-flow-daemon.service:** Active.
- **Alpaca alignment:** positions_count 18, cash 51025.39, equity 48983.34, status ACTIVE.
- **Artifacts:** PHASE1_DROPLET_RESULTS.md, PHASE1_DROPLET_RESULTS.json, PHASE1_ALPACA_ALIGNMENT.json updated.

---

## Follow-up recommendations

1. **Effectiveness runs:** When the next effectiveness run executes, exit attribution with `exit_` prefixed `signal_id` values will flow into effectiveness_aggregates and exit_effectiveness; no code change required.
2. **Historical data:** Old lines in `logs/exit_attribution.jsonl` may still have unprefixed component IDs (if any were written before this fix). New records are canonical. Optional: one-time backfill script to normalize old records if needed for analytics.
3. **Monitoring:** Use `scripts/report_last_5_trades.py` after the next market close to confirm new exits show `exit_` prefixed components when v2 exit score is non-zero.

---

**Verification complete.** Exit attribution naming contract is normalized to the `exit_` prefix; tests and docs updated; deploy and droplet verification successful.
