# Board Review: Implementation and Current Status

**Date:** 2026-02-28  
**Scope:** Post-deploy implementation (exit attribution prefix, giveback, entry attribution, dashboard, pytest spine, replay-driven lever selection, governance loop restart) and path to profitability.  
**References:** STRATEGIC_REVIEW_AND_PATH_TO_PROFITABILITY_2026-02-26.md, GOVERNANCE_LOOP_RESTART_AND_REPLAY_INTEGRATION.md, EXIT_ATTRIBUTION_PREFIX_FIX_VERIFICATION.md, DROPLET_POST_DEPLOY_VERIFICATION.md, MEMORY_BANK_INDEX.md.

---

## 1. Implementation summary (what was done)

| Area | Change | Status |
|------|--------|--------|
| **Exit attribution naming** | All exit attribution `signal_id` values use `exit_` prefix (e.g. exit_flow_deterioration). Enforced in src/exit/exit_score_v2.py and test_exit_attribution_phase4.py. | ✅ Deployed; tests 10/10 pass. |
| **Giveback logic** | high_water fallback in main.py so MFE/profit_giveback and effectiveness_aggregates.avg_profit_giveback can populate when high_water missing. | ✅ In code; giveback still null until more exits with high_water. |
| **Entry attribution** | context.attribution_components set from composite_meta/composite_result/comps so signal_effectiveness.json can populate from joined trades. | ✅ In code; signal_effectiveness minimal (2 bytes) until next effectiveness run with full join. |
| **Dashboard** | GET /api/governance/status exposes expectancy_per_trade, win_rate, avg_profit_giveback, stopping_condition_met, stopping_checks, source_decision, source_aggregates. | ✅ Live on port 5000. |
| **Pytest spine** | validation/scenarios/test_exit_attribution_phase4, test_effectiveness_reports, test_attribution_loader_join; run in venv on droplet during deploy. | ✅ 10/10 pass on droplet. |
| **Replay-driven lever selection** | select_lever_with_replay.py: when FORCE_LEVER unset, compare live recommendation vs top ranked_candidates.json; choose lever with stronger evidence; write overlay_config.json. Autopilot A2/A3 integrated. | ✅ Integrated; first cycle used live (no replay stronger). |
| **Governance loop** | Killed stale processes; restarted via run_equity_governance_orchestrator.py online --loop. Loop: no-progress → opposite lever; even cycle → exit; stagnation → replay campaign; else → replay-driven comparison. | ✅ Running; A4 waiting for ≥100 closed trades. |

---

## 2. Board review by persona

### 2.1 Adversarial

- **Risk — Giveback gate still open:** avg_profit_giveback remains null in effectiveness_aggregates; stopping_checks.giveback_le_baseline_plus_005 is null, so stopping_condition_met cannot become True on the giveback dimension until we have enough exits with high_water and a populated giveback. The code fix is in place; we need volume and time for data to populate.
- **Risk — One-off bug in A3:** First cycle (00:17) failed with AttributeError on overlay lever .lower(); fixed in c9ce815. Confirms need for defensive parsing (j.get('lever') or 'exit') and explicit overlay["lever"] string in select_lever_with_replay. No recurrence in second cycle.
- **Risk — Replay not yet influencing:** Current cycle chose “live -> entry” because no ranked_candidates or replay expectancy did not beat live. Replay will only matter when (a) an OFFLINE replay campaign has been run and ranked_candidates.json exists, and (b) top replay candidate has trade_count ≥ 30 and expectancy > live baseline. Stagnation path (run replay campaign in-loop) will create candidates; odd-cycle comparison will then use them.
- **Positive:** Exit attribution is now canonical (exit_ prefix); no opaque components; effectiveness and board review can rely on consistent signal_ids. Single lever per cycle; no manual overlay application.

### 2.2 Quant

