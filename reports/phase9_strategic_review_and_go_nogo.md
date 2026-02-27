# Phase 9 — Strategic review + execution authorization

**Date:** 2026-02-18  
**Context:** Phases 0–9 complete; instrumented, auditable, reversible. Remaining work = learning velocity and capital efficiency.

---

## PART 1 — Multi-model review of ideas (A–F)

*Reviewed in context of this bot: signals (UW micro-signals, composite v2), exits (exit_score_v2, flow_deterioration, etc.), regimes, effectiveness pipeline, and exit_flow_weight_phase9 proposal.*

---

### IDEA A — Profitability from DAMAGE REDUCTION first

**Adversarial:** Agree. Reducing harm (down-weight harmful signals, cut giveback, contain losses) is measurable and reversible; “boost upside” is noisier and easier to overfit. **Risk:** Over-reducing can kill edge (e.g. zeroing a signal that sometimes helps). **This bot:** signal_effectiveness + entry_vs_exit_blame already rank harmful signals and exit reasons; damage reduction maps to existing levers (entry_weights_v3, exit_weights).  
**Quant:** High ROI: worst signal_id and worst exit_reason_code are in the reports; small deltas on those levers are the right first move.  
**Product:** Dashboard shows blame %, signal/exit effectiveness, giveback — enough to target damage reduction.

**Verdict:** **Adopt immediately.** Aligns with generate_recommendation.py (harmful signals, worst giveback exits) and PATH_TO_PROFITABILITY priority order.

---

### IDEA B — Trust only CONSISTENT evidence across windows

**Adversarial:** Correct in principle. Single 30d backtest can be regime-specific or noisy. **Risk:** Waiting for “multiple windows” can delay any move; we have no automated 45d/60d or rolling comparison yet. **This bot:** We have one baseline today; comparison is baseline vs proposed (same window). Multi-window is a next step.  
**Quant:** First cycle should still run — but we should **document** that the hypothesis is “conditional on this 30d window” and add paper/no-change validation (Idea F) before calling the lever proven.  
**Product:** Dashboard shows one effectiveness dir (latest_backtest_dir). No multi-window view yet; defer that feature.

**Verdict:** **Adopt as principle; defer full implementation.** Run first cycle on one 30d baseline; treat result as “provisional until confirmed in paper or second window.” Explicitly avoid: treating single-window improvement as permanent without a follow-up check.

---

### IDEA C — Counterfactual exits as FILTER, not logic

**Adversarial:** Right. counterfactual_exit (hold_longer_would_help, exit_earlier_would_save) identifies *candidates* for exit-timing issues; turning them directly into rules risks overfitting. **This bot:** build_counterfactual_exit in run_effectiveness_reports uses giveback/MAE thresholds; recommendation script does *not* auto-suggest from counterfactual counts — it uses blame + exit_effectiveness. So we already use counterfactuals as context, not as direct rule input.  
**Quant:** Use counterfactual to answer “is the problem entry or exit?” then use blame + signal/exit effectiveness to pick the lever.  
**Product:** Counterfactual is on dashboard; no “apply counterfactual” button. Good.

**Verdict:** **Adopt immediately.** Already how the pipeline works; make it explicit in docs: “Counterfactual = filter/diagnostic; lever choice = blame + signal/exit effectiveness.”

---

### IDEA D — One lever per cycle, small deltas only

**Adversarial:** Enforced by current process: one overlay, one weight/threshold, +0.01–0.03, LOCK or REVERT. **Risk:** None if we follow the runbook.  
**Quant:** exit_flow_weight_phase9 is exactly this: one lever (flow_deterioration), +0.02.  
**Product:** Change proposal template and checklist enforce single lever.

**Verdict:** **Adopt immediately.** No change needed; already policy.

---

### IDEA E — Backtesting strategy: multiple baselines, sensitivity, disable-to-learn

**Adversarial:** Multiple baselines (30d/45d/60d) and sensitivity sweeps (+0.01/+0.02/+0.03) improve confidence but require more runs and tooling. **This bot:** We have 30d pipeline and compare_backtest_runs; 45d/60d would need BACKTEST_DAYS and possibly separate runs. Disable-to-learn (zero one signal) would need an overlay that sets a weight to 0 and a way to interpret “no signal” in the engine.  
**Quant:** High value *after* first cycle. First cycle: one 30d baseline, one proposed, compare. Then add 45d/60d or sensitivity if we want stronger evidence.  
**Product:** Dashboard and runbook don’t yet support “compare 3 baselines” or “sensitivity table.” Defer.

**Verdict:** **Defer.** Adopt as *next* backtesting strategy once first cycle is done. For first cycle: single 30d baseline vs proposed is sufficient and correct.

---

### IDEA F — Paper as CONTROL, not test

**Adversarial:** Running a no-change paper period to compare paper effectiveness vs backtest effectiveness validates that backtest isn’t overly optimistic. **This bot:** We have live logs (attribution + exit_attribution); we could run effectiveness from logs for a “paper period” and compare to backtest effectiveness. Not automated yet.  
**Quant:** After LOCK, run e.g. 7 days paper with the new overlay; then run effectiveness from logs and compare to backtest. If paper metrics match backtest direction, confidence increases.  
**Product:** Dashboard can show effectiveness from latest_backtest_dir or reports; paper would need a dedicated effectiveness run from logs and a way to compare (manual or script). Defer automation; adopt as *practice*: “After LOCK, validate with paper before considering lever proven.”

