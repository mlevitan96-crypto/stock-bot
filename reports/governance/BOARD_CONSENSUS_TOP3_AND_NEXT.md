# Board and personas: agreed top 3 paths forward and what is next

**Date:** 2026-02-27  
**Purpose:** Board and all personas (Adversarial, Quant, Product/Operator, Execution/SRE, Risk) agree on the three best, most productive paths forward and what is next. “None” is acceptable if data does not support a change.

---

## Current state (what data supports)

- **Governance loop:** Live on droplet; 100-trade gate, alternation (entry/exit), no-progress rule, entry strength lever (2.7/2.9), stopping_checks populated, giveback fallback in aggregates, expectancy-gate diagnostic each cycle, replay on stagnation, board/persona review each cycle.
- **Expectancy:** Still negative; LOCK and REVERT both occur. Diagnostic (when populated) shows p50 entry_score ~3.6 and **pct_marginal_2_5_to_2_9 low (~2–3%)** — so we are **not** currently “selecting for bad expectancy by construction” in the last run; the diagnostic is in place to monitor.
- **Blame and one lever at a time:** In place. We have not yet added the **down-weight worst signal** entry lever (Strategic Phase B1 and Quant both call for “down-weight that signal or raise MIN_EXEC_SCORE”; we only do the latter).
- **Giveback:** Fallback exists; giveback can still be null in aggregates when exit_quality_metrics lack profit_giveback. Stopping_checks then show giveback_le_baseline_plus_005: null.

**Conclusion from data:** No need to change loop structure. One high-value addition is supported: add down-weight-worst-signal as an entry lever option. Other two are operational/monitoring and brake.

---

## Agreed top 3 recommended changes (board + personas)

### 1. Add “down-weight worst signal” as an entry-lever option

- **What:** From `signal_effectiveness` (or recommendation’s `top5_harmful`), pick the **single worst** signal (min win_rate, trade_count ≥ 5). When the loop chooses an **entry** lever, allow an overlay that **down-weights that signal** (e.g. −0.05 or half weight) instead of (or in addition to) raising MIN_EXEC_SCORE. One cycle at a time; measure over 100 trades; LOCK or REVERT.
- **Why it helps:** Strategic Phase B1: “Create one tuning overlay: down-weight that signal or slightly raise MIN_EXEC_SCORE.” We only do the second. Quant: “Add down-weight worst signal as an entry-lever option.” Product: same checklist. Adversarial: one lever at a time, no new pipeline. Execution/SRE: no new infra. Risk: fine.
- **Data support:** We have `signal_effectiveness` and `top5_harmful`; we have not tried this lever. Data supports adding it as an option.

### 2. Keep the loop running; monitor with diagnostic and board review (no structural change)

- **What:** Do not add new pipelines or change the governance loop structure. Keep alternation, no-progress, replay-on-stagnation, expectancy-gate diagnostic, and board/persona review. Use `expectancy_gate_diagnostic.json` and `board_review_latest.md` to monitor marginal share and by-score-bucket expectancy. If marginal share rises or low-score buckets worsen, revisit.
- **Why it helps:** Adversarial: “Do not add another discovery run.” Product: one baseline, one lever, repeat. Quant: evidence pipeline in place. Execution/SRE: diagnostic is live. Risk: no new risk from churn.
- **Data support:** Current process is aligned; diagnostic shows we are not selecting for marginal trades in the last run. Data supports “no structural change.”

### 3. Ensure giveback is populated when possible; use optional risk brake when needed

- **What:**  
  - **(a)** Verify that giveback is populated in `effectiveness_aggregates` on the droplet when exit data has `profit_giveback` (fallback exists; if still null, trace and fix so `stopping_checks.giveback_le_baseline_plus_005` is true/false when data exists).  
  - **(b)** When drawdown is **unacceptable**, apply the documented risk brake (e.g. MIN_EXEC_SCORE 3.0 or pause new entries) for a cycle or two and **document** the decision; do not only leave it in the runbook.
- **Why it helps:** Quant: stopping condition should be fully testable. Execution/SRE: honest stopping check. Risk: “Use the brake when it hurts.” Product: optional brake is in the checklist.
- **Data support:** Giveback is sometimes null; fixing that (when source data exists) is supported. Brake is conditional on drawdown, not on a specific metric threshold here.

---

## Best changes to make right now (if data supports)

| Change | Data supports? | Action |
|--------|----------------|--------|
| Add down-weight worst signal as entry lever | **Yes** — we have signal_effectiveness and top5_harmful; this lever type is in the plan but not implemented. | Implement so the loop can choose “entry with down-weight worst signal” when recommendation suggests entry and top5_harmful is non-empty. |
| Change loop structure or add new pipelines | **No** — personas agree: no new pipelines; keep one lever at a time. | None. |
| Run more cycles with current loop | **Yes** — process is aligned; diagnostic and board review are in place. | Keep running; use board review and diagnostic each cycle. |
| Populate giveback when exit data has it | **Yes** — fallback exists; if giveback is still null on droplet, trace and fix. | One-time check on droplet; fix aggregation if needed. |
| Apply risk brake (3.0 or pause) | **Only if** drawdown is unacceptable. | When appropriate, apply and document; otherwise no change. |

So: **one clear change** (add down-weight-worst-signal), **one operational check** (giveback), and **one conditional action** (brake when needed). Everything else: keep the loop and monitor.

---

## What is next

1. **Implement the first agreed change:** Add “down-weight worst signal” as an entry-lever option (recommendation or overlay format specifies which signal and delta; apply_paper_overlay or a small extension supports it; autopilot/loop can choose it when lever=entry and top5_harmful is available).
2. **Continue the governance loop** on the droplet; each cycle produces board review and expectancy-gate diagnostic. No change to loop logic.
3. **Verify giveback on droplet:** Confirm whether `effectiveness_aggregates.avg_profit_giveback` is ever populated; if not, trace from exit_quality_metrics and fix aggregation so stopping_checks can set giveback_le_baseline_plus_005 when data exists.
4. **Use the brake only when needed:** If drawdown becomes unacceptable, raise MIN_EXEC_SCORE (e.g. to 3.0) or pause new entries, document the decision, and resume when appropriate.

**Goal:** Increase chances of profitability by testing the one entry-lever type we have not yet tried (down-weight worst signal), while keeping the loop stable and the stopping condition fully auditable.
