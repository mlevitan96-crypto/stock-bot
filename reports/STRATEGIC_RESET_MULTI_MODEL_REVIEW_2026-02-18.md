# Strategic reset — Multi-model review + conditional execution
## 2026-02-18

**Context:** Phases 0–9 complete; system losing money daily. Goal: profitability, not elegance.  
**Task:** Review ideas A–E adversarially; synthesize; GO/NO-GO; if GO, proceed per runbook only.

---

## Critical finding (must read first)

**The current backtest pipeline does not apply exit-weight overlays.**

- `scripts/run_30d_backtest_droplet.py` **replays** `logs/attribution.jsonl` and `logs/exit_attribution.jsonl`. It does **not** re-simulate exit decisions using `GOVERNED_TUNING_CONFIG`.
- `board/eod/run_30d_backtest_on_droplet.sh` does not pass `GOVERNED_TUNING_CONFIG` into the backtest step. Even if it did, the backtest script does not read it.
- Consequence: **baseline vs proposed backtest comparison for exit-weight overlays is structurally incapable of showing a difference.** PnL delta 0 and win_rate delta 0 are expected, not evidence of “no harm.”
- Phase 9 “LOCK” was therefore based on a **degenerate comparison**: the runbook’s Step 4 (compare + guards) cannot falsify exit-weight changes with the current backtest. Treating that LOCK as “overlay proven” is incorrect.

This does not invalidate the governance *process*; it means **the runbook’s backtest-compare step is not yet a valid measurement for exit levers** until either (A) backtest applies overlay in the exit path, or (B) paper-period effectiveness is the primary evidence and backtest is deprecated for exit-weight decisions.

---

## Multi-model review of ideas A–E

### IDEA A — Damage reduction first

**Claim:** Profitability will come from removing harmful trades and reducing giveback, not from boosting upside. Down-weight or gate the worst signals before adding anything new.

| Lens | Challenge / risk | Applies to this bot? |
|------|-------------------|----------------------|
| **Adversarial** | “Damage reduction first” can become “only cut,” and you may remove marginal-but-positive edge. You need a threshold: how bad is “worst”? If you cut everything below median win_rate, you might over-trim. | Yes. signal_effectiveness + entry_vs_exit_blame exist; worst signal_id and worst exit_reason_code are in reports. Risk is over-cutting. |
| **Quant** | High ROI if you target the true worst offenders. Without entry_vs_exit_blame on a representative window, you might be reducing “damage” from the wrong side (entry vs exit). | Yes, but we lack a **single authoritative baseline** of blame (effectiveness from backtest dirs on droplet failed join; effectiveness from logs was run but recommendation was empty). |
| **Product** | Dashboard supports damage reduction (blame %, giveback). Adopt, but pair with “one lever per cycle” so we don’t cut five signals at once. | Yes. |

**Verdict:** **Adopt immediately** with a caveat: we must have at least one solid effectiveness baseline (from logs or fixed backtest) that includes entry_vs_exit_blame before we decide *whether* damage reduction is entry-focused or exit-focused. Otherwise we may tune the wrong side.

---

### IDEA B — One lever per cycle, small deltas only

**Claim:** +0.01 to +0.03 changes; no stacking exit_flow + exit_score; LOCK or REVERT, no partial acceptance.

| Lens | Challenge / risk | Applies to this bot? |
|------|-------------------|----------------------|
| **Adversarial** | Strict one-lever discipline can slow discovery if the true fix is “exit flow and score together.” But stacking without evidence is worse. | Yes. We already have two exit levers in play: flow_deterioration 0.22 (LOCKed on degenerate evidence) and score_deterioration 0.28 (paper run, exploratory). Stacking them now would violate this idea. |
| **Quant** | Small deltas limit downside and make attribution clear. No objection. | Yes. |
| **Product** | Runbook and change proposal template enforce single lever. Good. | Yes. |

**Verdict:** **Adopt immediately.** No change. Explicitly avoid: stacking exit_flow and exit_score in one cycle; deltas > 0.03.

---

### IDEA C — Counterfactuals are diagnostic only

**Claim:** Use counterfactuals to identify exit timing issues; do NOT turn them into rules yet.

| Lens | Challenge / risk | Applies to this bot? |
|------|-------------------|----------------------|
| **Adversarial** | If we never turn counterfactuals into rules, we might under-use a valid signal. But turning them directly into “exit when hold_longer_would_help” would be overfitting. | Yes. Pipeline already uses counterfactual as context; generate_recommendation does not auto-suggest from counterfactual counts. |
| **Quant** | Use counterfactual to answer “entry vs exit?” then use blame + signal/exit effectiveness to pick the lever. Correct. | Yes. |
| **Product** | No “apply counterfactual” button; diagnostic only. Good. | Yes. |