- **Evidence:** Baseline effectiveness run (A1) shows joined_count=2320, total_losing_trades=1431 — sufficient for blame and recommendation. Live expectancy_per_trade ≈ -0.079 to -0.088; win_rate ≈ 37.5%. Decision logic (weak_entry_pct vs exit_timing_pct → entry vs exit) is in generate_recommendation and is used by the loop.
- **Gate:** Loop uses MIN_CLOSED_TRADES=100 (not 50) for overlay window before A5 compare. Align with strategic review “50-trade gate” by either documenting 100 as current policy or lowering to 50 if we want faster cycles.
- **Replay comparison:** select_lever_with_replay uses “replay expectancy > live baseline expectancy” and “trade_count ≥ 30”. Consider adding win_rate and stability (e.g. subperiod consistency) to the comparison so we don’t pick a high-expectancy, low-sample or unstable replay candidate.
- **Next lever:** Current cycle applied entry (MIN_EXEC_SCORE=2.7). Next cycle will be even → FORCE_LEVER=exit (alternation), then odd again with live vs replay. No change to one-lever-per-cycle discipline.

### 2.3 Product / Operator

- **Current status:** Bot is live (paper). stock-bot.service and uw-flow-daemon.service active; Alpaca positions_count=18, status ACTIVE. Governance loop running; log at /tmp/equity_governance_autopilot.log. Loop is in A4 (waiting for ≥100 closed trades since overlay start 2026-02-28).
- **Canonical baseline:** reports/effectiveness_baseline_blame is the designated baseline; A1 refreshes it each cycle. recommendation.json and overlay_config.json written per run to reports/equity_governance/equity_governance_<tag>/.
- **Checklist alignment:** We have (1) effectiveness from logs → blame + signal_effectiveness; (2) entry vs exit from recommendation; (3) one overlay applied (entry, MIN_EXEC_SCORE=2.7); (4) paper run with that overlay; (5) waiting for 100 closed trades → then compare → LOCK/REVERT. Replay-driven selection adds “compare with top replay candidate when available” without skipping the one-lever discipline.
- **Gap:** signal_effectiveness.json is still minimal (2 bytes) on droplet; entry attribution fix is in code but full population depends on joined trades with context.attribution_components. Next effectiveness run (and more closed trades with correct logging) should improve.

### 2.4 Execution / SRE

- **Deploy and tests:** Droplet at c9ce815; venv used for pytest (system Python externally managed). Pytest spine 10/10; no manual config or overlay changes.
- **Loop resilience:** If the autopilot script fails (e.g. missing file or Python error), the loop exits. Consider wrapping the autopilot call in a retry or logging “cycle failed, retry in N min” so the loop doesn’t exit on transient failures.
- **Log and PID:** Log path and process (run_equity_governance_loop_on_droplet.sh) confirmed. No stale duplicate loops observed after kill + restart.
- **Dashboard:** Governance status endpoint returns all required fields; when overlay run has no lock_or_revert_decision yet, dashboard may show nulls for decision/source — expected until A5 completes.

### 2.5 Risk

- **No live config or overlay changes by hand:** Confirmed; only the loop and selection logic were changed; overlay applied by the autopilot (MIN_EXEC_SCORE=2.7) is the single active paper lever.
- **Stopping condition:** Until giveback is populated, stopping_condition_met cannot be True on all four checks. That’s acceptable as long as we treat “three of four” or “expectancy + win_rate + joined_count” as sufficient for a soft stop and document giveback as “when available.”
- **Optional brake:** Strategic review suggests a temporary raise of MIN_EXEC_SCORE or pause if paper stays negative while waiting for data. Current cycle already raised threshold to 2.7; if next LOCK/REVERT still negative, consider 2.9 or 3.0 as next entry lever or as a short-term risk brake.

---

## 3. Issues and gaps (concise)

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| avg_profit_giveback null → giveback gate never True | Medium | Let time/volume populate; optionally run a one-off effectiveness run after more closes with high_water to validate giveback pipeline. |
| signal_effectiveness.json minimal | Low | Rely on next effectiveness run and entry attribution in new trades; verify join and attribution_components in last_5_trades after next market day. |
| Replay not yet used (no stronger candidate) | Low | Run OFFLINE replay campaign when convenient; or wait for stagnation path to run campaign in-loop. |
| First-cycle A3 .lower() bug (fixed) | Closed | Defensive (j.get('lever') or 'exit') and explicit overlay lever string in place. |
| 100 vs 50 trade gate | Low | Document 100 as current policy or reduce to 50 for faster iteration per strategic review. |
| Loop exits on autopilot failure | Low | Add retry or “cycle failed, sleep and retry” so loop doesn’t exit on transient errors. |

---

## 4. Current status of the bot

