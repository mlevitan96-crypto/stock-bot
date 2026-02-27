# Board consensus: top 3 most powerful next steps toward profitability

**As of:** 20260227T183736Z UTC  
**Source:** Board and all personas (Adversarial, Quant, Product/Operator, Execution/SRE, Risk) after review of all droplet governance data.

---

The board and all personas (Adversarial, Quant, Product/Operator, Execution/SRE, Risk) agree on the following three recommendations, in order of impact:

---

### 1. Fix entry attribution so signal_effectiveness populates (highest leverage)

**What:** Ensure every entry record in `logs/attribution.jsonl` (trade_id `open_*`) includes `context.attribution_components` (list of `{signal_id, contribution_to_score}`). Verify the join with exit_attribution so joined closed trades have `entry_attribution_components`. Re-run effectiveness so `signal_effectiveness.json` is built on the droplet.

**Why it's #1:** Right now we cannot try the **down-weight worst signal** lever (or later, up-weight best signal) because `signal_effectiveness` is empty. Every persona and the board called this the single highest-leverage fix. It unblocks the one entry-lever type we have never been able to test and enables data-driven signal tuning.

**Next step:** On droplet, inspect `logs/attribution.jsonl` for a recent entry record; if `context.attribution_components` is missing, trace the write path in main.py and add it. Then confirm the attribution loader joins correctly and effectiveness reports produce non-empty signal_effectiveness.

---

### 2. Keep rotation and add tried-lever tracking (full coverage, no blind repeat)

**What:** We already rotate entry threshold (2.7, 2.9, 3.0) and exit strength (0.02, 0.03, 0.05) by cycle. Add a small **tried-lever register** in `equity_governance_loop_state.json` (e.g. `tried_entry_thresholds`, `tried_exit_strengths` or last N overlay configs). Have the autopilot or recommender prefer the **next untried** value in rotation so we get explicit coverage and can report what has been tried vs not.

**Why it's #2:** Run history showed the same two lever types (2.9 and 0.03) repeating; rotation fixes that, but explicit tracking ensures we don't miss a combination and gives operators a clear audit of "what we've tried" toward profitability.

**Next step:** Extend state with tried-lever fields; when building overlay, prefer (e.g.) the smallest entry threshold or exit strength not yet tried in the last K cycles; document in the governance runbook.

---

### 3. Circuit breaker and honest giveback (risk control and stopping condition)

**What:** (a) **Circuit breaker:** Define a clear rule—e.g. if baseline expectancy is below -0.15 for two consecutive baseline rebuilds, auto-apply MIN_EXEC_SCORE=3.0 or pause new entries and document the decision. (b) **Giveback:** When `avg_profit_giveback` is null in effectiveness_aggregates, treat giveback in stopping_checks as "unknown"; do not LOCK on giveback alone; log that giveback could not be evaluated so the stopping condition is honest.

**Why it's #3:** Protects capital when things deteriorate (Risk, Board) and makes the stopping condition auditable (Quant, Execution/SRE). Prevents false LOCK when we don't actually have giveback data.

**Next step:** Add to runbook or state: circuit_breaker_triggered (bool), consecutive_bad_baselines (int). In the loop, after rebuilding baseline, check rule and set brake if needed. In compare_effectiveness_runs, when giveback is null, set stopping_checks.giveback_le_baseline_plus_005 to null and document in decision output.

---

**Summary:** Attribution first (unlock levers) → rotation + tracking (explore systematically) → circuit breaker + giveback (protect and stay honest). These three are the board's consensus on the most powerful next steps toward profitability.