**Verdict:** **Adopt immediately.** Already the de facto policy; keep it explicit.

---

### IDEA D — Paper runs are probes, not truth

**Claim:** Paper is for validation AFTER a governed LOCK. Exploratory paper runs must not bypass backtest comparison.

| Lens | Challenge / risk | Applies to this bot? |
|------|-------------------|----------------------|
| **Adversarial** | If backtest *cannot* measure exit overlay impact, then “paper must not bypass backtest” effectively blocks all exit-lever validation until we fix the backtest. So the principle is right, but the *implementation* of “governed” must adapt: for exit levers, paper may have to be the primary evidence until backtest is fixed. | Yes. Current state: backtest compare is degenerate for exit weights. So “don’t bypass backtest” either means (1) fix backtest first, or (2) for exit levers, define “governed” as: hypothesis → paper run → effectiveness from logs → compare to baseline effectiveness → LOCK/REVERT. |
| **Quant** | Paper with same metrics (effectiveness from logs, same comparison criteria) is valid evidence. Backtest that doesn’t apply overlay is not. | Yes. |
| **Product** | Paper run doc already says “exploratory, NOT a governed LOCK candidate yet.” Good. 7–14 day check is the right gate. | Yes. |

**Verdict:** **Adopt as principle.** For **exit-weight overlays** specifically: treat paper + effectiveness-from-logs as the **primary** comparison until backtest applies overlay in exit path. Do not treat exploratory paper as LOCK without that comparison and explicit decision record.

---

### IDEA E — We may be tuning the wrong side

**Claim:** If losses are dominated by weak entries, exit tuning will not save us. Entry quality may be the real bottleneck.

| Lens | Challenge / risk | Applies to this bot? |
|------|-------------------|----------------------|
| **Adversarial** | This is the most important challenge. We have been pushing exit levers (flow_deterioration, score_deterioration) while we lack a single, join-complete effectiveness baseline that reports entry_vs_exit_blame. If weak_entry_pct >> exit_timing_pct, we are optimizing the wrong thing. | **Yes.** We do not yet have a definitive blame split from a full effectiveness run (backtest effectiveness failed on droplet; logs-based effectiveness had “recommendation empty”). So we are **assuming** exit is the bottleneck. |
| **Quant** | PATH_TO_PROFITABILITY says: fix entry if blame says “bad trades”; fix exit if blame says “closing good too early / bad too late.” We have not yet confirmed which dominates. | Yes. Next high-value step is to **produce one authoritative entry_vs_exit_blame** (e.g. effectiveness from logs for last 14–30 days with join working) and then choose entry vs exit lever from that. |
| **Product** | Dashboard can show blame when data exists. We need to ensure at least one effectiveness run produces blame. | Yes. |

**Verdict:** **Adopt immediately as a check, not a veto.** Before committing to another exit-only cycle: get one effectiveness run (from logs or fixed backtest) that yields entry_vs_exit_blame. If weak_entry_pct dominates, the next governed cycle should be an **entry** lever (down-weight worst signal or raise threshold), not a second exit lever.

---

## Synthesis — What to adopt / defer / avoid

| Adopt immediately | Defer | Explicitly avoid |
|-------------------|--------|-------------------|
| A: Damage reduction first (after we have blame baseline) | Full multi-window backtest tooling | Treating backtest compare as proof of exit-overlay impact (current pipeline) |
| B: One lever per cycle, small deltas | E: Multiple baselines, sensitivity sweeps | Stacking exit_flow + exit_score in one cycle |
| C: Counterfactuals diagnostic only | | Turning counterfactuals into direct rules |
| D: Paper as validation; for exit levers, paper + effectiveness-from-logs as primary evidence until backtest fixed | | Exploratory paper LOCK without comparison + decision record |
| E as check: Confirm entry vs exit blame before assuming exit is the bottleneck | | Another exit-only cycle without checking blame first |

---

## GO / NO-GO decision

### NO-GO for “execute runbook Steps 2–5 as written on droplet now”

**Reasons:**

1. **Backtest does not apply overlay.** Re-running baseline vs proposed backtest and compare would again show PnL delta 0, win_rate delta 0. Step 5 (LOCK/REVERT) would be based on a comparison that cannot measure the hypothesis. That would repeat the Phase 9 degenerate outcome and add no information.
2. **Missing evidence:** We do not have a single, join-complete effectiveness baseline with **entry_vs_exit_blame** (and ideally signal_effectiveness, exit_effectiveness) to justify “exit only” as the next lever. Recommendation from logs was empty; backtest effectiveness on droplet did not produce blame (no effectiveness/ or join failure).
3. **Paper run is already live.** The score_deterioration 0.28 paper run is exploratory and correctly documented. The right move is to **define the 7–14 day check** for that run as the next decision point, not to start a second runbook cycle that would again use a non-measuring backtest.