- **Services:** stock-bot (with dashboard), uw-flow-daemon active. Alpaca paper: 18 positions, ACTIVE.
- **Governance:** Loop running; cycle 1 completed A1–A3; A4 waiting for ≥100 closed trades (overlay joined_count polling from 0).
- **Metrics (pre-restart snapshot):** expectancy_per_trade ≈ -0.079, win_rate ≈ 37.5%, joined_count 2320 (baseline), decision LOCK from last compare. stopping_condition_met false (expectancy &lt; 0, giveback null, win_rate below baseline+2pp).
- **Attribution:** Exit attribution canonical (exit_ prefix); entry attribution and giveback logic in code; next effectiveness run will improve signal_effectiveness and giveback when data exists.
- **Codebase:** Exit prefix, giveback high_water fix, entry attribution context, dashboard /api/governance/status, pytest spine, select_lever_with_replay and A2/A3 integration all in place and verified.

---

## 5. Next steps to improve toward profitability

**Immediate (this week)**

1. **Let the loop run:** Allow A4 to collect ≥100 closed trades under the current overlay (MIN_EXEC_SCORE=2.7). No manual lever changes.
2. **After A5 compare:** If LOCK and metrics improve (e.g. win_rate or expectancy better), keep baseline and proceed to next cycle (alternation will force exit lever). If REVERT, loop will revert overlay and rebuild baseline; next cycle will try the other lever or a new candidate.
3. **Confirm giveback pipeline:** After the next effectiveness run that includes exits with high_water, check effectiveness_aggregates.avg_profit_giveback and stopping_checks.giveback_le_baseline_plus_005. If still null, trace high_water in log_exit_attribution and compute_exit_quality_metrics.

**Short-term (next 2–4 weeks)**

4. **One blame baseline, one lever (strategic review):** We have the baseline (effectiveness_baseline_blame, joined_count 2320). Continue one lever per cycle; use recommendation (entry vs exit) and replay when ranked_candidates beat live. Goal: first LOCK with improved expectancy or win_rate over 50–100 trades.
5. **Optional OFFLINE replay:** Run `python scripts/governance/run_equity_governance_orchestrator.py offline` to produce a fresh ranked_candidates.json so odd cycles can compare live vs replay. Not required for the loop to function but increases chance of picking a stronger lever.
6. **Document 100-trade gate:** In EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK or MEMORY_BANK, state that MIN_CLOSED_TRADES=100 is the current overlay window; align with strategic review (50 vs 100) and any decision to shorten cycles.

**Medium-term (path to profitability)**

7. **Tighten or brake if needed:** If paper stays negative after 2–3 cycles, consider raising MIN_EXEC_SCORE (e.g. 2.9, 3.0) as the next entry lever or as a temporary risk brake to reduce volume and drawdown.
8. **Stability in replay selection:** Enhance select_lever_with_replay to consider win_rate and, if available, subperiod stability so we don’t overfit to a single replay run.
9. **Signal effectiveness and giveback:** Once signal_effectiveness.json and giveback are populated, use them in generate_recommendation and in board reviews to justify entry (down-weight worst signal) vs exit (flow_deterioration or other) and to close the giveback gate when data allows.

---

## 6. Board verdict

- **Implementation:** Exit attribution prefix, giveback logic, entry attribution, dashboard endpoint, pytest spine, and replay-driven lever selection are correctly implemented and integrated. One transient bug (A3 .lower()) was fixed. No manual overlay or live config changes.
- **Current status:** Bot and governance loop are running; baseline is healthy (joined_count 2320); loop is waiting for 100 closed trades before the next compare. Giveback and signal_effectiveness will improve with data and next effectiveness run.
- **Issues:** Giveback null (data/time); signal_effectiveness minimal (next run); replay not yet used (optional campaign); 100 vs 50 trade gate and loop exit-on-failure are minor operational points.
- **Next steps:** Let the loop complete the current cycle (100 trades → A5 compare → LOCK/REVERT). Keep one-lever-per-cycle discipline; optionally run OFFLINE replay to feed ranked_candidates; document gate and consider retry logic for the loop. Proceed along the strategic review path: one blame baseline, one correct lever, 50–100 trade check, repeat until positive expectancy or clear improvement.

**No blocking issues.** Implementation and status support continued operation and the next steps above.
