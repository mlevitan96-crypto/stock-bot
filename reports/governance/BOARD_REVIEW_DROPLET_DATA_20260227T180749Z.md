# Board review: all droplet data + additional ideas

**Generated:** 20260227T180749Z UTC

**Data source:** Fetched from droplet: state, effectiveness_baseline_blame (aggregates, signal_effectiveness, exit_effectiveness, blame, expectancy_gate_diagnostic), full equity_governance run history (decisions + overlays), latest recommendation, autopilot log tail.
**Prior context:** STRATEGIC_REVIEW, BOARD_CONSENSUS_TOP3_AND_NEXT, WHY_SAME_LEVERS_AND_RECOMMENDATIONS.

**Run history summary:**
- Total runs with decision: 20. LOCK: 0. REVERT: 20.
- Entry levers tried: thresholds [2.9]. Exit strengths tried: [0.03]. Down-weight signal ever tried: False.
- signal_effectiveness on droplet: empty.

---

## Adversarial

**Droplet data reviewed:**
- Run history: 20 runs, LOCK=0, REVERT=20. Entry levers tried: 11 (thresholds used: [2.9]). Exit levers tried: 9 (strengths: [0.03]). Down-weight signal lever ever tried: False.
- signal_effectiveness on droplet: empty. Baseline joined=2642, expectancy=-0.096338, win_rate=0.3948.
- Expectancy-gate diagnostic: p50=3.6661, pct_marginal_2_5_to_2_9=2.24. By-bucket expectancy present: True.

**Prior guidance (board consensus):** Down-weight worst signal; keep loop; giveback + brake. **Prior analysis (why same levers):** Only two lever types repeated; signal_effectiveness empty so down-weight never selected.

**Other ideas from full droplet data:**
- Do not add another discovery pipeline; the bottleneck is attribution not feeding signal_effectiveness. Fix the write/join so entry records carry attribution_components; then down-weight can run.
- If we have exit_effectiveness with reason codes, consider challenging: which exit reason has worst giveback? That could drive a targeted exit lever (e.g. weight for that reason) instead of only global flow_deterioration strength.

---

## Quant

**Droplet data reviewed:**
- Baseline: joined=2642, expectancy=-0.096338, win_rate=0.3948, giveback=None. Blame: weak_entry_pct=2.38, exit_timing_pct=0.0.
- Recommendation (latest): next_lever=entry, suggested_min_exec_score=2.9, entry_lever_type=None, top5_harmful count=0.
- Exit effectiveness: 1 reason codes; sample: ['other'].

**Other ideas from full droplet data:**
- Add a simple 'tried lever' register in state (e.g. tried_entry_thresholds, tried_exit_strengths) and have the recommender prefer the next untried value in rotation so we get explicit coverage.
- Once signal_effectiveness is populated, add a second lever: up-weight best signal (e.g. +0.05 for top win_rate component with enough trades) as an entry option alongside down-weight worst.
- Consider WTD (week-to-date) effectiveness vs 30D baseline as an early brake: if WTD expectancy is sharply worse than 30D, pause or tighten before 100 trades.

---

## Product / Operator

**Droplet data reviewed:**
- Process: 20 cycles with decisions; last_lever=entry, last_decision=REVERT, expectancy_history length=0.
- Lever variety implemented: rotation of entry threshold (2.7/2.9/3.0) and exit strength (0.02/0.03/0.05) by cycle; down-weight lever blocked until signal_effectiveness exists.

**Other ideas from full droplet data:**
- After N consecutive REVERTs (e.g. 6), run one cycle with no overlay (baseline only) to refresh baseline metrics and avoid drift from repeated overlay windows.
- Document one 'governance runbook' page that lists: what we have tried (from run history), what we have not tried (down-weight, up-weight, exit-by-reason), and what is blocked (attribution → signal_effectiveness).
- Optional: expose a small dashboard or report that shows last 10 runs with decision + lever + expectancy so operators can see variety at a glance.

---

## Execution / SRE

**Droplet data reviewed:**
- Diagnostic: by_score_bucket keys=['below_2_5', '2_5_to_2_7', '2_7_to_2_9', '2_9_to_3_2', 'above_3_2']. State has expectancy_history, last_replay_jump_cycle.
- Run history shows same two lever types until rotation; no replay overlay triggered (0 LOCKs so stagnation logic never fires).

**Other ideas from full droplet data:**
- Verify on droplet: do logs/attribution.jsonl entry records (trade_id open_*) contain context.attribution_components? If not, trace the write path in main.py and fix so effectiveness reports can build signal_effectiveness.
- After K REVERTs, optionally force a replay campaign run even without LOCK history, to inject a different overlay (replay-driven) and break the entry/exit alternation once.
- Ensure GOVERNANCE_ENTRY_THRESHOLD and GOVERNANCE_EXIT_STRENGTH are logged in autopilot log each cycle so we can confirm rotation is active.

---

## Risk

**Droplet data reviewed:**
- Candidate expectancy in last runs: [-0.216836, -0.216836, -0.216836]. Baseline expectancy: [-0.096338, -0.096338, -0.096338]. Stopping condition never met (0 LOCKs).
- Brake: documented; suggested_min_exec_score and rotation (2.7/2.9/3.0) in use.

**Other ideas from full droplet data:**
- Define an explicit 'circuit breaker': e.g. if baseline expectancy drops below -0.15 for two consecutive baseline rebuilds, auto-apply MIN_EXEC_SCORE=3.0 or pause new entries and document.
- When giveback is null in stopping_checks, treat as 'unknown' and do not LOCK on giveback alone; consider REVERT if other checks fail, and log that giveback could not be evaluated.

---

## Board verdict (from full droplet data review)

**Synthesis:** All personas have reviewed the full droplet dataset: state, baseline effectiveness, signal_effectiveness (empty), exit_effectiveness, governance run history, diagnostic, recommendation, and prior board consensus / why-same-levers analysis.

**Agreed (from BOARD_CONSENSUS_TOP3):** (1) Add down-weight worst signal when data allows. (2) Keep loop; monitor. (3) Giveback + brake when needed. **Not from board previously:** Lever rotation (2.7/2.9/3.0, 0.02/0.03/0.05) and the 'why same levers' diagnosis were engineering synthesis; the board now endorses rotation as a way to get variety until signal_effectiveness is fixed.

**Additional ideas (board, from this review):**
- **Attribution first:** Fix entry attribution so signal_effectiveness populates; then down-weight and (optionally) up-weight levers become available. This is the single highest-leverage fix.
- **Track tried levers:** Maintain a small 'tried' state (entry thresholds and exit strengths used) so we can explicitly prefer untried values or document coverage.
- **After N REVERTs:** One baseline-only cycle or one forced replay overlay to refresh and add variety.
- **Exit by reason:** Use exit_effectiveness (per reason code) to suggest a targeted exit lever (e.g. weight for worst-giveback reason) in addition to global flow_deterioration strength.
- **Circuit breaker:** Define a clear rule (e.g. baseline expectancy below -0.15 for two cycles) that triggers brake and document.


---

*Generated by scripts/governance/run_board_review_on_droplet_data.py*