**What would make it GO later:**

- **Option 1 (preferred for runbook fidelity):** Implement exit-path simulation in backtest (recompute exit_score with overlay and simulate exit time); then run baseline vs proposed and use comparison + guards for LOCK/REVERT. Then runbook Steps 2–5 are valid.
- **Option 2 (faster):** Treat paper as the experiment. After 7–14 days of the current paper run: run effectiveness from logs for that period; compare to a baseline effectiveness from logs (e.g. pre–paper period); record LOCK or REVERT in a change proposal and in phase8_first_cycle_result (or a dedicated paper-cycle result doc). No re-run of expensive backtests until we have overlay-aware backtest.

---

## Recommended path forward (single highest-EV, lowest-risk step)

**Do not re-run the full runbook on droplet** until either backtest applies overlay (Option 1) or we explicitly adopt paper-first governance for exit levers (Option 2).

**Immediate next steps (in order):**

1. **Unblock evidence (entry vs exit blame)**  
   - On droplet or locally (with synced logs): run effectiveness from **logs** for the last 14–30 days with a date range where join succeeds (attribution + exit_attribution both have entry_timestamp / trade_id).  
   - Ensure output includes `entry_vs_exit_blame.json` (and ideally signal_effectiveness, exit_effectiveness).  
   - If join still fails, fix logging or backtest output so that at least one of (logs, backtest dir) produces join-complete data.  
   - **Decision:** If weak_entry_pct > exit_timing_pct, plan the **next** governed cycle as an **entry** lever (e.g. down-weight worst signal). If exit_timing_pct ≥ weak_entry_pct, exit levers remain justified.

2. **Treat current paper run as the governed experiment for score_deterioration 0.28**  
   - Do not start another runbook cycle (baseline/proposed backtest) for exit weights now.  
   - After 7–14 days: run effectiveness from logs for the paper period; compare to baseline effectiveness (e.g. effectiveness_from_logs_2026-02-18 or pre-paper window); document in reports/PROFITABILITY_PAPER_RUN_2026-02-18.md: comparison summary, guard outcome if run, and LOCK or REVERT with rationale.  
   - If REVERT: restart paper without overlay per the doc. If LOCK: promote overlay to active or document as new baseline and plan post-LOCK validation (e.g. short no-change paper or second window).

3. **Do not introduce new overlays mid-run.**  
   - Let the score_deterioration 0.28 paper run complete its 7–14 day check before adding or stacking any other lever.

4. **Optional but high value:**  
   - Add a small “exit simulation” step to the backtest (or a separate script) that, given a backtest dir and an overlay, recomputes exit decisions and rewrites exit times / PnL so that compare_backtest_runs can measure exit-weight changes. Then the runbook becomes fully valid for exit levers.

---

## Conditional execution (runbook)

**Authorization:** You asked for execution “only if GO” and “following the canonical runbook.”

Because the conclusion is **NO-GO** for executing the runbook’s backtest-compare flow now (Steps 2–5 do not currently measure exit overlay impact), **I am not executing the runbook** on the droplet.

**If you decide to override and run the runbook anyway:**  
- Steps 1 (deploy) and 2 (baseline) can be run to capture proof and baseline path.  
- Steps 3–5 would again produce a degenerate comparison (delta 0) for exit overlays; the only honest decision would be “REVERT due to inconclusive evidence” or “no decision until backtest measures overlay.”  
- I recommend instead using the **exact unblock steps** above: get blame baseline, then use the 7–14 day paper check as the decision gate for the current overlay.

---

## Emotional reality

You are losing money every day; the urge to “do something” is strong. Slowing down here means:

- **Not** pretending the backtest compare is meaningful for exit weights until it actually measures them.  
- **Not** LOCKing more overlays on zero-delta comparisons.  
- **Doing** one thing that moves the needle: **get entry_vs_exit_blame once**, then either (a) fix the backtest so the runbook is valid, or (b) use paper + effectiveness-from-logs as the governed gate and document it.

That is the disciplined path. The runbook remains the canonical process; for exit levers, the pipeline must either measure overlay impact in backtest or we must formally use paper + logs as the evidence source until it does.

---

**Summary**

- **Ideas:** Adopt A (with blame baseline), B, C; adopt D with “paper + effectiveness as primary for exit levers until backtest fixed”; adopt E as a mandatory check before another exit-only cycle.  
- **GO/NO-GO:** **NO-GO** for executing runbook Steps 2–5 now; comparison is degenerate for exit weights.  
- **Unblock:** (1) Produce one authoritative entry_vs_exit_blame; (2) Use 7–14 day paper check for score_deterioration 0.28 as the decision gate; (3) Optionally add exit simulation to backtest so runbook is valid for exit levers.  
- **Execution:** Not running the runbook on droplet; recommended path is unblock steps above.