**Verdict:** **Adopt as practice; defer full automation.** After first cycle LOCK: run a short paper period, then effectiveness from logs; compare to backtest. Document in change proposal as “post-LOCK validation.”

---

## Synthesis — What to adopt / defer / avoid

| Adopt immediately | Defer | Explicitly avoid |
|-------------------|--------|-------------------|
| A: Damage reduction first | B: Multi-window tooling (keep principle; one 30d for first cycle) | Treating single-window backtest as final truth without follow-up |
| C: Counterfactual as filter only | E: Multiple baselines, sensitivity sweeps, disable-to-learn (do after first cycle) | Turning counterfactuals directly into rules |
| D: One lever, small deltas | F: Automated paper-vs-backtest comparison (do manual/semi-manual after LOCK) | Multiple levers or >0.03 delta in one cycle |
| B as principle: “provisional until confirmed” | | Bypassing guards or runbook |

---

## PART 2 — Decision gate: GO / NO-GO

**Are we ready to run the first governed tuning cycle now?**

**GO**, with one condition.

**Condition:** Baseline must exist and be recorded. That means either:
- **Option 1 (preferred):** Run Step 2 of the runbook on the droplet (OUT_DIR_PREFIX=30d_baseline, full 30d pipeline). Then we have a baseline dir, effectiveness/*, latest_backtest_dir.json, and optionally profitability_recommendation.md.
- **Option 2:** Use an existing backtest dir that already has effectiveness/* and (if possible) profitability_recommendation.md; record that dir as baseline in phase8_first_cycle_result.md and in the change proposal.

**Why GO:**  
- Phase 5 effectiveness outputs exist (signal_effectiveness, exit_effectiveness, entry_vs_exit_blame, counterfactual_exit) and are produced by the droplet pipeline.  
- Phase 7/8 dashboard shows source, source_mtime, blame, effectiveness tables, trade lookup; we can verify truth post-run.  
- exit_flow_weight_phase9 is a single lever (flow_deterioration +0.02), evidence-backed by the *logic* of the recommendation script (when exit_timing_pct ≥ weak_entry_pct, suggest exit lever). Baseline numbers will be filled *when* we have the baseline dir (Step 2).  
- Guards and compare_backtest_runs are in place; runbook is explicit.

**If no baseline yet:** **NO-GO** until Step 2 is run and baseline path + effectiveness dir are recorded. Evidence “missing” = no baseline effectiveness dir to cite in the change proposal and no comparison baseline for proposed run.

**Single hypothesis with highest expected value and lowest risk:**  
**exit_flow_weight_phase9** (exit_weights.flow_deterioration +0.02).  
- **Expected value:** If exit timing dominates losers, exiting slightly earlier when flow deteriorates should reduce giveback and/or contain losses; small delta limits downside.  
- **Risk:** Low: one weight, +0.02, reversible; falsification criteria (win rate, giveback, guards) are explicit.  
- **Discard only if:** Baseline shows weak_entry_pct > exit_timing_pct and recommendation suggests an *entry* lever instead; then switch to that entry lever for this cycle and keep exit_flow for a later cycle.

---

## PART 3 — Authorization to execute

Once baseline is established (Step 2 complete) and proof is recorded:

**Execution is authorized** using **reports/phase9_droplet_runbook.md** as the canonical runbook.

**Scope:**
1. Deploy (if needed) and capture proof  
2. Establish baseline effectiveness (if not already done)  
3. Run baseline vs proposed backtests (Steps 3A–B)  
4. Compare + regression guards (Steps 3C–D)  
5. LOCK or REVERT with evidence (Step 3E)  
6. Dashboard truth check + screenshots (Step 4)

**Rules:**
- Follow the runbook exactly.  
- Do not introduce new tuning ideas mid-run.  
- Do not bypass guards.  
- Every step produces a proof artifact.

**Where proof artifacts are written:**

| Step | Artifact | Location |
|------|----------|----------|
| 1 Deploy | Deploy proof | `reports/phase8_deploy_proof.md` (commit hash, restart snippet, health, timestamp) |
| 2 Baseline | Baseline path + mtime | `reports/phase8_first_cycle_result.md` (baseline dir, effectiveness dir, mtime) |
| 3C Compare | Comparison output | `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` and `comparison.json` |
| 3D Guards | Guard result | Stdout of `regression_guards.py`; record PASS/FAIL in phase8_first_cycle_result.md |
| 3E Decide | LOCK/REVERT + deltas | `reports/phase8_first_cycle_result.md` (baseline/proposed dirs, deltas, guard result, decision) |
| 3E Proposal | Baseline path + cited metrics | `reports/change_proposals/exit_flow_weight_phase9.md` (fill Section 2) |
| 4 Dashboard | Screenshots | `reports/phase7_proof/` per README (freshness, trade lookup, tables) |
| 6 Checklist | Final checklist | `reports/phase9_deliverables_checklist.md` (checkboxes) |

**Note:** Execution on the droplet is performed by the user (or operator with droplet access) following the runbook. Cursor does not have SSH or runtime access to the droplet; it has prepared the runbook, change proposal, overlay, and this review. After each step, fill the artifacts above so the run is auditable and the decision (LOCK/REVERT) is evidence-based.

---

## Summary

- **Ideas:** Adopt A, C, D immediately; B and F as principle/practice; defer E and full B/F tooling.  
- **GO:** First governed cycle is authorized once baseline exists; hypothesis = exit_flow_weight_phase9 unless baseline clearly points to an entry lever.  
- **Execution:** Follow phase9_droplet_runbook.md; record every artifact in the locations above; no new levers mid-run, no bypassing guards.
