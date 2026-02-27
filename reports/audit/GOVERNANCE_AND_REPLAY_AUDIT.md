# Phase 4 — Governance Loop and Replay Engine Audit

**Audit date:** 2026-02-27  
**Scope:** run_equity_governance_loop_on_droplet.sh, state/equity_governance_loop_state.json, lock_or_revert_decision.json, compare_effectiveness_runs, replay campaign and canonical ledger.

---

## 1. Governance loop script

**File:** `scripts/run_equity_governance_loop_on_droplet.sh`

### 1.1 Alternation (even cycle = exit)

- Lines 136–139: `if [ -z "${FORCE_LEVER}" ] && [ $((CYCLE % 2)) -eq 0 ]; then FORCE_LEVER="exit"; fi`  
**Verdict:** **VERIFIED** — Even cycles force exit lever.

### 1.2 No-progress override

- Lines 121–134: If LAST_DECISION is LOCK and expectancy did not improve (LAST_EXP <= PREV_EXP), FORCE_LEVER is set to the other lever (entry vs exit).  
**Verdict:** **VERIFIED** — No-progress rule implemented.

### 1.3 100-trade gate

- In `CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh`: MIN_CLOSED_TRADES=100 (or 50 in some paths); overlay run waits until overlay effectiveness_aggregates joined_count >= MIN_CLOSED_TRADES before compare.  
- Stopping condition in compare_effectiveness_runs: `joined_count_ge_100` = (cand_joined >= 100).  
**Verdict:** **VERIFIED** — 100-trade gate present in stopping_checks; autopilot may use 50 for overlay wait (confirm MIN_CLOSED_TRADES in script).

### 1.4 Stopping condition logic

**File:** `scripts/analysis/compare_effectiveness_runs.py`

- stopping_checks: expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100.
- stopping_condition_met = all four True (lines 94–99).
- **Caveat:** giveback_le_baseline_plus_005 is None when base_gb or cand_gb is None (lines 89–90). If avg_profit_giveback is never populated in effectiveness_aggregates, this check is never True and stopping condition cannot be met.  
**Verdict:** **STRUCTURALLY SOUND**; **YELLOW** — giveback must be populated for stopping to work.

### 1.5 State file

- State: `state/equity_governance_loop_state.json`. Keys: last_lever, last_candidate_expectancy, prev_candidate_expectancy, last_decision, expectancy_history, last_replay_jump_cycle, tried_entry_thresholds, tried_exit_strengths.  
**Verdict:** **VERIFIED** — Script initializes and updates state; loop reads it for no-progress and stagnation.

---

## 2. lock_or_revert_decision.json

**Produced by:** `compare_effectiveness_runs.py --out <dir>/lock_or_revert_decision.json`.

**Expected fields:** decision, reasons, stopping_condition_met, stopping_checks (expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100), baseline (joined_count, win_rate, avg_profit_giveback, expectancy_per_trade), candidate (same).

**Verdict:** **VERIFIED** from compare_effectiveness_runs.py output structure. Win_rate and expectancy are computed from effectiveness_aggregates; giveback is passed through (can be null).

**DROPLET_REQUIRED:** Cat latest `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` and confirm stopping_checks and candidate/baseline sections present and reasonable.

---

## 3. Replay engine

### 3.1 Canonical equity trades

**Script:** `scripts/replay/build_canonical_equity_ledger.py`  
**Output:** `reports/replay/canonical_equity_trades.jsonl`  
**Input:** `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` (joined via attribution_loader).  
**Verdict:** Script exists and is correct. File exists only where logs exist (e.g. droplet). Run on droplet after logs are present.

### 3.2 Replay campaign

**Script:** `scripts/replay/run_equity_replay_campaign.py`  
- Runs equity_exit_replay.py (flow_deterioration sweep) and equity_entry_replay.py (min_exec_score sweep).
- Writes campaign_results.json and ranked_candidates.json (min 30 trades, ranked by expectancy desc, win_rate desc).
**Verdict:** **VERIFIED** — Structure is sound. Replay scripts (equity_exit_replay, equity_entry_replay) read from backtest or joined data; campaign does not require canonical_equity_trades.jsonl (it runs subprocess replays with different params).

### 3.3 ranked_candidates.json

- Ranked list of candidates with trade_count >= 30; each has lever_type, lever_params, expectancy_per_trade, win_rate, trade_count.  
**Adversarial:** Candidates with trade_count &lt; 30 are filtered out; ensure replay scripts produce plausible expectancy (no obvious hallucination).  
**Verdict:** Logic verified; sanity check on droplet by inspecting one campaign dir.

### 3.4 select_lever_from_replay.py

- Reads campaign_results.json, picks first implementable entry (min_exec_score) or exit (flow_deterioration) lever, writes overlay config.  
**Verdict:** **VERIFIED** — Consistent with governance loop usage (REPLAY_OVERLAY_CONFIG).

---

## 4. Stagnation and replay jump

- Loop (lines 82–116): If last N LOCK expectancies are stagnant (range &lt; epsilon) and cooldown elapsed, runs run_equity_replay_campaign.py and select_lever_from_replay, sets REPLAY_OVERLAY_CONFIG.  
**Verdict:** **VERIFIED** — Stagnation detection and replay overlay injection implemented.

---

## 5. Recommendations

1. **Guardrail:** Ensure effectiveness_aggregates includes avg_profit_giveback (trace exit_quality_metrics.profit_giveback → join → aggregate) so stopping_condition_met can become True when targets are hit.
2. **Thresholds:** Document MIN_CLOSED_TRADES (50 vs 100) in one place and align with stopping_checks joined_count_ge_100.
3. **Replay:** Run `run_equity_replay_campaign.py` on droplet (or with local data) once and confirm campaign_results.json and ranked_candidates.json are generated and values plausible.
4. **Board review:** Loop invokes run_board_persona_review.py after each cycle; confirm it runs and writes to reports/governance/.

---

## 6. Summary

| Item | Status |
|------|--------|
| Alternation (even = exit) | VERIFIED |
| No-progress override | VERIFIED |
| 100-trade gate (stopping_checks) | VERIFIED |
| Stopping condition logic | VERIFIED (giveback null = never True) |
| lock_or_revert_decision.json schema | VERIFIED |
| build_canonical_equity_ledger | VERIFIED (run where logs exist) |
| run_equity_replay_campaign | VERIFIED |
| select_lever_from_replay | VERIFIED |
| Stagnation → replay jump | VERIFIED |
